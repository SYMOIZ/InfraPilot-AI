# InfraPilot AI — optimized AWS CLI deploy (serverless, low-cost).
# Requires: AWS CLI v2, Node 20+, Python 3.12+ with pip.
# Usage (from repo root):
#   powershell -ExecutionPolicy Bypass -File scripts\deploy.ps1
# Optional: -EnableBedrock to set DEMO_MODE=false (uses Bedrock; incurs AI cost)

param(
    [switch]$EnableBedrock,
    [string]$Region = "us-east-1",
    [string]$ModelId = "amazon.nova-micro-v1:0"
)

$ErrorActionPreference = "Stop"
# Native tools (pip/aws) often write progress to stderr; do not treat as terminating.
$PSNativeCommandUseErrorActionPreference = $false
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$AccountId = aws sts get-caller-identity --query Account --output text
if (-not $AccountId) { throw "AWS credentials not available" }

$ArtifactsBucket = "infrapilot-artifacts-$AccountId-$Region"
$FrontendBucket  = "infrapilot-frontend-$AccountId-$Region"
$DdbTable        = "infrapilot-projects"
$FuncName        = "infrapilot-api"
$RoleName        = "infrapilot-lambda-role"
$ApiName         = "infrapilot-http-api"
$DemoMode        = if ($EnableBedrock) { "false" } else { "true" }

Write-Host "Account=$AccountId Region=$Region DEMO_MODE=$DemoMode"

function Ensure-Bucket($Name) {
    $exists = $false
    try {
        aws s3api head-bucket --bucket $Name 2>$null
        if ($LASTEXITCODE -eq 0) { $exists = $true }
    } catch { $exists = $false }
    if (-not $exists) {
        Write-Host "Creating bucket $Name"
        if ($Region -eq "us-east-1") {
            aws s3api create-bucket --bucket $Name --region $Region | Out-Null
        } else {
            aws s3api create-bucket --bucket $Name --region $Region `
                --create-bucket-configuration "LocationConstraint=$Region" | Out-Null
        }
    }
    aws s3api put-public-access-block --bucket $Name `
        --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" | Out-Null
}

# --- Data plane ---
Ensure-Bucket $ArtifactsBucket
Ensure-Bucket $FrontendBucket

$tables = aws dynamodb list-tables --region $Region --query "TableNames" --output json | ConvertFrom-Json
if ($tables -notcontains $DdbTable) {
    Write-Host "Creating DynamoDB table $DdbTable"
    aws dynamodb create-table `
        --table-name $DdbTable `
        --attribute-definitions AttributeName=id,AttributeType=S `
        --key-schema AttributeName=id,KeyType=HASH `
        --billing-mode PAY_PER_REQUEST `
        --region $Region | Out-Null
    aws dynamodb wait table-exists --table-name $DdbTable --region $Region
}

# --- IAM role ---
$trust = @'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
'@
$trustPath = Join-Path $env:TEMP "infrapilot-trust.json"
Set-Content -Path $trustPath -Value $trust -Encoding ascii

try {
    aws iam get-role --role-name $RoleName 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "missing" }
} catch {
    Write-Host "Creating IAM role $RoleName"
    aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$trustPath" | Out-Null
    Start-Sleep -Seconds 8
}

aws iam attach-role-policy --role-name $RoleName `
    --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>$null | Out-Null

$policy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Artifacts",
      "Effect": "Allow",
      "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"],
      "Resource": "arn:aws:s3:::${ArtifactsBucket}/*"
    },
    {
      "Sid": "ArtifactsList",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::${ArtifactsBucket}"
    },
    {
      "Sid": "Dynamo",
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem","dynamodb:PutItem","dynamodb:DeleteItem","dynamodb:Scan","dynamodb:Query"],
      "Resource": "arn:aws:dynamodb:${Region}:${AccountId}:table/${DdbTable}"
    },
    {
      "Sid": "Bedrock",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel","bedrock:Converse"],
      "Resource": [
        "arn:aws:bedrock:${Region}::foundation-model/*",
        "arn:aws:bedrock:${Region}:${AccountId}:inference-profile/*"
      ]
    }
  ]
}
"@
$policyPath = Join-Path $env:TEMP "infrapilot-lambda-policy.json"
Set-Content -Path $policyPath -Value $policy -Encoding ascii
aws iam put-role-policy --role-name $RoleName --policy-name infrapilot-access --policy-document "file://$policyPath" | Out-Null

$RoleArn = aws iam get-role --role-name $RoleName --query Role.Arn --output text

# --- Package Lambda (Linux wheels) ---
$BuildDir = Join-Path $env:TEMP "infrapilot-lambda-build"
$ZipPath  = Join-Path $env:TEMP "infrapilot-api.zip"
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
New-Item -ItemType Directory -Path $BuildDir | Out-Null
if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }

Write-Host "Installing Linux Lambda dependencies..."
& python -m pip install -r "$Root\backend\requirements-lambda.txt" -t $BuildDir `
    --platform manylinux2014_x86_64 `
    --python-version 3.12 `
    --implementation cp `
    --only-binary=:all: `
    --upgrade --disable-pip-version-check
if (-not (Test-Path (Join-Path $BuildDir "mangum"))) {
    throw "Lambda dependency install failed (mangum missing in $BuildDir)"
}

Copy-Item -Recurse "$Root\backend\app" "$BuildDir\app"
Copy-Item -Recurse "$Root\agent" "$BuildDir\agent"
Copy-Item -Recurse "$Root\rules" "$BuildDir\rules"
Copy-Item -Recurse "$Root\catalog" "$BuildDir\catalog"

# Strip caches / tests noise
Get-ChildItem -Recurse $BuildDir -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse $BuildDir -Directory -Filter "*.dist-info" | Where-Object { $_.Name -match "pip|setuptools|wheel" } | ForEach-Object { } # keep dist-info for imports

Write-Host "Zipping Lambda package..."
Push-Location $BuildDir
Compress-Archive -Path * -DestinationPath $ZipPath -Force
Pop-Location

$zipSizeMb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 2)
Write-Host "Package size: ${zipSizeMb} MB"
if ((Get-Item $ZipPath).Length -gt 50MB) {
    Write-Warning "Zip exceeds 50MB direct-upload limit; consider S3 upload for code."
}

# --- Lambda function ---
$envJson = @{
    Variables = @{
        DEMO_MODE        = $DemoMode
        AWS_REGION       = $Region
        BEDROCK_REGION   = $Region
        BEDROCK_MODEL_ID = $ModelId
        S3_BUCKET        = $ArtifactsBucket
        DYNAMODB_TABLE   = $DdbTable
        CORS_ORIGINS     = "*"
    }
} | ConvertTo-Json -Compress
# AWS CLI expects nested JSON string for --environment; write file
$envPath = Join-Path $env:TEMP "infrapilot-lambda-env.json"
# Format: {"Variables":{...}}
$envObj = @{
    Variables = [ordered]@{
        DEMO_MODE        = $DemoMode
        BEDROCK_REGION   = $Region
        BEDROCK_MODEL_ID = $ModelId
        S3_BUCKET        = $ArtifactsBucket
        DYNAMODB_TABLE   = $DdbTable
        CORS_ORIGINS     = "*"
    }
}
($envObj | ConvertTo-Json -Compress -Depth 5) | Set-Content -Path $envPath -Encoding ascii

$fnExists = $false
try {
    aws lambda get-function --function-name $FuncName --region $Region 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $fnExists = $true }
} catch { $fnExists = $false }

if (-not $fnExists) {
    Write-Host "Creating Lambda $FuncName"
    # Role may need a moment to propagate
    $created = $false
    for ($i = 0; $i -lt 6; $i++) {
        aws lambda create-function `
            --function-name $FuncName `
            --runtime python3.12 `
            --role $RoleArn `
            --handler app.lambda_handler.handler `
            --timeout 60 `
            --memory-size 512 `
            --architectures x86_64 `
            --zip-file "fileb://$ZipPath" `
            --environment "file://$envPath" `
            --region $Region 2>&1
        if ($LASTEXITCODE -eq 0) { $created = $true; break }
        Write-Host "Waiting for IAM role propagation..."
        Start-Sleep -Seconds 10
    }
    if (-not $created) { throw "Failed to create Lambda function" }
} else {
    Write-Host "Updating Lambda code $FuncName"
    aws lambda update-function-code `
        --function-name $FuncName `
        --zip-file "fileb://$ZipPath" `
        --region $Region | Out-Null
    aws lambda wait function-updated --function-name $FuncName --region $Region
    aws lambda update-function-configuration `
        --function-name $FuncName `
        --timeout 60 `
        --memory-size 512 `
        --environment "file://$envPath" `
        --region $Region | Out-Null
    aws lambda wait function-updated --function-name $FuncName --region $Region
}

try {
    aws logs put-retention-policy --log-group-name "/aws/lambda/$FuncName" --retention-in-days 14 --region $Region 2>$null | Out-Null
} catch {}

# --- HTTP API ---
$apis = aws apigatewayv2 get-apis --region $Region --query "Items[?Name=='$ApiName']" --output json | ConvertFrom-Json
if (-not $apis -or $apis.Count -eq 0) {
    Write-Host "Creating HTTP API $ApiName"
    $ApiId = aws apigatewayv2 create-api `
        --name $ApiName `
        --protocol-type HTTP `
        --cors-configuration "AllowOrigins=*,AllowMethods=GET,POST,PUT,PATCH,DELETE,OPTIONS,AllowHeaders=*,MaxAge=300" `
        --region $Region `
        --query ApiId --output text
} else {
    $ApiId = $apis[0].ApiId
    Write-Host "Reusing HTTP API $ApiId"
}

$LambdaArn = "arn:aws:lambda:${Region}:${AccountId}:function:${FuncName}"
$integrations = aws apigatewayv2 get-integrations --api-id $ApiId --region $Region --output json | ConvertFrom-Json
$IntegrationId = $null
if ($integrations.Items) {
    $existing = $integrations.Items | Where-Object { $_.IntegrationUri -like "*${FuncName}*" } | Select-Object -First 1
    if ($existing) { $IntegrationId = $existing.IntegrationId }
}
if (-not $IntegrationId) {
    $IntegrationId = aws apigatewayv2 create-integration `
        --api-id $ApiId `
        --integration-type AWS_PROXY `
        --integration-uri $LambdaArn `
        --payload-format-version 2.0 `
        --region $Region `
        --query IntegrationId --output text
}

$routes = aws apigatewayv2 get-routes --api-id $ApiId --region $Region --output json | ConvertFrom-Json
$routeKeys = @()
if ($routes.Items) { $routeKeys = $routes.Items | ForEach-Object { $_.RouteKey } }
if ($routeKeys -notcontains "ANY /{proxy+}") {
    aws apigatewayv2 create-route --api-id $ApiId --route-key "ANY /{proxy+}" --target "integrations/$IntegrationId" --region $Region | Out-Null
}
if ($routeKeys -notcontains "ANY /") {
    aws apigatewayv2 create-route --api-id $ApiId --route-key "ANY /" --target "integrations/$IntegrationId" --region $Region | Out-Null
}

$stages = aws apigatewayv2 get-stages --api-id $ApiId --region $Region --output json | ConvertFrom-Json
$hasDefault = $false
if ($stages.Items) { $hasDefault = ($stages.Items | Where-Object { $_.StageName -eq '$default' }) -ne $null }
if (-not $hasDefault) {
    aws apigatewayv2 create-stage --api-id $ApiId --stage-name '$default' --auto-deploy --region $Region | Out-Null
}

aws lambda add-permission `
    --function-name $FuncName `
    --statement-id "apigw-invoke-$ApiId" `
    --action lambda:InvokeFunction `
    --principal apigateway.amazonaws.com `
    --source-arn "arn:aws:execute-api:${Region}:${AccountId}:${ApiId}/*/*" `
    --region $Region 2>$null | Out-Null

$ApiEndpoint = aws apigatewayv2 get-api --api-id $ApiId --region $Region --query ApiEndpoint --output text
Write-Host "API endpoint: $ApiEndpoint"

# --- Frontend build + S3 website via CloudFront OAC ---
Write-Host "Building frontend..."
Push-Location "$Root\frontend"
if (-not (Test-Path "node_modules")) { npm ci --no-fund --no-audit 2>&1 | Out-Host }
# Bake API URL into build
$env:VITE_API_BASE_URL = $ApiEndpoint
npm run build 2>&1 | Out-Host
if (-not (Test-Path "dist\index.html")) { Pop-Location; throw "Frontend build failed (dist/index.html missing)" }
Pop-Location

aws s3 sync "$Root\frontend\dist" "s3://$FrontendBucket/" --delete --region $Region | Out-Null

# Origin Access Control + CloudFront
$oacList = aws cloudfront list-origin-access-controls --output json | ConvertFrom-Json
$OacId = $null
if ($oacList.OriginAccessControlList.Items) {
    $match = $oacList.OriginAccessControlList.Items | Where-Object { $_.Name -eq "infrapilot-frontend-oac" } | Select-Object -First 1
    if ($match) { $OacId = $match.Id }
}
if (-not $OacId) {
    $oacConfig = @"
{
  "Name": "infrapilot-frontend-oac",
  "Description": "InfraPilot frontend OAC",
  "SigningProtocol": "sigv4",
  "SigningBehavior": "always",
  "OriginAccessControlOriginType": "s3"
}
"@
    $oacPath = Join-Path $env:TEMP "infrapilot-oac.json"
    Set-Content -Path $oacPath -Value $oacConfig -Encoding ascii
    $OacId = aws cloudfront create-origin-access-control --origin-access-control-config "file://$oacPath" --query 'OriginAccessControl.Id' --output text
}

$dists = aws cloudfront list-distributions --query "DistributionList.Items[?Comment=='InfraPilot AI frontend']" --output json | ConvertFrom-Json
$DistId = $null
$DistDomain = $null
if ($dists -and $dists.Count -gt 0) {
    $DistId = $dists[0].Id
    $DistDomain = $dists[0].DomainName
    Write-Host "Reusing CloudFront $DistId"
} else {
    $callerRef = "infrapilot-$(Get-Date -Format 'yyyyMMddHHmmss')"
    $originDomain = "$FrontendBucket.s3.$Region.amazonaws.com"
    $distConfig = @"
{
  "CallerReference": "$callerRef",
  "Comment": "InfraPilot AI frontend",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [{
      "Id": "s3-frontend",
      "DomainName": "$originDomain",
      "S3OriginConfig": { "OriginAccessIdentity": "" },
      "OriginAccessControlId": "$OacId"
    }]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": { "Quantity": 2, "Items": ["GET","HEAD"], "CachedMethods": { "Quantity": 2, "Items": ["GET","HEAD"] } },
    "Compress": true,
    "ForwardedValues": { "QueryString": false, "Cookies": { "Forward": "none" } },
    "MinTTL": 0,
    "DefaultTTL": 3600,
    "MaxTTL": 86400
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      { "ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 0 },
      { "ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "200", "ErrorCachingMinTTL": 0 }
    ]
  },
  "PriceClass": "PriceClass_100"
}
"@
    $distPath = Join-Path $env:TEMP "infrapilot-cf-dist.json"
    Set-Content -Path $distPath -Value $distConfig -Encoding ascii
    $createdDist = aws cloudfront create-distribution --distribution-config "file://$distPath" | ConvertFrom-Json
    $DistId = $createdDist.Distribution.Id
    $DistDomain = $createdDist.Distribution.DomainName
    Write-Host "Created CloudFront $DistId (deploying...)"
}

# Bucket policy for OAC
$bucketPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontServicePrincipal",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::${FrontendBucket}/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::${AccountId}:distribution/${DistId}"
      }
    }
  }]
}
"@
$bpPath = Join-Path $env:TEMP "infrapilot-frontend-bucket-policy.json"
Set-Content -Path $bpPath -Value $bucketPolicy -Encoding ascii
aws s3api put-bucket-policy --bucket $FrontendBucket --policy "file://$bpPath" | Out-Null

# Update Lambda CORS to CloudFront origin
$CorsOrigin = "https://$DistDomain"
$envObj.Variables.CORS_ORIGINS = "$CorsOrigin,http://localhost:5173"
($envObj | ConvertTo-Json -Compress -Depth 5) | Set-Content -Path $envPath -Encoding ascii
aws lambda update-function-configuration `
    --function-name $FuncName `
    --environment "file://$envPath" `
    --region $Region | Out-Null

aws cloudfront create-invalidation --distribution-id $DistId --paths "/*" | Out-Null

# --- Smoke test ---
Write-Host "Smoke testing API health..."
Start-Sleep -Seconds 3
try {
    $health = Invoke-RestMethod -Uri "$ApiEndpoint/health" -Method GET -TimeoutSec 30
    Write-Host ("Health: " + ($health | ConvertTo-Json -Compress))
} catch {
    Write-Warning "Health check failed (Cold start may need retry): $_"
}

$out = @"
=== InfraPilot AI deploy complete ===
API:        $ApiEndpoint
Frontend:   https://$DistDomain
CloudFront: $DistId
DEMO_MODE:  $DemoMode
Model:      $ModelId
Artifacts:  s3://$ArtifactsBucket
Table:      $DdbTable
Region:     $Region

Teardown hint:
  aws cloudfront get-distribution --id $DistId
  # disable then delete distribution, then:
  aws s3 rb s3://$FrontendBucket --force
  aws s3 rb s3://$ArtifactsBucket --force
  aws lambda delete-function --function-name $FuncName --region $Region
  aws apigatewayv2 delete-api --api-id $ApiId --region $Region
  aws dynamodb delete-table --table-name $DdbTable --region $Region
"@
$outPath = Join-Path $Root "deploy-outputs.txt"
Set-Content -Path $outPath -Value $out -Encoding utf8
Write-Host $out
Write-Host "Wrote $outPath"

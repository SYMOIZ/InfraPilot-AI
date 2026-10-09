# Tear down InfraPilot AI prototype resources created by deploy.ps1
param([string]$Region = "us-east-1")
$ErrorActionPreference = "Continue"
$AccountId = aws sts get-caller-identity --query Account --output text
$ArtifactsBucket = "infrapilot-artifacts-$AccountId-$Region"
$FrontendBucket  = "infrapilot-frontend-$AccountId-$Region"
$DdbTable        = "infrapilot-projects"
$FuncName        = "infrapilot-api"
$RoleName        = "infrapilot-lambda-role"
$ApiName         = "infrapilot-http-api"

Write-Host "This will delete InfraPilot prototype resources in $Region / $AccountId"
$confirm = Read-Host "Type DELETE to confirm"
if ($confirm -ne "DELETE") { Write-Host "Aborted"; exit 1 }

$apis = aws apigatewayv2 get-apis --region $Region --query "Items[?Name=='$ApiName'].ApiId" --output text
if ($apis) {
  foreach ($id in ($apis -split "`t")) {
    if ($id) { aws apigatewayv2 delete-api --api-id $id --region $Region }
  }
}

aws lambda delete-function --function-name $FuncName --region $Region 2>$null
aws dynamodb delete-table --table-name $DdbTable --region $Region 2>$null
aws s3 rb "s3://$FrontendBucket" --force 2>$null
aws s3 rb "s3://$ArtifactsBucket" --force 2>$null

aws iam delete-role-policy --role-name $RoleName --policy-name infrapilot-access 2>$null
aws iam detach-role-policy --role-name $RoleName --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" 2>$null
aws iam delete-role --role-name $RoleName 2>$null

Write-Host "Note: Disable and delete the CloudFront distribution named 'InfraPilot AI frontend' in the console (eventual consistency)."
Write-Host "Teardown of API/Lambda/DynamoDB/S3 attempted."

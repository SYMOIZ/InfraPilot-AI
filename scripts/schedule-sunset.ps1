# Schedule one-shot AWS EventBridge Scheduler reminder for 8 Nov 2026.
param(
    [string]$Region = "us-east-1",
    [string]$AtUtc = "2026-11-08T12:00:00"
)

$ErrorActionPreference = "Continue"
$PSNativeCommandUseErrorActionPreference = $false

$AccountId = aws sts get-caller-identity --query Account --output text
$ScheduleName = "infrapilot-sunset-2026-11-08"
$RoleName = "infrapilot-scheduler-role"
$TopicName = "infrapilot-sunset-reminder"

Write-Host "Scheduling sunset reminder at $AtUtc UTC for account $AccountId"

$TopicArn = aws sns create-topic --name $TopicName --region $Region --query TopicArn --output text
Write-Host "SNS topic: $TopicArn"

$trust = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"scheduler.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
$trustPath = Join-Path $env:TEMP "infrapilot-scheduler-trust.json"
Set-Content -Path $trustPath -Value $trust -Encoding ascii

aws iam get-role --role-name $RoleName 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    aws iam create-role --role-name $RoleName --assume-role-policy-document "file://$trustPath" | Out-Null
    Start-Sleep -Seconds 10
}

$policy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["sns:Publish"],
    "Resource": "$TopicArn"
  }]
}
"@
$polPath = Join-Path $env:TEMP "infrapilot-scheduler-policy.json"
Set-Content -Path $polPath -Value $policy -Encoding ascii
aws iam put-role-policy --role-name $RoleName --policy-name sns-publish --policy-document "file://$polPath" | Out-Null
$RoleArn = aws iam get-role --role-name $RoleName --query Role.Arn --output text

aws scheduler delete-schedule --name $ScheduleName --region $Region 2>$null | Out-Null

$payload = '{"project":"InfraPilot AI","action":"SUNSET_DUE","date":"2026-11-08","teardown":"Run GitHub Actions sunset.yml or scripts/teardown-auto.sh"}'
$targetPath = Join-Path $env:TEMP "infrapilot-scheduler-target.json"
@"
{
  "Arn": "$TopicArn",
  "RoleArn": "$RoleArn",
  "Input": $($payload | ConvertTo-Json)
}
"@ | Set-Content -Path $targetPath -Encoding ascii

aws scheduler create-schedule `
  --name $ScheduleName `
  --region $Region `
  --schedule-expression "at($AtUtc)" `
  --flexible-time-window Mode=OFF `
  --target "file://$targetPath" `
  --action-after-completion DELETE

if ($LASTEXITCODE -eq 0) {
  Write-Host "Created schedule $ScheduleName"
  Write-Host "SNS: $TopicArn"
  Write-Host "Subscribe email with: aws sns subscribe --topic-arn $TopicArn --protocol email --notification-endpoint YOU@example.com --region $Region"
} else {
  Write-Host "Schedule create failed - sunset still covered by GitHub Actions sunset.yml"
}

Write-Host "Destructive delete via GitHub Actions sunset.yml or scripts/teardown-auto.sh"

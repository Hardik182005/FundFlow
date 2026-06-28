# FundFlow — AWS deploy helper (run after `aws configure` / `aws sso login`).
# Backend  -> ECR image (consumed by App Runner)
# Frontend -> static export synced to S3 (+ optional CloudFront invalidation)
#
# Usage:
#   ./deploy-aws.ps1 -Region ap-south-1 -AccountId 123456789012 `
#       -Bucket fundflow-web -ApiUrl https://xxxx.ap-south-1.awsapprunner.com `
#       -ElevenLabsAgentId agent_xxx -CloudFrontId E123ABC   (CloudFrontId optional)

param(
  [Parameter(Mandatory=$true)][string]$Region,
  [Parameter(Mandatory=$true)][string]$AccountId,
  [Parameter(Mandatory=$true)][string]$Bucket,
  [string]$ApiUrl = "",
  [string]$ElevenLabsAgentId = "",
  [string]$CloudFrontId = "",
  [string]$Repo = "fundflow-api",
  [switch]$BackendOnly,
  [switch]$FrontendOnly
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Deploy-Backend {
  Write-Host "==> Building & pushing backend image to ECR" -ForegroundColor Cyan
  aws ecr describe-repositories --repository-names $Repo --region $Region 2>$null
  if ($LASTEXITCODE -ne 0) { aws ecr create-repository --repository-name $Repo --region $Region | Out-Null }
  $registry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
  aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $registry
  docker build -t "${Repo}:latest" "$root/fundflow-backend"
  docker tag "${Repo}:latest" "$registry/${Repo}:latest"
  docker push "$registry/${Repo}:latest"
  Write-Host "Image pushed: $registry/${Repo}:latest" -ForegroundColor Green
  Write-Host "First time: create an App Runner service from this image (port 8080, health '/health', timeout 120s) and set env vars from fundflow-backend/.env (DEMO_MODE=false, ALLOWED_ORIGINS=<frontend URL>)." -ForegroundColor Yellow
  Write-Host "After that, re-running this script + App Runner auto-deploy ships new versions." -ForegroundColor Yellow
}

function Deploy-Frontend {
  Write-Host "==> Building & syncing frontend to s3://$Bucket" -ForegroundColor Cyan
  Push-Location "$root/fundflow-frontend"
  if (Test-Path .next) { Remove-Item -Recurse -Force .next }
  if (Test-Path out)   { Remove-Item -Recurse -Force out }
  $env:NEXT_PUBLIC_API_URL = $ApiUrl
  $env:NEXT_PUBLIC_ELEVENLABS_AGENT_ID = $ElevenLabsAgentId
  npm run build
  aws s3 sync out/ "s3://$Bucket" --delete --region $Region
  if ($CloudFrontId) {
    aws cloudfront create-invalidation --distribution-id $CloudFrontId --paths "/*" | Out-Null
    Write-Host "CloudFront invalidation requested." -ForegroundColor Green
  }
  Pop-Location
  Write-Host "Frontend deployed to s3://$Bucket" -ForegroundColor Green
}

if (-not $FrontendOnly) { Deploy-Backend }
if (-not $BackendOnly)  { Deploy-Frontend }
Write-Host "Done." -ForegroundColor Green

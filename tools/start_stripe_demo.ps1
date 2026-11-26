[CmdletBinding()]
param(
    [switch]$OwnerApproved,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$project = "nexusai-phase3-stripe"

function Get-EnvironmentValue {
    param([string]$Name)

    $value = [Environment]::GetEnvironmentVariable($Name)
    if ($null -eq $value) {
        return ""
    }
    return $value
}

if (-not $OwnerApproved) {
    throw "Refusing to start Stripe demonstration without -OwnerApproved."
}

if ($FrontendPort -lt 1024 -or $FrontendPort -gt 65535) {
    throw "FrontendPort must be between 1024 and 65535."
}

$environment = (Get-EnvironmentValue "NEXUSAI_ENVIRONMENT").Trim().ToLowerInvariant()
if (-not $environment) {
    $environment = "development"
}
if ($environment -in @("production", "prod")) {
    throw "Stripe Sandbox demonstration cannot run in production environment."
}

$secretKey = (Get-EnvironmentValue "NEXUSAI_STRIPE_SECRET_KEY").Trim()
if (-not $secretKey) {
    throw "A private Stripe Sandbox API key must be injected before starting the demo."
}
if ($secretKey -match "(^|_)live_") {
    throw "Live Stripe credentials are rejected."
}
if ($secretKey -notmatch "^(sk_test_|rk_test_|rkcs_test_|csk_rk_test_)") {
    throw "The Stripe key format is not an accepted Sandbox format."
}

$webhookSecret = (Get-EnvironmentValue "NEXUSAI_STRIPE_WEBHOOK_SECRET").Trim()
if (-not $webhookSecret -or $webhookSecret -notmatch "^whsec_") {
    throw "A private Stripe Sandbox webhook secret must be injected before starting the demo."
}

$env:NEXUSAI_STRIPE_DEMO_ENABLED = "true"
$env:NEXUSAI_STRIPE_DEMO_SECRET_KEY = $secretKey
$env:NEXUSAI_STRIPE_DEMO_WEBHOOK_SECRET = $webhookSecret

Write-Output "Starting the owner-approved local Stripe Sandbox demonstration."
docker compose --project-name $project up -d postgres backend
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose could not start the isolated local backend services."
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8100/health/ready"
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) {
    throw "The local backend readiness check failed."
}

$settingsCheck = docker compose --project-name $project exec -T backend python -c "from app.core.config import get_settings; assert get_settings().stripe_enabled is True; print('demo_backend_configured=true')"
if ($LASTEXITCODE -ne 0 -or $settingsCheck -notcontains "demo_backend_configured=true") {
    throw "The backend did not confirm the approved Sandbox configuration."
}

# Do not pass backend Stripe credentials to the frontend development process.
$env:NEXUSAI_STRIPE_ENABLED = "false"
$env:NEXUSAI_STRIPE_SECRET_KEY = $null
$env:NEXUSAI_STRIPE_WEBHOOK_SECRET = $null
$env:NEXUSAI_STRIPE_DEMO_ENABLED = $null
$env:NEXUSAI_STRIPE_DEMO_SECRET_KEY = $null
$env:NEXUSAI_STRIPE_DEMO_WEBHOOK_SECRET = $null
$env:VITE_DATA_MODE = "api"
$env:VITE_API_BASE_URL = "/api/v1"
$env:API_PROXY_TARGET = "http://127.0.0.1:8100"

$frontendPath = (Resolve-Path (Join-Path $PSScriptRoot "..\frontend")).Path
$bunWrapper = (Get-Command bun.ps1 -ErrorAction Stop).Source
$bun = Join-Path (Split-Path $bunWrapper -Parent) "node_modules\bun\bin\bun.exe"
if (-not (Test-Path -LiteralPath $bun)) {
    $bun = (Get-Command bun.cmd -ErrorAction Stop).Source
}
$frontend = Start-Process -FilePath $bun -ArgumentList @(
    "run", "dev", "--", "--host", "127.0.0.1", "--port", $FrontendPort
) -WorkingDirectory $frontendPath -PassThru -WindowStyle Hidden

Write-Output "Stripe demo frontend: http://127.0.0.1:$FrontendPort"
Write-Output "Backend health: http://127.0.0.1:8100/health/ready"
Write-Output "Frontend process id: $($frontend.Id)"
Write-Output "No Checkout Session or payment is created automatically."

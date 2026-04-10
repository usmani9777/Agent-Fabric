param(
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if ($SkipBuild) {
    docker compose up -d
} else {
    docker compose up -d --build
}

curl.exe --silent --show-error --fail --retry 30 --retry-delay 1 --retry-connrefused "http://localhost:8081/api/health" | Out-Null
curl.exe --silent --show-error --fail --retry 30 --retry-delay 1 --retry-connrefused "http://localhost:8080/api/health" | Out-Null

Push-Location "backend_mcp"
uv run backend-mcp-bootstrap-db
Pop-Location

Push-Location "backend_langgraph"
uv run backend-langgraph-bootstrap-db
Pop-Location

$timestamp = [DateTime]::UtcNow.ToString("yyyyMMddHHmmss")
$email = "smoke-$timestamp@example.com"
$password = "super-secret-123"

$register = Invoke-RestMethod -Method Post -Uri "http://localhost:8080/api/v1/auth/register" -ContentType "application/json" -Body (@{
    email = $email
    password = $password
} | ConvertTo-Json)

$token = $register.session_token
if (-not $token) {
    throw "Failed to acquire session token during smoke test"
}

$invoke = Invoke-RestMethod -Method Post -Uri "http://localhost:8080/api/v1/agent/invoke" -Headers @{"X-Session-Token"=$token} -ContentType "application/json" -Body (@{
    input = "Give me an onboarding strategy"
    refine_prompt = $true
} | ConvertTo-Json)

$summary = [PSCustomObject]@{
    backend_mcp_health = "ok"
    backend_langgraph_health = "ok"
    session_token_issued = [bool]$token
    invoke_selected_intent = $invoke.selected_intent
    invoke_memory_written = $invoke.memory_written
}

$summary | Format-List | Out-String | Write-Host
Write-Host "Deploy-check completed successfully."

$ErrorActionPreference = "Stop"

Write-Host "Testing Smart Elderly Nutritionist API..." -ForegroundColor Cyan

# 1. Check Root Endpoint
try {
    $response = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/"
    Write-Host "[OK] API is running: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "[Error] Cannot connect to API. Please make sure 'run_app.bat' is running!" -ForegroundColor Red
    exit
}

# 2. Trigger Sync
Write-Host "`nTriggering Knowledge Base Sync..." -ForegroundColor Yellow
try {
    $syncResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/knowledge/trigger_sync"
    
    if ($syncResponse.status -eq "success") {
        Write-Host "[Success] Sync triggered successfully!" -ForegroundColor Green
        $syncResponse.details | Format-Table
    } else {
        Write-Host "[Failed] Sync returned error: $($syncResponse.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "[Error] Failed to trigger sync: $_" -ForegroundColor Red
}

Pause

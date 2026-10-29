@echo off
echo Sending batch trigger request to http://localhost:8080/batch/trigger
echo.

:: Try using curl (available on modern Windows)
curl -s -X POST http://localhost:8080/batch/trigger
if errorlevel 1 (
    echo.
    echo curl failed, trying PowerShell fallback...
    powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8080/batch/trigger' -Method Post -ContentType 'application/json' | ConvertTo-Json -Depth 3"
)

echo.
echo Done.

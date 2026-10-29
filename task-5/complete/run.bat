@echo off
echo Building application...
call build.bat
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)
echo Starting docker-compose stack...
docker compose up -d --build
echo.
echo Stack started. Endpoints:
echo   App health:    http://localhost:8080/batch/health
echo   Batch trigger: http://localhost:8080/batch/trigger (POST)
echo   Prometheus:    http://localhost:8080/actuator/prometheus
echo   Jaeger UI:     http://localhost:16686
echo   Kibana:        http://localhost:5601
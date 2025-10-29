@echo off
set PORT=8083
set URL=http://localhost:%PORT%/logs_page

REM 启动Web服务器
cd /d "%~dp0"
start "LogsServer" python -c "import sys; sys.path.insert(0, '.'); from src.web_server import run_web_server; run_web_server()"

REM 等待服务器启动
timeout /t 5 /nobreak >nul

REM 打开日志页面
start "" %URL%

@echo off
set PORT=8082    REM 修改端口为8082
set URL=http://localhost:%PORT%/db_management

start "" "%URL%"

setlocal

REM 检查是否已经安装依赖
python -c "import flask, fastapi, uvicorn, openai, mysql.connector, PIL, colorama, requests" 2>nul
if errorlevel 1 (
    echo 缺少依赖，正在安装...
    pip install -r requirements.txt
)

REM 启动Web服务器
start "WebServer" /D "%CD%" python web_server.py

REM 等待服务器启动
ping 127.0.0.1 -n 5 > nul

REM 打开数据库管理页面
start "" %URL%

endlocal
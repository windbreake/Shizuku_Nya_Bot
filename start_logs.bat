@echo off
set PORT=8083    REM 修改端口为8083
set URL=http://localhost:%PORT%/logs_page

start "" "%URL%"

setlocal

REM 检查是否已经安装依赖
python -c "import flask, fastapi, uvicorn, openai, mysql.connector, PIL, colorama, requests" 2>nul
if errorlevel 1 (
    echo 缺少依赖，正在安装...
    pip install -r requirements.txt
)

REM 启动日志服务
start "LogsServer" /D "%CD%" python -c "import logging; logging.basicConfig(filename='app.log', level=logging.INFO); input('日志服务已启动，按Enter键退出')"

REM 等待日志服务启动
ping 127.0.0.1 -n 5 > nul

REM 打开日志页面
start "" %URL%

endlocal
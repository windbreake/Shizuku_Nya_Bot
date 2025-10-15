@echo off
REM 设置控制台为UTF-8编码
chcp 65001 > nul

title 傲娇猫娘小雫 - 启动器
color 0B
cls

REM 确保使用正确的Python解释器路径
set PYTHON_EXE=python

REM 检查依赖是否安装 - 使用英文提示避免编码问题
echo Checking dependencies...
%PYTHON_EXE% -c "import flask, fastapi, uvicorn, openai, mysql.connector, PIL, colorama, requests" 2>nul
if errorlevel 1 (
    echo Missing dependencies, installing...
    %PYTHON_EXE% -m pip install flask fastapi uvicorn openai mysql-connector-python pillow colorama requests
)

:main_menu
cls                                  :: 在每次显示主菜单前清屏
echo.
echo ==============================================
echo   🐱 傲娇猫娘小雫 - 运行模式选择
echo ==============================================
echo.
echo   0: 映射至Koishi (OpenAI API兼容)
echo   1: 终端聊天模式
echo   2: 沙箱聊天模式 (Web界面)
echo   3: 运行服务诊断
echo   4: 数据库维护工具
echo   5: Start Web Controler
echo   6: 映射至Koishi (统一API服务)
echo.
echo ==============================================
echo.
goto get_choice

:get_choice
set /p choice="请选择模式 (0/1/2/3/4/5/6): "

if "%choice%"=="0" goto run_koishi
if "%choice%"=="1" goto run_terminal
if "%choice%"=="2" goto run_sandbox
if "%choice%"=="3" goto run_diagnosis
if "%choice%"=="4" goto run_cleanup
if "%choice%"=="5" goto open_panel
if "%choice%"=="6" goto run_unified_api

echo.
echo 无效选择，请重新输入!
echo.
goto get_choice

:run_koishi
REM 同时启动 Koishi 映射和统一API服务
(
    echo.
    echo 🚀 启动Koishi映射模式...
    start "Koishi Server" cmd /k "%PYTHON_EXE% main.py 0"
    if errorlevel 1 (
        echo 启动失败! 请检查错误信息
    ) else (
        echo 启动成功! 日志已在新窗口中显示
    )

    echo.
    echo 🚀 启动统一API服务...
    start "Unified API Server" cmd /k "%PYTHON_EXE% src/unified_api.py"
    if errorlevel 1 (
        echo 启动失败! 请检查错误信息
    ) else (
        echo 启动成功! 日志已在新窗口中显示
    )
)
REM 自动继续，无需按键
goto main_menu


:run_terminal
echo.
echo 🐱 启动终端聊天模式...
start "Terminal Chat" cmd /k "%PYTHON_EXE% main.py 1"
if errorlevel 1 (
    echo 启动失败! 请检查错误信息
) else (
    echo 启动成功! 日志已在新窗口中显示
)
REM 自动继续，无需按键
goto main_menu

:run_sandbox
echo.
echo 🌐 启动沙箱聊天模式...
start "Sandbox Server" cmd /k "%PYTHON_EXE% main.py 2"
REM 去掉以下自动打开浏览器，避免重复弹窗
REM start "" http://localhost:2555/sandbox
if errorlevel 1 (
    echo 启动失败! 请检查错误信息
) else (
    echo 启动成功! 日志已在新窗口中显示
)
goto main_menu

:run_diagnosis
echo.
echo 🩺 运行服务诊断...
start "Diagnosis" cmd /k "%PYTHON_EXE% main.py 3"
if errorlevel 1 (
    echo 诊断启动失败! 请检查错误信息
) else (
    echo 诊断已启动! 日志已在新窗口中显示
)
REM 自动继续，无需按键
goto main_menu

:run_cleanup
echo.
echo 🛠 启动数据库维护工具...
start "数据库维护工具" cmd /k "start_cleanup.bat"
if errorlevel 1 (
    echo 启动失败! 请检查错误信息
) else (
    echo 启动成功! 维护工具已在新窗口中打开
)
REM 自动继续，无需按键
goto main_menu

:run_unified_api
echo.
echo 🚀 启动统一API服务...
start "Unified API Server" cmd /k "%PYTHON_EXE% src/unified_api.py"
if errorlevel 1 (
    echo 启动失败! 请检查错误信息
) else (
    echo 启动成功! 日志已在新窗口中显示
)
REM 自动继续，无需按键
goto main_menu

:open_panel
echo.
echo 🌐 启动 Web 控制面板服务...
start "Web Control Panel" cmd /k "set WERKZEUG_RUN_MAIN=true&&%PYTHON_EXE% main.py 2"
timeout /t 1 /nobreak >nul
start "" http://localhost:8888/control_panel   REM 修改端口为Web服务器匹配
goto main_menu

:end
echo.
echo 程序已退出...
pause
@echo off
:: 设置编码为 UTF-8
chcp 65001 >nul

title 数据库维护工具

:start
cls
echo.
echo =============================
echo   数据库维护工具
echo =============================
echo.
echo 请选择操作：
echo.
echo 1. 启动自动清理守护进程
echo 2. 手动重置数据库（清空 chat_history）
echo 3. 退出
echo.

set /p "choice=请输入选项 (1/2/3): "

if /i "%choice%"=="1" goto start_cleanup
if /i "%choice%"=="2" goto reset_db
if /i "%choice%"=="3" goto exit

echo 无效输入，请按任意键重试...
pause >nul
goto start

:start_cleanup
cls
echo.
echo 正在启动自动清理守护进程...
echo 按 Ctrl+C 可随时退出
echo.
python src/cleanup_chat_history.py
echo.
timeout /t 1 /nobreak >nul
goto start

:reset_db
cls
echo.
echo 正在手动重置数据库（交互式删除 chat_history）...
echo.
python src/reset_database.py

echo.
timeout /t 1 /nobreak >nul
goto start

:exit
cls
echo.
echo 正在退出...
echo.
exit

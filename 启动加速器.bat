@echo off
chcp 936 >nul
title 游戏加速器启动器

echo ======================================
echo          游戏加速器启动器
echo ======================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python 环境
    echo 请安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [信息] 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [信息] 正在启动加速器...
echo.

:: 设置工作目录
cd /d "%~dp0"

:: 启动 Python 程序
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序异常退出
    echo 请查看上方错误信息或检查 accelerator.log 日志文件
    echo.
    pause
    exit /b 1
)

exit /b 0

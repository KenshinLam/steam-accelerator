@echo off
echo 正在以管理员身份启动加速器...
powershell Start-Process python -ArgumentList "run.py" -Verb RunAs -WorkingDirectory "%~dp0"

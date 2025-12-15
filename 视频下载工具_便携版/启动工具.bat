@echo off
chcp 65001 >nul
title 视频下载工具 v5.0

echo ========================================
echo    视频下载工具 v5.0 - 便携版
echo ========================================
echo.
echo 正在启动程序...
echo.

REM 检查exe文件是否存在
if not exist "视频下载工具.exe" (
    echo 错误: 未找到视频下载工具.exe文件
    echo 请确保文件在同一个目录中
    pause
    exit /b 1
)

REM 启动程序
start "" "视频下载工具.exe"

REM 等待一下然后退出
timeout /t 2 >nul
exit

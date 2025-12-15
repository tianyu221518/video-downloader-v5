@echo off
chcp 65001 >nul
echo ========================================
echo         视频下载工具 v1.0
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python环境检查通过
echo.

echo 正在检查依赖包...
python -c "import yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] yt-dlp未安装，正在自动安装...
    pip install yt-dlp
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败，请运行"安装依赖.bat"
        pause
        exit /b 1
    )
)

echo [✓] 依赖检查通过
echo.

echo 正在启动视频下载工具...
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序运行出错，请检查错误信息
    pause
)

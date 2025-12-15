@echo off
chcp 65001 >nul
echo ========================================
echo       视频下载工具 - 依赖安装
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

echo 正在安装依赖包...
echo 这可能需要几分钟时间，请耐心等待...
echo.

pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo [✓] 依赖安装成功！
    echo.
    echo 现在可以运行"启动程序.bat"来启动视频下载工具
) else (
    echo.
    echo [✗] 依赖安装失败，请检查网络连接或手动运行以下命令：
    echo pip install yt-dlp requests
)

echo.
pause

@echo off
chcp 65001 >nul
echo ============================================
echo   酒店房态与入住协同系统 MVP - 启动脚本
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install -r requirements.txt
)

echo [启动] 后端服务启动中...
echo [提示] 启动后浏览器访问 http://127.0.0.1:5001/
echo.
python app.py
pause

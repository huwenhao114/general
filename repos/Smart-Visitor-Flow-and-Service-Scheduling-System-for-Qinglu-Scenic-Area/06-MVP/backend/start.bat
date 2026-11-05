@echo off
chcp 65001 >nul
echo ============================================
echo   青麓景区客流与服务调度系统 MVP - 启动脚本
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装依赖...
    pip install -r requirements.txt
)

echo [启动] 后端服务启动中...
echo [提示] 启动后浏览器访问 http://127.0.0.1:5002/
echo.
python app.py
pause

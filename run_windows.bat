@echo off
chcp 65001 >nul
echo ═══════════════════════════════════
echo 📈 A股尾盘选股系统 启动中...
echo ═══════════════════════════════════

echo 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python, 请先安装: https://www.python.org/downloads/
    echo    安装时勾选 "Add Python to PATH"
    pause
    exit /b
)
echo ✅ Python 已安装

echo 首次运行: 拉取A股全市场数据(本机联网,实时)...
python scripts\fetch_local.py

echo 拉取K线+新闻+情绪数据...
python scripts\cache_kline.py

echo 🚀 启动选股服务...
echo   🔗 浏览器打开: http://localhost:10070
echo   ⏹️ 停止: 关闭此窗口
python server.py
pause

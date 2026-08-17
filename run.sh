#!/bin/bash
# ═══════════════════════════════════════════════════════════
# A股尾盘选股 · 一键启动 (Linux/Mac)
# 用法: bash run.sh  然后浏览器打开 http://localhost:10070
# ═══════════════════════════════════════════════════════════
clear
echo "════════════════════════════════════"
echo "📈 A股尾盘选股系统 启动中..."
echo "════════════════════════════════════"

# 1. 检查 python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3, 请先安装 Python 3"
    read -p "按回车退出"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 2. 首次运行拉取全市场数据(用本机网络,可实时拉)
echo "📥 拉取A股全市场数据(首次需要,本机联网正常)..."
python3 scripts/fetch_local.py 2>&1 | tail -2

# 3. 拉K线+新闻+情绪缓存(本机实时)
echo "📥 拉取K线+新闻+情绪数据..."
python3 scripts/cache_kline.py 2>&1 | tail -3

# 4. 启动服务
echo "🚀 启动选股服务..."
echo "   🔗 浏览器打开: http://localhost:10070"
echo "   ⏹️ 停止: Ctrl+C"
echo "════════════════════════════════════"
python3 server.py

# Windows 双击 bat
cat > run_windows.bat <<'BAT'
@echo off
echo A股尾盘选股系统 启动中...
python --version >nul 2>&1
if errorlevel 1 (
    echo 未找到Python,请安装 https://www.python.org/downloads/
    pause
    exit /b
)
echo 拉取A股数据...
python scripts\fetch_local.py
python scripts\cache_kline.py
echo 启动服务: 浏览器打开 http://localhost:10070
python server.py
pause
BAT
echo ""
echo "✅ 已生成 run_windows.bat (Windows可用)"

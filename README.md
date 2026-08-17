# A股尾盘选股系统（独立）
独立于AI智能体/量化机器人。选尾盘强势股+精确买卖点。
数据: 新浪全市场(5543只,量价)
逻辑: 趋势/量价/箱体突破/支撑压力/涨停潜力/尾盘强势 多维评分
输出: 精选TOP3 + 精确买卖点(买入/目标/止损/盈亏比)
用法: python3 scripts/select.py
部署: 任意有Python3+akshare的环境, 拉取本仓库运行

## 使用步骤
1. 安装依赖: pip install akshare pandas
2. 拉取真实数据: python3 scripts/fetch.py
3. 多维选股+买卖点: python3 scripts/select_real.py
4. 每日14:30后在能联网的电脑运行

## 部署
本系统独立于AI智能体/量化。在你能访问东财/新浪的电脑
git clone 本仓库即可运行。阿里云上东财/新浪全市场被限,
故建议在你本地/境内服务器运行。

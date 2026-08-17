#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📈 A股尾盘选股系统
# 独立系统, 与AI智能体/量化完全分离
# 数据: 新浪全市场(5543只, 量价)
# 逻辑: 趋势/量价/箱体突破/支撑压力/涨停潜力/尾盘强势 多维评分
# 输出: 精选TOP3 + 精确买卖点
# ═══════════════════════════════════════════════════════════
import sys, datetime, json

def simple_scan():
    """示例扫描(生产用可接真实数据)。返回模拟的全市场行情。"""
    # 生产: 用 stock_zh_a_spot() 拉全市场; 这里演示返回示例股票
    demo = [
        {"code":"600519","name":"贵州茅台","close":1500,"open":1460,"high":1510,"low":1445,"vol":120000,"prev":1450,"turnover":6.0},
        {"code":"000858","name":"五粮液","close":155,"open":150,"high":156,"low":149,"vol":80000,"prev":149,"turnover":8.0},
        {"code":"601318","name":"中国平安","close":55,"open":53,"high":55.5,"low":52.8,"vol":150000,"prev":53,"turnover":9.5},
        {"code":"000001","name":"平安银行","close":12,"open":11.5,"high":12.1,"low":11.4,"vol":200000,"prev":11.4,"turnover":10.0},
        {"code":"600036","name":"招商银行","close":38,"open":36.5,"high":38.2,"low":36.2,"vol":160000,"prev":36.6,"turnover":12.0},
    ]
    return demo

def calc_indicators(stock):
    """计算: 趋势/量比/尾盘强势/箱体/支撑压力/涨停潜力"""
    c,o,h,l = stock["close"],stock["open"],stock["high"],stock["low"]
    prev = stock.get("prev",o)
    chg = (c-prev)/prev*100 if prev else 0
    # 量比(用换手率近似资金活跃)
    turnover = stock.get("turnover",0)
    # 尾盘强势: 收盘接近当日高
    tail = (c-l)/(h-l) if h>l else 0.5
    # 箱体突破(简化: 用当日最高突破假设, 生产需历史)
    # 支撑位: 用开盘与最低之间低点; 压力位: 开盘与最高之间高点
    support = min(o,l)
    resistance = max(o,h)
    # 涨停潜力: 涨幅适中+量活跃+尾盘强
    limit_potential = chg + turnover*0.5 + tail*100*0.3
    # 评分(加权): 涨幅+量能+尾盘强度+趋于
    score = chg*0.3 + min(turnover,15)*0.2 + tail*100*0.25 + (chg>0)*30
    return {
        "chg": round(chg,2), "vol_ratio": round(turnover,1), "tail_power": round(tail*100),
        "support": round(support,2), "resistance": round(resistance,2),
        "limit_pot": round(limit_potential,2), "score": round(score,2),
    }

def calc_bs(stock, ind):
    """精确买卖点"""
    price = stock["close"]
    support = ind["support"]
    resistance = ind["resistance"]
    # 次日目标: 冲高压力位; 止损: 跌破支撑-2%
    buy_price = price  # 尾盘/次日开盘买
    target = round(resistance*1.03, 2)   # 冲高3%
    stop = round(support*0.98, 2)          # 跌破支撑-2%止损
    r = round((target-buy_price)/buy_price*100, 2)
    return {"buy": round(buy_price,2), "target": target, "stop": stop, "risk_reward": f"1:{round(r/abs((buy_price-stop)/buy_price*100),1) if buy_price>stop else 0}"}

def main():
    stocks = simple_scan()
    scored=[]
    for s in stocks:
        # 排除不可买(300/688) - 生产接真实代码
        code=s["code"]
        if code.startswith("3") or code.startswith("68") or code.startswith("301"):
            continue
        ind=calc_indicators(s); bs=calc_bs(s,ind)
        scored.append({**s, "ind":ind, "bs":bs})
    scored.sort(key=lambda x:-x["ind"]["score"])
    print(f"=== A股尾盘选股 TOP{min(3,len(scored))} (尾盘数据) ===")
    for i,s in enumerate(scored[:3],1):
        print(f"\n[{i}] {s['code']} {s['name']} 收盘{s['close']}")
        print(f"  涨幅{s['ind']['chg']}% 量比{s['ind']['vol_ratio']} 尾盘强{s['ind']['tail_power']} 评分{s['ind']['score']}")
        print(f"  支撑{s['ind']['support']} 压力{s['ind']['resistance']}")
        print(f"  🎯买入 {s['bs']['buy']} | 目标 {s['bs']['target']} | 止损 {s['bs']['stop']} | 盈亏比 {s['bs']['risk_reward']}")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📈 A股尾盘选股 · 真实数据多维评分版
# 输入: data/market.json (fetch.py 拉取)
# 因子: 趋势/量比/换手/尾盘强势/箱体突破/支撑压力/涨停潜力/涨幅
# 输出: 精选TOP3 + 精确买卖点(买入/目标/止损/盈亏比)
# ═══════════════════════════════════════════════════════════
import json, os, sys

def load():
    if not os.path.exists('data/market.json'):
        print("❌ 无数据。先运行: python3 scripts/fetch.py")
        return []
    with open('data/market.json') as f:
        return json.load(f)

def analyze(s):
    c,o,h,l,p = s['close'], s['open'], s['high'], s['low'], s['prev']
    chg = (c-p)/p*100 if p else 0
    amt = s.get('amount',0)
    turn = s.get('turnover',0)
    # 1 趋势: 价格位置(相对当日区间, 收盘强势=多头信号)
    tail = (c-l)/(h-l)*100 if h>l else 50       # 尾盘强度(收盘在区间位置)
    # 2 量价: 量比(成交额/市值近似失真, 用换手率代表资金活跃)
    vol_active = turn                                   # 换手率=资金活跃
    # 3 涨停潜力: 涨幅适中+放量+尾盘强
    # 4 箱体/支撑压力: 今日高=压力, 低=支撑
    support = l
    resistance = h
    # 5 打分(加权, 尾盘选股次日冲高逻辑)
    score = chg*0.3 + min(turn,20)*0.15 + tail*0.25 + (chg>0)*20 + (amt>0 and (amt/1e8)>1)*15   # 成交额>1亿加分
    # 条件过滤: 涨幅适中+尾盘强+放量
    ok = (2 < chg < 9.5) and tail > 75 and turn > 3 and amt > 1e8
    return {"chg":chg,"turn":turn,"tail":tail,"support":support,"resistance":resistance,"score":score,"ok":ok,"amt":amt}

def bs(s, a):
    # 精确买卖点: 次日冲高到压力位+3%; 止损跌破支撑-2%
    buy = round(s['close'],2)
    target = round(a['resistance']*1.03,2)
    stop = round(a['support']*0.98,2)
    rr = round((target-buy)/max((buy-stop),0.01),1)
    return {"buy":buy,"target":target,"stop":stop,"rr":f"1:{rr}" if rr>0 else "-"}

def main():
    stocks = load()
    if not stocks: return
    results=[]
    for s in stocks:
        a=analyze(s); 
        if a['ok']:
            b=bs(s,a)
            results.append({**s,**a,**b})
    results.sort(key=lambda x:-x['score'])
    print(f"=== A股尾盘选股 TOP{min(3,len(results))} (基于{len(stocks)}只主板可买股) ===")
    if not results:
        print("⚠️ 今日无符合条件的强势股(行情偏弱), 建议空仓观望")
        return
    for i,x in enumerate(results[:3],1):
        print(f"\n[{i}] {x['code']} {x['name']} 收盘{x['close']}")
        print(f"  涨幅{x['chg']:.2f}% 换手{x['turn']:.1f}% 尾盘强{x['tail']:.0f} 成交额{x['amt']/1e8:.1f}亿")
        print(f"  支撑位{x['support']} 压力位{x['resistance']}")
        print(f"  🎯买入 {x['buy']} | 目标 {x['target']} | 止损 {x['stop']} | 盈亏比 {x['rr']} | 评分{x['score']:.1f}")

if __name__=="__main__":
    main()

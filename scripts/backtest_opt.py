#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📊 A股尾盘选股策略回测 (优化版)
# 优化: 1)过滤高波动题材股(避开蓝筹0胜率) 2)测不同止盈目标 3)加量能/波动过滤
# ═══════════════════════════════════════════════════════════
import urllib.request, json, time

UA={'User-Agent':'Mozilla/5.0'}
# 候选: 高波动中小盘(含题材股) + 蓝筹对照
SYMBOLS = ['sz002428','sz002371','sz002916','sh601869','sh603061','sh603129','sh603444','sh603986',
           'sz002584','sh603288','sz300666','sz002475','sh600536','sz300059','sh688981','sz300750',
           'sh600519','sh601318','sh600036','sz000858','sz000001']
K_URL='https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={0},day,,,250,qfq'

def get_kline(sym):
    try:
        req=urllib.request.Request(K_URL.format(sym),headers=UA)
        d=json.loads(urllib.request.urlopen(req,timeout=15).read().decode())
        k=d['data'][sym]['qfqday']
        return [{'date':x[0],'open':float(x[1]),'close':float(x[2]),'high':float(x[3]),'low':float(x[4]),'vol':float(x[5])} for x in k]
    except: return []

def atr_pct(stocks,i,n=14):
    """平均真实波幅% (衡量波动性)"""
    if i<n: return 0
    trs=[]
    for j in range(i-n+1,i+1):
        h,l,pc=stocks[j]['high'],stocks[j]['low'],stocks[j-1]['close']
        trs.append(max(h-l,abs(h-pc),abs(l-pc)))
    return (sum(trs)/n)/stocks[i]['close']*100

def backtest_opt(stocks, target_pct, require_volatility):
    """优化版尾盘策略"""
    trades=0;wins=0;total=0
    for i in range(20,len(stocks)-1):
        d0,d1=stocks[i],stocks[i+1]
        if d0['close']<=d0['open']: continue
        chg=(d0['close']-d0['open'])/d0['open']*100
        if not (2<chg<9): continue
        # 波动率过滤(只做高波动活跃股, 避开死水蓝筹)
        vol=atr_pct(stocks,i)
        if require_volatility and vol<1.0: continue
        # 量比(当日>5日均)
        if d0['vol']<=0: continue
        avg5=sum(stocks[j]['vol'] for j in range(i-4,i+1))/5
        if d0['vol']<avg5*1.3: continue
        # 尾盘强
        tail=(d0['close']-d0['low'])/(d0['high']-d0['low']) if d0['high']>d0['low'] else 0.5
        if tail<0.8: continue
        # 次日: 触目标止盈, 否则收盘卖
        target=d0['close']*(1+target_pct/100)
        ret=target_pct/100 if d1['high']>=target else (d1['close']-d0['close'])/d0['close']
        trades+=1; total+=ret
        if ret>0: wins+=1
    return {'t':trades,'wr':round(wins/trades*100,1) if trades else 0,'avg':round(total/trades*100,2) if trades else 0,'total':round(total*100,1)}

def main():
    print("优化回测: 测试止盈目标 + 波动率过滤")
    for req_vol in [0, 1.0, 1.5]:
        print(f"\n═══ 波动率过滤: {'开(>1%)' if req_vol else '关'} ═══")
        for target in [2,3,4,5]:
            t=w=0; av=[]
            for sym in SYMBOLS:
                s=get_kline(sym)
                if not s: continue
                r=backtest_opt(s,target,req_vol==1.5)
                if r['t']>0: t+=r['t'];w+=r['t']*r['wr']/100;av.extend([r['avg']])
            if t:
                print(f"  止盈{target}%: 交易{t} 胜率{round(w/t*100,1)}% 均单{round(sum(av)/len(av),2)}%")
            time.sleep(0.3)

if __name__=='__main__':
    main()

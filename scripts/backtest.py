#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📊 A股尾盘选股策略回测
# 模拟: 每日尾盘按因子选强势股 → 次日冲高卖出(高点止盈/收盘止损)
# 统计: 胜率/平均收益/总收益/最大回撤
# ═══════════════════════════════════════════════════════════
import urllib.request, json, os, time

UA={'User-Agent':'Mozilla/5.0'}
# 候选池(涨幅靠前的成长股/强势股)
SYMBOLS = ['sz002428','sz002371','sz002916','sh600519','sh601869','sh603061','sh603129','sh603444','sh603986',
           'sz000858','sz000001','sh600036','sh601318','sz002584','sh603288']
K_URL = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={0},day,,,250,qfq'

def get_kline(sym):
    """拉250日K线"""
    try:
        req=urllib.request.Request(K_URL.format(sym),headers=UA)
        d=json.loads(urllib.request.urlopen(req,timeout=15).read().decode())
        k=d['data'][sym]['qfqday']
        return [{
            'date':x[0],'open':float(x[1]),'close':float(x[2]),
            'high':float(x[3]),'low':float(x[4]),'vol':float(x[5])
        } for x in k]
    except: return []

def backtest_tail(stocks):
    """尾盘选股: 用收盘近似尾盘策略, 次日冲高"""
    trades=0; wins=0; total_ret=0; daily=[]
    for i in range(10, len(stocks)-1):
        d0=stocks[i]; d1=stocks[i+1]
        # 选出条件(收盘后判断): 强势(涨>2%) + 放量 + 突破(收>5日均)
        if d0['close'] <= d0['open']: continue  # 需阳线
        chg=(d0['close']-d0['open'])/d0['open']*100
        if not (2 < chg < 9): continue         # 涨幅适中
        if d0['vol'] <= 0: continue
        # 尾盘强势: 收盘接近最高
        tail=(d0['close']-d0['low'])/(d0['high']-d0['low']) if d0['high']>d0['low'] else 0.5
        if tail < 0.8: continue                 # 尾盘顶住高位
        # 次日卖出: 冲高3%止盈, 或收盘卖出
        target=d0['close']*1.03
        if d1['high'] >= target:
            ret=0.03; wins+=1                    # 触目标止盈
        else:
            ret=(d1['close']-d0['close'])/d0['close']  # 未到目标,收盘卖出
        trades+=1; total_ret+=ret; daily.append(ret)
    wr = wins/trades*100 if trades else 0
    avg = total_ret/trades*100 if trades else 0
    # 最大回撤(按日收益)
    cum=0; mx=0; peak=0
    for r in daily:
        cum+=r; peak=max(peak,cum); mx=min(mx,cum-peak)
    return {'trades':trades,'winRate':round(wr,1),'avg':round(avg,2),'total':round(total_ret*100,1),'maxdd':round(mx*100,1)}

def main():
    print("开始回测 A股尾盘选股策略...")
    all_results=[]
    fetched=0
    for sym in SYMBOLS:
        stocks=get_kline(sym)
        if not stocks: continue
        fetched+=1
        r=backtest_tail(stocks)
        if r['trades']>0:
            all_results.append(r)
            print(f"{sym}: 交易{r['trades']}次 胜率{r['winRate']}% 均收益{r['avg']}% 总收益{r['total']}% 最大回撤{r['maxdd']}%")
        time.sleep(0.5)
    # 汇总
    t=sum(x['trades'] for x in all_results); w=sum(x['trades']*x['winRate']/100 for x in all_results)
    av=sum(x['avg'] for x in all_results)/len(all_results)
    print(f"\n═══ 回测汇总 (拉取{fetched}只, 有效{len(all_results)}只) ═══")
    print(f"总交易: {t}次 | 平均胜率: {round(w/t*100 if t else 0,1)}% | 平均单笔: {round(av,2)}%")
    print(f"注: 样本为候选强势股近250日, 策略=尾盘强涨→次日冲高3%止盈")

if __name__=='__main__':
    main()

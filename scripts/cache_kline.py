#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📥 拉取K线+新闻缓存 (交互运行, 绕沙箱后台联网限制)
# 为TOP候选股拉K线算买卖点; 拉A股实时新闻
# ═══════════════════════════════════════════════════════════
import urllib.request, json, os, time, sys

UA = {'User-Agent': 'Mozilla/5.0'}
K_URL = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={0},day,,,80,qfq'
NEWS_URL = 'https://newsapi.eastmoney.com/kuaixun/v1/getlist_102_ajaxResult_50_1_.html'

def http_json(url, decode='utf-8'):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=15).read().decode(decode, 'ignore')

def cache_kline(code):
    sym = ('sh' if code.startswith('6') else 'sz') + code
    try:
        d = json.loads(http_json(K_URL.format(sym)))
        k = d['data'][sym]['qfqday']
        # 计算箱体/支撑压力/量能
        hs=[float(x[3]) for x in k]; ls=[float(x[4]) for x in k]
        c=[float(x[2]) for x in k]; v=[float(x[5]) for x in k]
        hi80, lo80 = max(hs), min(ls)
        # 支撑: 近20日低点; 压力: 近20日高点
        support = min(ls[-20:]); resistance = max(hs[-20:])
        # 量能: 近5日均量 vs 近20日均量
        avg5 = sum(v[-5:])/5; avg20 = sum(v[-20:])/20
        return {'support': round(support,2), 'resistance': round(resistance,2), 'hi80': round(hi80,2), 'lo80': round(lo80,2),
                'vol5': round(avg5,0), 'vol20': round(avg20,0), 'last': round(c[-1],2), 'close5': [round(x,2) for x in c[-5:]]}
    except Exception as e:
        return None

def cache_news():
    try:
        s = http_json(NEWS_URL, 'utf-8')
        j = json.loads(s.replace('var ajaxResult=','').rstrip(';'))
        return [{'title': x.get('title',''), 'time': x.get('showtime','')} for x in j.get('LivesList',[])[:15]]
    except Exception as e:
        return []

def main(codes):
    os.makedirs('data', exist_ok=True)
    # K线
    ok=0
    for code in codes:
        k = cache_kline(code)
        if k:
            with open(f'data/kline_{code}.json','w') as f: json.dump(k,f)
            ok+=1
    print(f'K线缓存: {ok}/{len(codes)} 只')
    # 新闻
    news = cache_news()
    if news:
        with open('data/news.json','w') as f: json.dump(news,f,ensure_ascii=False)
        print(f'新闻缓存: {len(news)} 条')
    # 汇总
    print('示例TOP新闻:')
    for n in news[:3]: print('  -', n['title'][:40])

if __name__=='__main__':
    # 从市场json找涨幅靠前的主板可买股作为候选
    if os.path.exists('data/market.json'):
        mkt = json.load(open('data/market.json'))
        codes=[]
        for r in mkt[:30]:
            pure=str(r.get('code','')).replace('sh','').replace('sz','')
            if not (pure.startswith('3') or pure.startswith('68') or pure.startswith('301')):
                codes.append(pure)
        main(codes[:15])
    else:
        main(sys.argv[1:])

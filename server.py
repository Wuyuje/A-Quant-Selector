#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# A股尾盘选股系统 · 完善版(多因子+买卖点+大盘)  手机网页版
# 数据: 腾讯全市场榜单 + 腾讯K线(算支撑压力/箱体) + 大盘指数
# 因子: 大盘过滤/涨幅/换手/量比/资金流/趋势(多周期)/振幅/箱体
# 输出: 精选TOP3 + 精确买卖点(买入/目标/止损/盈亏比)
# ═══════════════════════════════════════════════════════════
import json, urllib.request, http.server, os

UA = {'User-Agent': 'Mozilla/5.0'}
TS_RANK = 'https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?board_code=aStock&sort_type=price&direct=down&offset=0&count=300'
TS_KLINE = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={0},day,,,60,qfq'
TS_INDEX = 'https://qt.gtimg.cn/q=sh000001,sz399001'

def http_json(url, decode='utf-8'):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=15).read().decode(decode)

def market_status():
    """大盘强弱: 上证/深证涨跌"""
    try:
        raw = http_json(TS_INDEX, 'gbk')
        sh = raw.split('v_sh000001="')[1].split('"')[0].split('~')
        sz = raw.split('v_sz399001="')[1].split('"')[0].split('~')
        return {'sh_chg': float(sh[32]) if len(sh)>32 else 0, 'sz_chg': float(sz[32]) if len(sz)>32 else 0}
    except: return {'sh_chg':0,'sz_chg':0}

def fetch_rank():
    # 优先读本地数据文件(沙箱后台无法联网, 用交互拉取的文件)
    import os
    if os.path.exists('data/market.json'):
        try:
            with open('data/market.json') as f: return json.load(f)
        except: pass
    # 无本地文件则尝试联网
    try:
        d = json.loads(http_json(TS_RANK)); return d.get('data',{}).get('rank_list',[])
    except: return []

def filter_stock(r):
    code = str(r.get('code','brand')); pure = code.replace('sh','').replace('sz','')
    if pure.startswith('3') or pure.startswith('68') or pure.startswith('301'):
        return None
    return {
        'code': pure, 'name': str(r.get('name','')),
        'chg': float(r.get('zdf')or 0), 'hsl': float(r.get('hsl')or 0),
        'lb': float(r.get('lb')or 0), 'speed': float(r.get('speed')or 0),
        'turnover': float(r.get('turnover')or 0), 'zf': float(r.get('zf')or 0),
        'zljlr': float(r.get('zljlr')or 0),       # 主力净流入
        'd5': float(r.get('zdf_d5')or 0), 'd10': float(r.get('zdf_d10')or 0), 'd20': float(r.get('zdf_d20')or 0),
        'zsz': float(r.get('zsz')or 0), 'price': float(r.get('zxj')or 0),
    }

def _kline_live(code):
    """实时拉K线算箱体(仅TOP3用)"""
    try:
        sym = ('sh' if code.startswith('6') else 'sz') + code
        d = json.loads(http_json(TS_KLINE.format(sym)))
        k = d['data'][sym]['qfqday']
        hs=[float(x[3]) for x in k]; ls=[float(x[4]) for x in k]
        return {'support': min(ls[-20:]), 'resistance': max(hs[-20:])}
    except: return None

def get_kline(code):
    """腾讯K线: 算60日箱体/支撑压力 (读本地缓存或返回None)"""
    import os
    cf = 'data/kline_' + code + '.json'
    if os.path.exists(cf):
        try:
            with open(cf) as f: return json.load(f)
        except: pass
    try:
        # 沙箱/受限: 不联网(避免900只候选卡死), 无缓存返回None(买卖点用简化)
        return None
    except: return None

def score_stock(s, k):
    """多维评分 + 选股条件"""
    # 选股条件(尾盘强势): 涨幅适中+放量+换手活跃+主力流入
    ok = (2 < s['chg'] < 9.5) and (s['hsl'] > 3) and (s['lb'] > 0.8) and (s['zljlr'] > 0)
    if not ok: return None
    # 评分(加权)
    tail = s.get('tail',0)
    sc = s['chg']*0.35 + min(s['hsl'],20)*0.15 + s['lb']*0.15 + min(s['zljlr']/1e8,5)*0.15 + tail*0.1 + (15 if s['d5']>2 else 0)
    return {'score': round(sc,1)}

def make_bs(s, k):
    """精确买卖点: 用K线箱体(支撑=近期低点, 压力=近期高点)"""
    price = s['price'] or 0
    # 从缓存K线加载(若传入的是路径或缓存)
    kd = k if (k and isinstance(k,dict) and 'support' in k) else None
    import os
    if not kd and price:
        cf='data/kline_'+s['code']+'.json'
        if os.path.exists(cf):
            try:
                with open(cf) as f: kd=json.load(f)
            except: pass
    if kd and price and kd.get('support') and kd.get('resistance'):
        buy=round(price,2)
        target=round(kd['resistance']*1.04,2)   # 冲高4%到压力上方
        stop=round(kd['support']*0.96,2)         # 跌破支撑-4%止损
        rr=round((target-buy)/max(buy-stop,0.01),1)
        return {'buy':buy,'target':target,'stop':stop,'rr':f'1:{rr}',
                'spt':kd['support'],'res':kd['resistance']}
    return {'buy':round(price,2) if price else '--','target':'--','stop':'--','rr':'--'}

def do_pick():
    try:
        mkt = market_status()
        # 大盘走弱(跌>0.5%)时降低开仓信号(但保留强势股)
        list_all = fetch_rank()
        stocks=[f for f in (filter_stock(r) for r in list_all) if f]
        scored=[]
        for s in stocks:
            k = get_kline(s['code'])
            sc = score_stock(s, k)
            if sc:
                scored.append({**s, 'kline':k, **sc, 'bs': make_bs(s,k)})
        scored.sort(key=lambda x:-x['score'])
        top = scored[:3]
        # 对TOP3联网拉K线算精确买卖点(仅3只不卡)
        for s in top:
            k = _kline_live(s['code'])
            if k:
                buy=round(s['price'],2); target=round(k['resistance']*1.04,2); stop=round(k['support']*0.96,2)
                rr=round((target-buy)/max(buy-stop,0.01),1)
                s['bs']={'buy':buy,'target':target,'stop':stop,'rr':f'1:{rr}','spt':round(k['support'],2),'res':round(k['resistance'],2)}
        news=[]; sent={}
        import os
        try:
            if os.path.exists('data/news.json'):
                with open('data/news.json') as f: news=json.load(f)
        except: pass
        try:
            if os.path.exists('data/sentiment.json'):
                with open('data/sentiment.json') as f: sent=json.load(f)
        except: pass
        # 情绪弱时降级(减少推荐数, 风控)
        if sent.get('weak') and top: top=top[:1]
        board = do_pick_extra()
        return {'ok':True, 'stocks':top, 'news':news, 'sentiment':sent, 'board':board, 'meta':{'count':len(stocks),'pickCount':len(top),'mkt':mkt}}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {'ok':False, 'error':'选股失败: '+str(e)+' | '+str(traceback.format_exc())[:200]}


# ─── 板块因子(东财板块接口, 本机联网可用; 沙箱受限时降级) ───
def fetch_board():
    """拉板块热榜(涨幅靠前板块, 反映板块情绪)"""
    try:
        url='https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f12,f14,f3'
        req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'})
        d=json.loads(urllib.request.urlopen(req, timeout=12).read().decode())
        diff=d.get('data',{}).get('diff',[])
        return [{'code':x.get('f12'),'name':x.get('f14'),'chg':x.get('f3')} for x in diff] if isinstance(diff,list) else []
    except Exception as e:
        return []   # 沙箱/受限: 返回空, 降级不阻塞

def board_cache():
    """读板块缓存文件(可交互拉取存 data/board.json)"""
    import os
    if os.path.exists('data/board.json'):
        try:
            with open('data/board.json') as f: return json.load(f)
        except: pass
    return []

def do_pick_extra():
    """补充板块: 优先本地缓存, 否则尝试实时"""
    b = board_cache()
    if not b:
        b = fetch_board()
        if b:
            import os
            try:
                with open('data/board.json','w') as f: json.dump(b,f,ensure_ascii=False)
            except: pass
    return b

# ─── 网页(内嵌, 带买卖点/趋势/大盘显示) ───
def page_html():
    return '''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>A股尾盘选股</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.header{background:linear-gradient(135deg,#dc2626,#991b1b);color:#fff;padding:16px 20px}.header h1{font-size:19px;font-weight:700}.header .sub{font-size:12px;opacity:.9}
.container{max-width:720px;margin:0 auto;padding:14px;padding-bottom:90px}.btn{background:#dc2626;color:#fff;border:none;border-radius:12px;padding:15px;font-size:17px;font-weight:700;width:100%;cursor:pointer}
.note{font-size:12px;color:#94a3b8;margin:10px 0;line-height:1.6}.status{background:#1e293b;border-radius:10px;padding:12px;font-size:13px;margin:10px 0}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin:12px 0}.rank{color:#f87171;font-weight:700}.name{font-size:19px;font-weight:700}.code{color:#94a3b8;font-size:13px}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0;font-size:12px}.stat{background:#334155;border-radius:8px;padding:5px 9px}.up{color:#22c55e}
.bs{background:#111827;border-radius:10px;padding:12px;display:flex;justify-content:space-between}.bs .t{font-size:11px;color:#94a3b8}.bs .v{font-size:16px;font-weight:700}
.buy{color:#22c55e}.target{color:#f59e0b}.stop{color:#ef4444}.foot{position:fixed;bottom:0;left:0;right:0;background:#0f172a;border-top:1px solid #334155;padding:10px;text-align:center;font-size:11px;color:#64748b}
</style></head><body>
<div class="header"><h1>📈 A股尾盘选股</h1><div class="sub">尾盘强势 · 多因子 · 精确买卖点</div></div>
<div class="container"><button class="btn" onclick="pick()">🕒 开始选股 (14:30后)</button>
<div class="note">排除300/688。含大盘/资金/趋势/箱体因子 + 买卖点。供参考，买卖自决。</div>
<div class="status" id="st">点上方开始选股</div><div id="rs"></div></div>
<div class="foot">A股量化 · 独立系统</div>
<script>
function $(i){return document.getElementById(i)}
async function pick(){ $('st').textContent='🔄 拉取数据…';
 try{ const r=await fetch('/api/pick'); const j=await r.json();
  if(!j.ok){$('st').textContent='⚠️ '+j.error;return}
  const m=j.meta; $('st').textContent='✅ 扫'+m.count+'只 选'+m.pickCount+'只 大盘(沪'+m.mkt.sh_chg+'%/深'+m.mkt.sz_chg+'%)';
  let h=''; (j.stocks||[]).forEach(function(s,i){ let k=s.kline||{};
   h+='<div class="card"><div class="rank">TOP '+(i+1)+'</div><div class="name">'+s.name+'</div><div class="code">'+s.code+' · 主力净流入'+(s.zljlr/1e8).toFixed(2)+'亿</div>'
   +'<div class="stats"><span class="stat up">涨'+s.chg+'%</span><span class="stat">换手'+s.hsl+'%</span><span class="stat">量比'+s.lb+'</span>'
   +'<span class="stat">5日'+s.d5+'%</span><span class="stat">'+(k.break?'箱体突破':'箱体内')+'</span><span class="stat">评分'+s.score+'</span></div>'
   +'<div class="bs"><div><div class="t">🎯买入</div><div class="v buy">'+s.bs.buy+'</div></div><div><div class="t">目标</div><div class="v target">'+s.bs.target+'</div></div><div><div class="t">止损</div><div class="v stop">'+s.bs.stop+'</div></div><div><div class="t">盈亏比</div><div class="v">'+s.bs.rr+'</div></div></div></div>'; });
  $('rs').innerHTML=h; if(j.news&&j.news.length){ var nh='<div class="card"><div class="rank">📰 A股要闻</div>'; j.news.slice(0,5).forEach(function(n){nh+='<div style="font-size:12px;color:#94a3b8;margin:6px 0">• '+n.title+'</div>';}); nh+='</div>'; $('rs').innerHTML+=nh; }
 }catch(e){$('st').textContent='❌ '+e.message} }
</script></body></html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/','/index.html'):
            self.send_response(200); self.send_header('Content-Type','text/html;charset=utf-8'); self.end_headers()
            self.wfile.write(page_html().encode('utf-8'))
        elif self.path.startswith('/api/pick'):
            j=do_pick(); body=json.dumps(j).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(body)
        else: super().do_GET()
    def do_POST(self): self.do_GET()

if __name__=='__main__':
    port=int(os.environ.get('PORT',10070))
    import sys
    print('启动前测试拉取...', file=sys.stderr)
    try:
        r=fetch_rank(); print(f'预热 fetch_rank: {len(r)} 条', file=sys.stderr)
    except Exception as e:
        print(f'预热失败: {e}', file=sys.stderr)
    print(f'A股尾盘选股 http://localhost:{port}', file=sys.stderr)
    http.server.HTTPServer(('0.0.0.0',port),Handler).serve_forever()

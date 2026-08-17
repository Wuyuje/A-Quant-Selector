#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# A股尾盘选股系统 · Python后端 (手机/平板网页版)
# Python urllib拉腾讯全市场 (避开Node沙箱网络bug)
# 提供: 网页 + /api/pick 选股接口
# ═══════════════════════════════════════════════════════════
import json, urllib.request, http.server, os, sys

TS_URL = 'https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?board_code=aStock&sort_type=price&direct=down&offset=0&count={}'

def fetch_rank(count=200):
    """拉腾讯全市场榜单"""
    url = TS_URL.format(count)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    d = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    return d.get('data', {}).get('rank_list', [])

def filter_stock(r):
    """排除300/688/301(买不了), 返回可用字段"""
    code = str(r.get('code',''))  # sh600519
    pure = code.replace('sh','').replace('sz','')
    if pure.startswith('3') or pure.startswith('68') or pure.startswith('301'):
        return None
    return {
        'code': pure, 'name': str(r.get('name','')),
        'chg': float(r.get('zdf') or 0),      # 涨跌幅%
        'hsl': float(r.get('hsl') or 0),      # 换手率%
        'lb': float(r.get('lb') or 0),        # 量比
        'volume': float(r.get('volume') or 0),
    }

def score_stock(s):
    """尾盘选股评分: 强势涨幅+放量+换手活跃"""
    ok = 2 < s['chg'] < 9.5 and s['hsl'] > 3 and s['hsl'] < 25 and s['lb'] >= 1
    sc = s['chg']*0.4 + s['hsl']*0.25 + s['lb']*0.2 + (15 if s['chg']>4 else 0)
    return ok, round(sc, 1)

def do_pick():
    """完整选股流程 → TOP3"""
    try:
        list_all = fetch_rank(200)
        stocks = [f for f in (filter_stock(r) for r in list_all) if f]
        scored = []
        for s in stocks:
            ok, sc = score_stock(s)
            if ok:
                # 买卖点: (简化) 次日目标=今日涨幅延续, 止损=防回落
                scored.append({**s, 'score': sc,
                    'bs': {'buy':'--','target':'--','stop':'--','rr':'--'}})
        scored.sort(key=lambda x: -x['score'])
        top = scored[:3]
        return {'ok': True, 'stocks': top, 'meta': {'count': len(stocks), 'pickCount': len(top)}}
    except Exception as e:
        return {'ok': False, 'error': '选股失败: ' + str(e)}

# 网页HTML(手机/平板适配, 内联)
def page_html():
    return '''<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>A股尾盘选股</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,Roboto,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.header{background:linear-gradient(135deg,#dc2626,#991b1b);color:#fff;padding:16px 20px}
.header h1{font-size:19px;font-weight:700}.header .sub{font-size:12px;opacity:.9;margin-top:2px}
.container{max-width:720px;margin:0 auto;padding:14px;padding-bottom:90px}
.btn{background:#dc2626;color:#fff;border:none;border-radius:12px;padding:15px;font-size:17px;font-weight:700;width:100%;cursor:pointer}
.btn:active{background:#b91c1c}
.note{font-size:12px;color:#94a3b8;margin:10px 0;line-height:1.6}
.status{background:#1e293b;border-radius:10px;padding:12px;font-size:13px;margin:10px 0}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;margin:12px 0}
.rank{font-size:14px;font-weight:700;color:#f87171}.name{font-size:19px;font-weight:700}.code{font-size:13px;color:#94a3b8}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0;font-size:13px}
.stat{background:#334155;border-radius:8px;padding:6px 10px}
.bs{background:#111827;border-radius:10px;padding:12px;display:flex;justify-content:space-between}
.bs .t{font-size:11px;color:#94a3b8}.bs .v{font-size:16px;font-weight:700}.buy{color:#22c55e}.target{color:#f59e0b}.stop{color:#ef4444}
.foot{position:fixed;bottom:0;left:0;right:0;background:#0f172a;border-top:1px solid #334155;padding:10px;text-align:center;font-size:11px;color:#64748b}
</style></head><body>
<div class="header"><h1>📈 A股尾盘选股</h1><div class="sub">尾盘强势 · 次日冲高 · 精选TOP3</div></div>
<div class="container">
<button class="btn" onclick="pick()">🕒 开始选股 (14:30后)</button>
<div class="note">排除300/688/301。选主板可买强势股。趋势/量价/换手多维评分。</div>
<div class="status" id="st">点上方开始选股</div><div id="rs"></div>
</div>
<div class="foot">A股量化 · 独立系统 · 供参考买卖自决</div>
<script>
function $(i){return document.getElementById(i)}
async function pick(){ $('st').textContent='🔄 拉取全市场数据…';
  try{ const r=await fetch('/api/pick'); const j=await r.json();
    if(!j.ok){$('st').textContent='⚠️ '+j.error;return}
    $('st').textContent='✅ 选出 '+j.meta.pickCount+' 只 (扫'+j.meta.count+'只)';
    let h=''; (j.stocks||[]).forEach(function(s,i){ h+=
      '<div class="card"><div class="rank">TOP '+(i+1)+'</div><div class="name">'+s.name+'</div><div class="code">'+s.code+'</div>'+
      '<div class="stats"><span class="stat">涨幅 '+s.chg+'%</span><span class="stat">换手 '+s.hsl+'%</span><span class="stat">量比 '+s.lb+'</span><span class="stat">评分 '+s.score+'</span></div>'+
      '<div class="bs"><div><div class="t">🎯买入</div><div class="v buy">'+s.bs.buy+'</div></div><div><div class="t">目标</div><div class="v target">'+s.bs.target+'</div></div><div><div class="t">止损</div><div class="v stop">'+s.bs.stop+'</div></div></div></div>';
    }); $('rs').innerHTML=h;
  }catch(e){$('st').textContent='❌ '+e.message} }
</script></body></html>'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send_response(200); self.send_header('Content-Type','text/html;charset=utf-8'); self.end_headers()
            self.wfile.write(page_html().encode('utf-8'))
        elif self.path == '/api/pick' or self.path.startswith('/api/pick'):
            j = do_pick(); body = json.dumps(j).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()
    def do_POST(self):
        if self.path == '/api/pick':
            j = do_pick()
            body = json.dumps(j).encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404); self.end_headers()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10070))
    print(f'A股尾盘选股 http://localhost:{port}')
    http.server.HTTPServer(('0.0.0.0', port), Handler).serve_forever()

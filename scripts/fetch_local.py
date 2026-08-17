#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📥 拉取A股全市场榜单数据存本地 (交互运行, 绕沙箱后台网络隔离)
# 你本机: 直接 python scripts/fetch_local.py 即可实时拉
# ═══════════════════════════════════════════════════════════
import urllib.request, json, os, time

UA = {'User-Agent': 'Mozilla/5.0'}
TS_RANK = 'https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?board_code=aStock&sort_type=price&direct=down&offset=0&count={}'

def fetch(offset=0, count=100):
    url = TS_RANK.format(count)
    req = urllib.request.Request(url, headers=UA)
    d = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
    return d.get('data', {}).get('rank_list', [])

def main():
    os.makedirs('data', exist_ok=True)
    # 分页拉全市场(每页100, 最多500只, 含强趋势股/领涨)
    all_data = []
    try:
        # 拉涨幅靠前(强势候选)
        for off in [0, 100, 200]:
            try:
                r = fetch(off, 100)
                if r: all_data.extend(r)
            except Exception as e:
                print(f'分页{off}失败: {e}', file=os.sys.stderr)
            time.sleep(0.5)
        # 也拉跌幅靠前作为对照(可选, 用换手排序再拉一批)
        with open('data/market.json', 'w') as f:
            json.dump(all_data, f, ensure_ascii=False)
        print(f'✅ 已拉取 {len(all_data)} 只到 data/market.json')
    except Exception as e:
        print(f'拉取失败: {e}')

if __name__ == '__main__':
    main()

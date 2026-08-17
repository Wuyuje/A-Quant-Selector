#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════
# 📥 拉取A股全市场数据(多数据源容错)
# 首选: 东方财富(全市场+板块, 需要能访问东财的网络)
# 备选: 新浪全市场
# 在你的本地电脑/能访问东财的环境运行即可拉全
# ═══════════════════════════════════════════════════════════
import sys, json, os

def fetch_east_gold():
    """东方财富全市场(含板块/资金流, 最全但需能访问东财)"""
    try:
        import akshare as ak
        print("拉取东方财富全市场...", file=sys.stderr)
        df = ak.stock_zh_a_spot_em()
        stocks = []
        for _, r in df.iterrows():
            code = str(r.get('代码',''))
            if code.startswith('3') or code.startswith('68') or code.startswith('301'):
                continue
            c = float(r.get('最新价',0) or 0)
            if c <= 0: continue
            stocks.append({
                "code": code, "name": str(r.get('名称','')),
                "close": c,
                "prev": float(r.get('昨收',c) or c),
                "open": float(r.get('今开',c) or c),
                "high": float(r.get('最高',c) or c),
                "low": float(r.get('最低',c) or c),
                "amount": float(r.get('成交额',0) or 0),
                "turnover": float(r.get('换手率',0) or 0),
                "chg": float(r.get('涨跌幅',0) or 0),
            })
        print(f"东方财富: {len(stocks)} 只主板可买股", file=sys.stderr)
        return stocks
    except Exception as e:
        print(f"东方财富失败: {e}", file=sys.stderr)
        return []

def fetch_sina():
    """新浪全市场(备选, 需能访问新浪)"""
    try:
        import akshare as ak
        print("拉取新浪全市场...", file=sys.stderr)
        df = ak.stock_zh_a_spot()
        stocks = []
        for _, r in df.iterrows():
            code = str(r.get('代码',''))
            if code.startswith('3') or code.startswith('68') or code.startswith('301'):
                continue
            c = float(r.get('最新价',0) or 0)
            if c <= 0: continue
            stocks.append({
                "code": code, "name": str(r.get('名称','')),
                "close": c,
                "prev": float(r.get('昨收',c) or c),
                "open": float(r.get('今开',c) or c),
                "high": float(r.get('最高',c) or c),
                "low": float(r.get('最低',c) or c),
                "amount": float(r.get('成交额',0) or 0),
                "turnover": float(r.get('换手率',0) or 0),
                "chg": float(r.get('涨跌幅',0) or 0),
            })
        print(f"新浪: {len(stocks)} 只主板可买股", file=sys.stderr)
        return stocks
    except Exception as e:
        print(f"新浪失败: {e}", file=sys.stderr)
        return []

def fetch_all():
    # 东方财富优先(数据全), 失败换新浪
    s = fetch_east_gold()
    if not s:
        s = fetch_sina()
    return s

if __name__ == "__main__":
    s = fetch_all()
    if s:
        os.makedirs('data', exist_ok=True)
        with open('data/market.json','w') as f:
            json.dump(s, f, ensure_ascii=False)
        print(f"✅ 已保存 {len(s)} 只到 data/market.json")
    else:
        print("❌ 数据源都失败。请确认网络能访问东财/新浪")

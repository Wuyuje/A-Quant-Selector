#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════
// A股尾盘选股系统 - Node后端
// 封装腾讯全市场榜单→多维评分→TOP3+买卖点
// 网页前端调本后端(同源无CORS问题), 供手机/平板使用
// ═══════════════════════════════════════════════════════════
const express = require('express');
const http = require('http');
const https = require('https');
const app = express();
const PORT = process.env.PORT || 10070;

// 取腾讯榜单数据(全市场)
function fetchRank(count=100) {
  return fetch('https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList?board_code=aStock&sort_type=price&direct=down&offset=0&count=' + count, { headers: { 'User-Agent': 'Mozilla/5.0' }, timeout: 15000 })
    .then(r => r.json()).then(j => Promise.resolve((j && j.data && j.data.rank_list) || []))
    .catch(() => Promise.resolve([]));
}

// 排除不可买(300/688/301); 提取字段
function parseStock(r) {
  const code = String(r.code||'');  // 如 sh600519
  const pure = code.replace(/^(sh|sz)/,'');
  if (pure.startsWith('3') || pure.startsWith('68') || pure.startsWith('301')) return null;
  return {
    code: pure, name: String(r.name||''),
    chg: parseFloat(r.zdf) || 0,        // 涨跌幅%
    hsl: parseFloat(r.hsl) || 0,        // 换手率%
    lb: parseFloat(r.lb) || 0,          // 量比
    volume: parseFloat(r.volume) || 0,  // 成交量
  };
}

// 多维评分(尾盘选股次日冲高逻辑)
function score(s) {
  // 强势: 涨幅2-9.5; 换手活跃3-20; 量比>1; 尾盘无数据近似用涨幅+换手
  const ok = s.chg>2 && s.chg<9.5 && s.hsl>3 && s.hsl<25 && s.lb>=1;
  sc = s.chg*0.4 + s.hsl*0.25 + s.lb*0.2 + (s.chg>4?15:0);
  return { ok, score: sc };
}

app.use(express.static('web'));

// 选股接口
app.post('/api/stock/pick', async (req,res) => {
  try {
    const list = await fetchRank(200);
    const parsed = list.map(parseStock).filter(Boolean);
    const scored = parsed.map(s=>({...s, ...score(s)})).filter(x=>x.ok);
    scored.sort((a,b)=>b.score-a.score);
    const top = scored.slice(0,3).map(s=>{
      // 买卖点: 无历史K用简化(按当日涨幅+换手估目标)
      const buy = 0;  // 需实时价, 腾讯榜单无比价, 简化
      return {
        code:s.code, name:s.name, chg:s.chg, turn:s.hsl, lb:s.lb, score: Math.round(s.score),
        bs: { buy:'--', target:'--', stop:'--', rr:'--' }
      };
    });
    res.json({ ok:true, stocks:top, meta:{ count:parsed.length, pickCount:top.length } });
  } catch(e){
    res.json({ ok:false, error:'选股失败: '+e.message });
  }
});

app.listen(PORT, ()=>console.log(`A股尾盘选股系统 http://localhost:${PORT}`));

#!/usr/bin/env python3
"""Mark Minervini 超級績效策略 v1.0"""
import urllib.request, json
from datetime import datetime, timedelta

API = "https://api.finmindtrade.com/api/v4/data"

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except:
        return None

def get_prices(stock):
    url = f"{API}?dataset=TaiwanStockPrice&data_id={stock}&start_date=2025-06-18&end_date=2026-04-14"
    d = fetch(url)
    return d.get("data", []) if d and d.get("status") == 200 else []

def analyze(code, name):
    prices = get_prices(code)
    if len(prices) < 180:
        return None
    
    c = [float(p["close"]) for p in prices]
    h = [float(p["max"]) for p in prices]
    l = [float(p["min"]) for p in prices]
    v = [int(p["Trading_Volume"]) for p in prices]
    
    m50 = sum(c[-50:]) / 50
    m150 = sum(c[-150:]) / 150
    m200 = sum(c[-200:]) / 200
    h52 = max(h[-250:]) if len(h) >= 250 else max(h)
    l52 = min(l[-250:]) if len(l) >= 250 else min(l)
    cur = c[-1]
    vol = v[-1]
    
    score = 0
    s2 = cur > m50 > m150 > m200
    if s2: score += 40
    
    if l52 > 0:
        if (cur - l52) / l52 * 100 >= 30: score += 15
        if (h52 - cur) / h52 * 100 <= 25: score += 15
    
    if vol > 1500000: score += 10
    
    sig = "🟢強勢" if score >= 70 else "🟡偏多" if score >= 50 else "⚪觀察" if score >= 30 else "🔴不符"
    
    return {"code": code, "name": name, "price": cur, "m50": m50, "m150": m150, "m200": m200,
            "h52": h52, "l52": l52, "score": score, "signal": sig, "stage2": s2, "vol": vol}

stocks = [("2330","台積電"), ("3413","京元電"), ("3037","景碩"), ("2454","聯發科"),
         ("6669","緯穎"), ("2303","聯電"), ("3211","順達"), ("2492","欣興")]

results = []
for code, name in stocks:
    r = analyze(code, name)
    if r:
        results.append(r)
        s2 = "✅" if r["stage2"] else "❌"
        print(f"{code} {name[:4]} | {r['score']:3d}分 {r['signal']} | Stage2:{s2} | {r['price']:.0f}")

results.sort(key=lambda x: x["score"], reverse=True)
print("\n=== Minervini 排名 ===")
for i, r in enumerate(results, 1):
    s2 = "✅" if r["stage2"] else "❌"
    print(f"{i}. {r['code']} {r['name'][:4]} | {r['score']}分 {r['signal']} | Stage2:{s2}")
#!/usr/bin/env python3
"""
Alpha Daily Scanner v1.0
最省 token 的股票篩選系統
"""

import urllib.request
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"
DB_PATH = "/home/node/.openclaw/workspace/projects/tw-stock-daily-report/scripts/alpha/signals.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_no TEXT, date TEXT, signal_type TEXT,
            alpha_score INTEGER, confidence TEXT,
            actual_return REAL, validated INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS validation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_no TEXT, signal_date TEXT,
            entry_price REAL, exit_price REAL,
            holding_days INTEGER, return_pct REAL,
            validated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_signal(stock, signal_type, score, confidence):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals (stock_no, date, signal_type, alpha_score, confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (stock, datetime.now().strftime("%Y-%m-%d"), signal_type, score, confidence, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except:
        return None

def get_stock_list():
    return [
        "2330", "2303", "2454", "3034", "3413", "3037", "4958",
        "2379", "3211", "6669", "3545",
        "2886", "2891", "5871", "3010",
        "8046", "2492", "4532",
    ]

def quick_scan(stock):
    """快速篩選：只取本月數據"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = datetime.now().strftime("%Y-%m-01")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    if not data or not data.get("data"):
        return None
    
    prices = data["data"]
    if len(prices) < 5:
        return None
    
    closes = [float(p.get("close", 0)) for p in prices]
    volumes = [int(p.get("Trading_Volume", 0)) for p in prices]
    
    current = closes[-1]
    ma5 = sum(closes[-5:]) / min(5, len(closes))
    ma10 = sum(closes[-10:]) / min(10, len(closes)) if len(closes) >= 10 else ma5
    vol_avg = sum(volumes) / len(volumes) if volumes else 1
    vol_now = volumes[-1] if volumes else 0
    
    score = 0
    if ma5 > ma10:
        score += 30
    else:
        score -= 20
    
    if vol_now > vol_avg * 1.5:
        score += 25
    elif vol_now > vol_avg * 1.2:
        score += 15
    
    mom = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    if mom > 5:
        score += 20
    elif mom > 0:
        score += 10
    elif mom < -5:
        score -= 20
    
    return {
        "stock": stock,
        "price": current,
        "ma5": ma5,
        "ma10": ma10,
        "mom": mom,
        "vol_ratio": vol_now / vol_avg if vol_avg > 0 else 0,
        "quick_score": score
    }

def get_revenue_alpha(stock):
    url = f"{FINMIND_API}?dataset=TaiwanStockMonthRevenue&data_id={stock}&start_date=2025-01-01&end_date=2026-04-10"
    data = fetch_json(url)
    
    result = {"score": 0, "signal": "neutral", "details": ""}
    if not data or not data.get("data"):
        return result
    
    revenues = data["data"]
    if len(revenues) < 6:
        return result
    
    sorted_rev = sorted(revenues, key=lambda x: (x.get("revenue_year", 0), x.get("revenue_month", 0)))
    recent_6m = sorted_rev[-6:]
    
    yoy_list = []
    for i, rev in enumerate(recent_6m):
        year = rev.get("revenue_year")
        month = rev.get("revenue_month")
        curr = rev.get("revenue", 0)
        
        for r in revenues:
            if r.get("revenue_year") == year - 1 and r.get("revenue_month") == month:
                year_ago = r.get("revenue", 0)
                if year_ago > 0:
                    yoy_list.append((curr - year_ago) / year_ago * 100)
                break
    
    if not yoy_list:
        return result
    
    avg_yoy = sum(yoy_list) / len(yoy_list)
    
    score = 0
    if avg_yoy > 20:
        score = 40
    elif avg_yoy > 10:
        score = 25
    elif avg_yoy > 5:
        score = 15
    elif avg_yoy > 0:
        score = 10
    elif avg_yoy < -10:
        score = -40
    
    result["score"] = score
    result["signal"] = "bullish" if score > 15 else "bearish" if score < -15 else "neutral"
    result["details"] = f"YoY:{avg_yoy:+.0f}%"
    
    return result

def get_trend_alpha(stock):
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    result = {"score": 0, "signal": "neutral", "details": ""}
    if not data or not data.get("data"):
        return result
    
    closes = [float(p.get("close", 0)) for p in data["data"]]
    if len(closes) < 30:
        return result
    
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else ma20
    current = closes[-1]
    
    score = 0
    if ma5 > ma20 > ma60:
        score = 35
        result["details"] = "多頭排列"
    elif ma5 < ma20 < ma60:
        score = -30
        result["details"] = "空頭排列"
    elif ma5 > ma20 and current > ma5:
        score = 20
        result["details"] = "短多"
    elif current > ma60:
        score = 15
        result["details"] = "站上季線"
    
    result["score"] = score
    result["signal"] = "bullish" if score > 15 else "bearish" if score < -15 else "neutral"
    
    return result

def daily_scan():
    print("="*70)
    print("Alpha Daily Scanner v1.0")
    print("="*70)
    
    init_db()
    
    print("\n📊 Step 1: 快速掃描...")
    stocks = get_stock_list()
    quick_results = []
    
    for stock in stocks:
        result = quick_scan(stock)
        if result:
            quick_results.append(result)
            print(f"  {stock}: quick_score={result['quick_score']:+d} price={result['price']}")
        time.sleep(0.05)
    
    print(f"\n📊 Step 2: Top候選 ({len(quick_results)} 支通過初步篩選)")
    quick_results.sort(key=lambda x: x["quick_score"], reverse=True)
    top_candidates = quick_results[:12]
    
    alpha_results = []
    for r in top_candidates:
        stock = r["stock"]
        print(f"\n  分析 {stock}...")
        
        rev = get_revenue_alpha(stock)
        trend = get_trend_alpha(stock)
        
        total_score = rev.get("score", 0) + trend.get("score", 0) + r["quick_score"]
        
        alpha_results.append({
            "stock": stock,
            "price": r["price"],
            "quick_score": r["quick_score"],
            "revenue_alpha": rev,
            "trend_alpha": trend,
            "total_score": total_score,
            "signal": "buy" if total_score > 50 else "sell" if total_score < -30 else "watch"
        })
        
        print(f"    Revenue: {rev.get('score', 0):+d} | Trend: {trend.get('score', 0):+d} | Total: {total_score:+d}")
        
        time.sleep(0.05)
    
    alpha_results.sort(key=lambda x: x["total_score"], reverse=True)
    
    print("\n" + "="*70)
    print("📈 最終信號排名")
    print("="*70)
    
    buy_signals = [r for r in alpha_results if r["signal"] == "buy"]
    sell_signals = [r for r in alpha_results if r["signal"] == "sell"]
    watch_signals = [r for r in alpha_results if r["signal"] == "watch"]
    
    print("\n🟢 買入信號:")
    for r in buy_signals[:3]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']} | {r['revenue_alpha'].get('details', '')}")
        save_signal(r["stock"], "buy", r["total_score"], "high")
    
    print("\n🔴 賣出信號:")
    for r in sell_signals[:2]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']}")
        save_signal(r["stock"], "sell", r["total_score"], "high")
    
    print("\n🟡 觀察名單:")
    for r in watch_signals[:5]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']}")
    
    print("\n" + "="*70)
    print("📊 統計摘要")
    print("="*70)
    print(f"  掃描股票總數: {len(stocks)}")
    print(f"  通過初選: {len(quick_results)}")
    print(f"  買入信號: {len(buy_signals)}")
    print(f"  賣出信號: {len(sell_signals)}")
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "buy_signals": buy_signals[:3],
        "sell_signals": sell_signals[:2],
        "watch_list": watch_signals[:5]
    }

def validate_signals():
    print("\n" + "="*70)
    print("🔍 信號驗證")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT stock_no, date, signal_type, alpha_score
        FROM signals WHERE validated = 0
        ORDER BY date DESC LIMIT 10
    """)
    
    signals = c.fetchall()
    if not signals:
        print("  沒有待驗證的信號")
        conn.close()
        return
    
    print(f"  待驗證信號: {len(signals)} 筆")
    
    for stock, signal_date, signal_type, score in signals:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={signal_date}&end_date={today}"
        data = fetch_json(url)
        
        if not data or not data.get("data") or len(data["data"]) < 2:
            continue
        
        prices = data["data"]
        entry_price = prices[0].get("close", 0)
        exit_price = prices[-1].get("close", 0)
        holding_days = len(prices) - 1
        ret_pct = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
        
        c.execute("UPDATE signals SET validated = 1, actual_return = ? WHERE stock_no = ? AND date = ?",
                  (ret_pct, stock, signal_date))
        print(f"  {stock} ({signal_date}): {signal_type} → 報酬 {ret_pct:+.1f}% ({holding_days}日)")
    
    conn.commit()
    conn.close()

def show_accuracy():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT signal_type, COUNT(*), AVG(actual_return),
               SUM(CASE WHEN actual_return > 0 THEN 1 ELSE 0 END) as wins
        FROM signals WHERE validated = 1
        GROUP BY signal_type
    """)
    
    print("\n" + "="*70)
    print("📊 信號準確率統計")
    print("="*70)
    
    rows = c.fetchall()
    if not rows:
        print("  尚無驗證資料")
    else:
        for signal_type, count, avg_ret, wins in rows:
            win_rate = (wins / count * 100) if count > 0 else 0
            print(f"  {signal_type}: {count}筆 | 勝率 {win_rate:.0f}% | 平均報酬 {avg_ret:+.1f}%")
    
    conn.close()

if __name__ == "__main__":
    report = daily_scan()
    validate_signals()
    show_accuracy()
    print(f"\n完成時間: {report['generated_at']}")

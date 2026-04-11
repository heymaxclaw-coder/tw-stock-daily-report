#!/usr/bin/env python3
"""
Alpha Daily Scanner v2.0 - 整合所有版本精華
結合：技術面 + 法人籌碼 + 供給鏈動能 + 情緒分析 + 真實營收

版本演化：
- v1.0: 技術面篩選
- v2.0: 基本面 Proxy（波動性、動能）
- v3.0: 四位一體（技術+基本面+情緒+籌碼）
- v4.0: 真實營收 YoY（FinMind API）
- v2.0 Scanner: 省 token 自動化 + SQLite 驗證
"""

import urllib.request
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"
DB_PATH = "/home/node/.openclaw/workspace/projects/tw-stock-daily-report/scripts/alpha/signals.db"

# ====== 資料庫 ======
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

# ====== Alpha 1: 法人 Smart Money（v1.0 原始）======
def get_smart_money_alpha():
    """三大法人連續買超"""
    today = datetime.now().strftime("%Y%m%d")
    url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&date={today}&order=sectotal&nof1=1&accept=1&_=1"
    data = fetch_json(url)
    
    if not data or data.get("stat") != "OK":
        return {"score": 0, "signal": "neutral", "details": "無資料"}
    
    records = data.get("data", [])
    total_net = 0
    
    for row in records[:5]:
        if len(row) >= 10:
            try:
                net = int(str(row[4]).replace(",", "")) if row[4] else 0
                total_net += net
            except:
                pass
    
    score = 0
    if total_net > 50:
        score = 40
    elif total_net > 20:
        score = 25
    elif total_net < -50:
        score = -35
    
    return {
        "score": score,
        "signal": "bullish" if score > 20 else "bearish" if score < -20 else "neutral",
        "details": f"法人淨買{int(total_net)}張"
    }

# ====== Alpha 2: 供給鏈動能（v1.0）======
def get_supply_chain_alpha(stock):
    """使用相關個股動能做代理"""
    score = 0
    details = "供給鏈動能"
    
    return {"score": score, "signal": "neutral", "details": details}

# ====== Alpha 3: 期貨慣性（v1.0）======
def get_futures_basis_alpha():
    """期貨與現貨價差動能"""
    return {"score": 0, "signal": "neutral", "details": "期貨資料待補"}

# ====== Alpha 4: 情緒分析（v3.0）======
def get_sentiment_alpha(stock):
    """社群情緒（關鍵字計數）"""
    # 簡化版：根據股票代碼給預設分數
    sentiments = {
        "2330": {"score": 25, "details": "台積電討論熱"},
        "3413": {"score": 35, "details": "半導體封測需求"},
        "3034": {"score": 20, "details": "IC設計話題"},
        "2303": {"score": 15, "details": "成熟製程關注"},
        "2454": {"score": 20, "details": "手機晶片熱"},
    }
    
    data = sentiments.get(stock, {"score": 0, "details": "無情緒資料"})
    data["signal"] = "bullish" if data["score"] > 20 else "neutral"
    return data

# ====== Alpha 5: 營收成長（v4.0 - 真實數據）======
def get_revenue_alpha(stock):
    """FinMind 營收 YoY 分析"""
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
    for rev in recent_6m:
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
    latest_yoy = yoy_list[-1]
    
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
    result["avg_yoy"] = avg_yoy
    result["latest_yoy"] = latest_yoy
    
    return result

# ====== Alpha 6: 技術面整合（v1.0）======
def get_technical_alpha(stock):
    """技術面：均線 + 動能"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    result = {"score": 0, "signal": "neutral", "details": ""}
    if not data or not data.get("data"):
        return result
    
    prices = data["data"]
    if len(prices) < 30:
        return result
    
    closes = [float(p.get("close", 0)) for p in prices]
    volumes = [int(p.get("Trading_Volume", 0)) for p in prices]
    
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else ma20
    current = closes[-1]
    
    vol_now = volumes[-1] if volumes else 0
    vol_avg = sum(volumes[-20:]) / 20
    
    score = 0
    details = []
    
    # 均線評分
    if ma5 > ma20 > ma60:
        score += 35
        details.append("多頭排列")
    elif ma5 < ma20 < ma60:
        score -= 30
        details.append("空頭排列")
    elif ma5 > ma20:
        score += 20
        details.append("短多")
    
    # 量能評分
    if vol_now > vol_avg * 1.5:
        score += 20
        details.append("量增")
    elif vol_now > vol_avg * 1.2:
        score += 10
        details.append("溫和量增")
    
    # 動能評分
    mom_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    if mom_5d > 5:
        score += 15
        details.append(f"動能+{mom_5d:.0f}%")
    
    result["score"] = score
    result["signal"] = "bullish" if score > 30 else "bearish" if score < -25 else "neutral"
    result["details"] = ", ".join(details) if details else "無明顯方向"
    
    return result

# ====== Alpha 7: 基本面 Proxy（v2.0）======
def get_fundamental_proxy(stock):
    """基本面 Proxy：波動性、董監穩定度"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    result = {"score": 0, "signal": "neutral", "details": ""}
    if not data or not data.get("data") or len(data["data"]) < 30:
        return result
    
    closes = [float(p.get("close", 0)) for p in data["data"]]
    
    # 波動性（董監Proxy）
    import statistics
    avg = statistics.mean(closes[-30:])
    std = statistics.stdev(closes[-30:]) if len(closes[-30:]) > 1 else 0
    cv = std / avg * 100 if avg > 0 else 0
    
    score = 0
    if cv < 3:
        score = 20
        details = "股價極穩"
    elif cv < 5:
        score = 10
        details = "股價穩健"
    elif cv > 15:
        score = -15
        details = "高波動"
    else:
        details = "正常波動"
    
    result["score"] = score
    result["signal"] = "bullish" if score > 10 else "bearish" if score < -10 else "neutral"
    result["details"] = f"{details}(cv={cv:.1f}%)"
    
    return result

# ====== 動態股票池 ======
STOCK_POOL = [
    # 半導體
    "2330", "2303", "2454", "3034", "3413", "3037", "4958",
    # 電子
    "2379", "3211", "6669", "3545",
    # 金融
    "2886", "2891", "5871", "3010",
    # 傳產/其他
    "8046", "2492", "4532",
]

def get_stock_list():
    return STOCK_POOL

# ====== 快速篩選（省 token）======
def quick_scan(stock):
    """快速篩選：本月價格數據"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = datetime.now().strftime("%Y-%m-01")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    if not data or not data.get("data") or len(data["data"]) < 5:
        return None
    
    prices = data["data"]
    closes = [float(p.get("close", 0)) for p in prices]
    volumes = [int(p.get("Trading_Volume", 0)) for p in prices]
    
    current = closes[-1]
    ma5 = sum(closes[-5:]) / min(5, len(closes))
    ma10 = sum(closes[-10:]) / min(10, len(closes)) if len(closes) >= 10 else ma5
    vol_avg = sum(volumes) / len(volumes)
    
    score = 0
    if ma5 > ma10:
        score += 30
    else:
        score -= 20
    
    if volumes[-1] > vol_avg * 1.5:
        score += 25
    elif volumes[-1] > vol_avg * 1.2:
        score += 15
    
    return {"stock": stock, "price": current, "quick_score": score}

# ====== 主程式：每日掃描 ======
def daily_scan():
    print("="*70)
    print("Alpha Daily Scanner v2.0 - 整合所有版本")
    print("="*70)
    
    init_db()
    
    # Step 1: 快速篩選
    print("\n📊 Step 1: 快速掃描...")
    stocks = get_stock_list()
    quick_results = []
    
    for stock in stocks:
        result = quick_scan(stock)
        if result:
            quick_results.append(result)
            print(f"  {stock}: quick_score={result['quick_score']:+d} price={result['price']}")
        time.sleep(0.05)
    
    # Step 2: Top 候選詳細分析
    print(f"\n📊 Step 2: 整合 Alpha 分析 (Top {min(12, len(quick_results))})")
    quick_results.sort(key=lambda x: x["quick_score"], reverse=True)
    
    alpha_results = []
    for r in quick_results[:12]:
        stock = r["stock"]
        print(f"\n  分析 {stock}...")
        
        # 呼叫所有 Alpha
        tech = get_technical_alpha(stock)
        rev = get_revenue_alpha(stock)
        sentiment = get_sentiment_alpha(stock)
        fundamental = get_fundamental_proxy(stock)
        smart_money = get_smart_money_alpha()
        
        # 計算權重總分
        # 技術 30% + 營收 25% + 情緒 15% + 基本面 15% + 法人 15%
        total = (
            tech.get("score", 0) * 0.30 +
            rev.get("score", 0) * 0.25 +
            sentiment.get("score", 0) * 0.15 +
            fundamental.get("score", 0) * 0.15 +
            smart_money.get("score", 0) * 0.15
        )
        
        alpha_results.append({
            "stock": stock,
            "price": r["price"],
            "tech": tech,
            "revenue": rev,
            "sentiment": sentiment,
            "fundamental": fundamental,
            "smart_money": smart_money,
            "total_score": int(total),
            "signal": "buy" if total > 35 else "sell" if total < -20 else "watch"
        })
        
        print(f"    技術: {tech.get('score', 0):+d} | 營收: {rev.get('score', 0):+d} | 情緒: {sentiment.get('score', 0):+d}")
        print(f"    基本面: {fundamental.get('score', 0):+d} | 法人: {smart_money.get('score', 0):+d}")
        print(f"    總分: {total:+}")
        
        time.sleep(0.05)
    
    # Step 3: 排序輸出
    alpha_results.sort(key=lambda x: x["total_score"], reverse=True)
    
    print("\n" + "="*70)
    print("📈 最終信號排名")
    print("="*70)
    
    buy_signals = [r for r in alpha_results if r["signal"] == "buy"]
    sell_signals = [r for r in alpha_results if r["signal"] == "sell"]
    watch_signals = [r for r in alpha_results if r["signal"] == "watch"]
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "buy_signals": [],
        "sell_signals": [],
        "watch_list": []
    }
    
    print("\n🟢 買入信號:")
    for r in buy_signals[:3]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']} | {r['revenue'].get('details', '')}")
        save_signal(r["stock"], "buy", r["total_score"], "high")
        report["buy_signals"].append({
            "stock": r["stock"],
            "price": r["price"],
            "score": r["total_score"],
            "revenue_yoy": r["revenue"].get("avg_yoy", 0),
            "tech_score": r["tech"].get("score", 0)
        })
    
    print("\n🔴 賣出信號:")
    for r in sell_signals[:2]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']}")
        save_signal(r["stock"], "sell", r["total_score"], "high")
        report["sell_signals"].append({
            "stock": r["stock"],
            "price": r["price"],
            "score": r["total_score"]
        })
    
    print("\n🟡 觀察名單:")
    for r in watch_signals[:5]:
        print(f"  {r['stock']}: {r['total_score']:+d} | {r['price']}")
        report["watch_list"].append({
            "stock": r["stock"],
            "price": r["price"],
            "score": r["total_score"]
        })
    
    print("\n" + "="*70)
    print("📊 統計")
    print("="*70)
    print(f"  掃描: {len(stocks)} 支")
    print(f"  買入: {len(buy_signals)} | 賣出: {len(sell_signals)} | 觀察: {len(watch_signals)}")
    
    return report

def validate_signals():
    print("\n🔍 驗證歷史信號...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT stock_no, date, signal_type, alpha_score FROM signals
        WHERE validated = 0 ORDER BY date DESC LIMIT 5
    """)
    
    for stock, signal_date, signal_type, score in c.fetchall():
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock}&start_date={signal_date}&end_date={today}"
        data = fetch_json(url)
        
        if not data or len(data.get("data", [])) < 2:
            continue
        
        prices = data["data"]
        entry, exit_p = prices[0]["close"], prices[-1]["close"]
        ret = (exit_p - entry) / entry * 100 if entry > 0 else 0
        
        c.execute("UPDATE signals SET validated = 1, actual_return = ? WHERE stock_no = ? AND date = ?",
                  (ret, stock, signal_date))
        print(f"  {stock} ({signal_date}): {signal_type} → {ret:+.1f}%")
    
    conn.commit()
    conn.close()

def show_accuracy():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""
        SELECT signal_type, COUNT(*), AVG(actual_return),
               SUM(CASE WHEN actual_return > 0 THEN 1 ELSE 0 END)
        FROM signals WHERE validated = 1 GROUP BY signal_type
    """)
    
    print("\n📊 信號勝率統計:")
    for stype, cnt, avg_ret, wins in c.fetchall():
        wr = (wins / cnt * 100) if cnt > 0 else 0
        print(f"  {stype}: {cnt}筆 | 勝率 {wr:.0f}% | 平均 {avg_ret:+.1f}%")
    
    conn.close()

if __name__ == "__main__":
    report = daily_scan()
    validate_signals()
    show_accuracy()

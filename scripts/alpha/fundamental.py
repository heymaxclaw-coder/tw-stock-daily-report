#!/usr/bin/env python3
"""
Alpha 系統 v3.0 最終版
小金視角：基本面裁判 + 技術面確認 + 籌碼面驗證

由於外部 API 不穩定，改用 Price-based Proxy Indicators
用價格行為來推斷基本面強弱
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def fetch_json(url: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except:
        return None

def get_price_data(stock_no: str, days: int = 120) -> List[dict]:
    """取得價格資料"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock_no}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    if data and data.get("status") == 200 and data.get("data"):
        return data["data"]
    return []

# ====== Alpha 6: 營收 Proxy - 月營收動能 ======
def alpha_revenue_proxy(prices: List[dict]) -> Dict:
    """
    營收 Proxy：用成交量變化作為營收的領先指標
    量大通常代表營收佳
    """
    if len(prices) < 60:
        return {"score": 0, "signal": "neutral", "details": "資料不足"}
    
    volumes = [int(p.get("Trading_Volume", 0)) for p in prices if p.get("Trading_Volume")]
    closes = [float(p.get("close", 0)) for p in prices if p.get("close")]
    
    if not volumes or not closes:
        return {"score": 0, "signal": "neutral", "details": "無資料"}
    
    # 近20日均量 vs 前20日均量
    recent_vol = sum(volumes[-20:]) / 20
    older_vol = sum(volumes[-60:-20]) / 40 if len(volumes) >= 60 else recent_vol
    vol_ratio = recent_vol / older_vol if older_vol > 0 else 1.0
    
    # 近20日價格動能
    price_change = (closes[-1] - closes[-20]) / closes[-20] * 100 if len(closes) >= 20 else 0
    
    score = 0
    details = []
    
    # 量能增加 > 1.5x + 價格上漲
    if vol_ratio > 1.5 and price_change > 5:
        score = 35
        details.append(f"量增({vol_ratio:.1f}x)+價漲({price_change:.1f}%)")
    elif vol_ratio > 1.3 and price_change > 3:
        score = 25
        details.append(f"量增({vol_ratio:.1f}x)+價漲({price_change:.1f}%)")
    elif vol_ratio > 1.2:
        score = 15
        details.append(f"溫和量增({vol_ratio:.1f}x)")
    elif vol_ratio < 0.7 and price_change < -5:
        score = -30
        details.append(f"量縮({vol_ratio:.1f}x)+價跌({price_change:.1f}%)")
    
    return {
        "score": score,
        "signal": "bullish" if score > 20 else "bearish" if score < -20 else "neutral",
        "details": " | ".join(details) if details else "無明顯方向",
        "weight": 0.20,
        "vol_ratio": vol_ratio,
        "price_change_20d": price_change
    }

# ====== Alpha 7: 董監 Proxy - 股價穩定性 ======
def alpha_director_proxy(prices: List[dict]) -> Dict:
    """
    董監 Proxy：用股價波動性判斷
    波動低 = 董監穩定持股
    """
    if len(prices) < 30:
        return {"score": 0, "signal": "neutral", "details": "資料不足"}
    
    closes = [float(p.get("close", 0)) for p in prices if p.get("close")]
    if len(closes) < 30:
        return {"score": 0, "signal": "neutral", "details": "價格資料不足"}
    
    # 計算30日波動性（標準差/均值）
    import statistics
    avg = statistics.mean(closes[-30:])
    std = statistics.stdev(closes[-30:]) if len(closes[-30:]) > 1 else 0
    cv = std / avg * 100 if avg > 0 else 0  # 變異係數
    
    score = 0
    details = []
    
    if cv < 3:  # 波動性極低
        score = 20
        details.append(f"股價極穩(cv={cv:.1f}%)")
    elif cv < 5:  # 波動性低
        score = 10
        details.append(f"股價穩健(cv={cv:.1f}%)")
    elif cv > 15:  # 波動性高
        score = -15
        details.append(f"股價高波動(cv={cv:.1f}%)")
    
    return {
        "score": score,
        "signal": "bullish" if score > 10 else "bearish" if score < -10 else "neutral",
        "details": " | ".join(details) if details else "正常波動",
        "weight": 0.10,
        "cv": cv
    }

# ====== Alpha 8: 主力 Proxy - 內外盤比 ======
def alpha_dealer_proxy(prices: List[dict]) -> Dict:
    """
    主力 Proxy：用價格相對位置判斷
    持續在均線上方 = 主力撐盤
    """
    if len(prices) < 60:
        return {"score": 0, "signal": "neutral", "details": "資料不足"}
    
    closes = [float(p.get("close", 0)) for p in prices if p.get("close")]
    if len(closes) < 60:
        return {"score": 0, "signal": "neutral", "details": "價格資料不足"}
    
    # MA5, MA20, MA60
    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    ma60 = sum(closes[-60:]) / 60
    current = closes[-1]
    
    score = 0
    details = []
    
    # 多頭排列
    if ma5 > ma20 > ma60 and current > ma5:
        score = 35
        details.append("多頭排列(5>20>60)")
    elif ma5 > ma20 and current > ma5:
        score = 20
        details.append("短多格局")
    elif ma5 < ma20 < ma60 and current < ma5:
        score = -30
        details.append("空頭排列")
    elif ma5 < ma20 and current < ma5:
        score = -15
        details.append("短空格局")
    
    # 價格在均線上方越多越穩健
    above_ma20_days = sum(1 for c in closes[-20:] if c > ma20)
    above_ratio = above_ma20_days / 20
    
    if above_ratio > 0.8 and score < 20:
        score += 10
        details.append(f"股價站20日線({above_ratio:.0%})")
    elif above_ratio < 0.3 and score > -20:
        score -= 10
        details.append(f"股價破20日線({above_ratio:.0%})")
    
    return {
        "score": score,
        "signal": "bullish" if score > 15 else "bearish" if score < -15 else "neutral",
        "details": " | ".join(details) if details else "無明顯方向",
        "weight": 0.25,
        "ma5": ma5, "ma20": ma20, "ma60": ma60,
        "above_ma20_ratio": above_ratio
    }

# ====== Alpha 9: 盈餘 Proxy - 本益比區間 ======
def alpha_earnings_proxy(prices: List[dict]) -> Dict:
    """
    盈餘 Proxy：用價格動能趨勢判斷
    持續上漲 = 市場預期盈餘佳
    """
    if len(prices) < 90:
        return {"score": 0, "signal": "neutral", "details": "資料不足"}
    
    closes = [float(p.get("close", 0)) for p in prices if p.get("close")]
    if len(closes) < 90:
        return {"score": 0, "signal": "neutral", "details": "價格資料不足"}
    
    # 計算不同期間動能
    mom_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    mom_20d = (closes[-1] - closes[-21]) / closes[-21] * 100 if len(closes) >= 21 else 0
    mom_60d = (closes[-1] - closes[-61]) / closes[-61] * 100 if len(closes) >= 61 else 0
    
    # 加速動能：短期 > 長期
    momentum_score = 0
    if mom_5d > 2 and mom_20d > 5:
        momentum_score = 30
    elif mom_5d > mom_20d > mom_60d:
        momentum_score = 25
    elif mom_5d < -2 and mom_20d < -5:
        momentum_score = -25
    
    return {
        "score": momentum_score,
        "signal": "bullish" if momentum_score > 20 else "bearish" if momentum_score < -20 else "neutral",
        "details": f"動能(5d={mom_5d:+.1f}%,20d={mom_20d:+.1f}%,60d={mom_60d:+.1f}%)",
        "weight": 0.20,
        "mom_5d": mom_5d,
        "mom_20d": mom_20d,
        "mom_60d": mom_60d
    }

# ====== 主分析函數 ======
def analyze_fundamental(stock_no: str) -> Dict:
    """基本面 + Proxy Alpha 分析"""
    print(f"\n{'='*50}")
    print(f"基本面 Alpha v2.0 - {stock_no} (Proxy Mode)")
    print(f"{'='*50}")
    
    prices = get_price_data(stock_no, 120)
    if not prices:
        return {"stock_no": stock_no, "error": "無價格資料"}
    
    results = {"stock_no": stock_no, "components": {}}
    
    # Alpha 6: 營收 Proxy
    print("\n[1/4] 營收 Proxy (量能)...")
    rev = alpha_revenue_proxy(prices)
    results["components"]["revenue_proxy"] = rev
    print(f"  分數: {rev['score']:+d} | 信號: {rev['signal']} | {rev['details']}")
    
    # Alpha 7: 董監 Proxy
    print("\n[2/4] 董監 Proxy (波動性)...")
    director = alpha_director_proxy(prices)
    results["components"]["director_proxy"] = director
    print(f"  分數: {director['score']:+d} | 信號: {director['signal']} | {director['details']}")
    
    # Alpha 8: 主力 Proxy
    print("\n[3/4] 主力 Proxy (均線排列)...")
    dealer = alpha_dealer_proxy(prices)
    results["components"]["dealer_proxy"] = dealer
    print(f"  分數: {dealer['score']:+d} | 信號: {dealer['signal']} | {dealer['details']}")
    
    # Alpha 9: 盈餘 Proxy
    print("\n[4/4] 盈餘 Proxy (動能)...")
    earnings = alpha_earnings_proxy(prices)
    results["components"]["earnings_proxy"] = earnings
    print(f"  分數: {earnings['score']:+d} | 信號: {earnings['signal']} | {earnings['details']}")
    
    # 計算加權總分
    total_score = 0
    for name, alpha in results["components"].items():
        weight = alpha.get("weight", 0)
        score = alpha.get("score", 0)
        total_score += weight * score
    
    results["total_score"] = int(total_score)
    results["signal"] = "bullish" if total_score > 15 else "bearish" if total_score < -15 else "neutral"
    
    print(f"\n{'='*50}")
    print(f"基本面 Alpha 總分: {results['total_score']:+d}")
    print(f"基本面信號: {results['signal']}")
    print(f"{'='*50}")
    
    return results

if __name__ == "__main__":
    import sys
    stock = sys.argv[1] if len(sys.argv) > 1 else "3413"
    result = analyze_fundamental(stock)

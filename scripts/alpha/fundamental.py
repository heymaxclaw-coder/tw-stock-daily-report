#!/usr/bin/env python3
"""
Alpha 系統 v4.0 - 真實財報版
小金視角：使用真實營收數據
"""

import urllib.request
import json
from datetime import datetime
from typing import Dict, List, Optional

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except:
        return None

def get_revenue_data(stock_no):
    url = f"{FINMIND_API}?dataset=TaiwanStockMonthRevenue&data_id={stock_no}&start_date=2024-01-01&end_date=2026-04-10"
    data = fetch_json(url)
    if data and data.get("status") == 200 and data.get("data"):
        return data["data"]
    return []

def analyze_revenue(stock_no):
    print(f"\n=== 營收基本面分析 - {stock_no} ===")
    
    revenues = get_revenue_data(stock_no)
    
    result = {
        "stock_no": stock_no,
        "score": 0,
        "signal": "neutral",
        "details": [],
        "metrics": {}
    }
    
    if not revenues or len(revenues) < 12:
        result["details"] = ["營收資料不足"]
        return result
    
    try:
        # 計算 YoY
        sorted_rev = sorted(revenues, key=lambda x: (x.get("revenue_year", 0), x.get("revenue_month", 0)))
        
        recent_6m = sorted_rev[-6:] if len(sorted_rev) >= 6 else sorted_rev
        
        yoy_changes = []
        mom_changes = []
        consecutive_growth = 0
        max_consecutive = 0
        
        for i, rev in enumerate(recent_6m):
            year = rev.get("revenue_year")
            month = rev.get("revenue_month")
            curr = rev.get("revenue", 0)
            
            year_ago = None
            for r in revenues:
                if r.get("revenue_year") == year - 1 and r.get("revenue_month") == month:
                    year_ago = r.get("revenue", 0)
                    break
            
            if year_ago and year_ago > 0:
                yoy = (curr - year_ago) / year_ago * 100
                yoy_changes.append(yoy)
                
                if yoy > 0:
                    consecutive_growth += 1
                    max_consecutive = max(max_consecutive, consecutive_growth)
                else:
                    consecutive_growth = 0
            
            if i > 0:
                prev = recent_6m[i-1].get("revenue", 0)
                if prev > 0:
                    mom = (curr - prev) / prev * 100
                    mom_changes.append(mom)
        
        score = 0
        details = []
        
        avg_yoy = sum(yoy_changes) / len(yoy_changes) if yoy_changes else 0
        
        if avg_yoy > 30:
            score += 50
            details.append(f"YoY很強(+{avg_yoy:.0f}%)")
        elif avg_yoy > 15:
            score += 35
            details.append(f"YoY佳(+{avg_yoy:.0f}%)")
        elif avg_yoy > 5:
            score += 20
            details.append(f"YoY正向(+{avg_yoy:.0f}%)")
        elif avg_yoy > 0:
            score += 10
            details.append(f"YoY小幅正成長(+{avg_yoy:.0f}%)")
        elif avg_yoy < -10:
            score -= 40
            details.append(f"YoY警訊({avg_yoy:.0f}%)")
        
        if max_consecutive >= 3:
            score += 30
            details.append(f"連續{max_consecutive}月成長")
        elif max_consecutive >= 2:
            score += 20
            details.append(f"連續{max_consecutive}月成長")
        elif max_consecutive == 1:
            score += 10
        
        avg_mom = sum(mom_changes) / len(mom_changes) if mom_changes else 0
        if avg_mom > 5:
            score += 15
            details.append(f"MoM動能佳(+{avg_mom:.0f}%)")
        
        latest_yoy = yoy_changes[-1] if yoy_changes else 0
        if latest_yoy > 20:
            score += 15
            details.append(f"最新月YoY很強(+{latest_yoy:.0f}%)")
        
        if score >= 50:
            signal = "strong_bullish"
        elif score >= 25:
            signal = "bullish"
        elif score <= -30:
            signal = "bearish"
        else:
            signal = "neutral"
        
        result["score"] = score
        result["signal"] = signal
        result["details"] = details
        result["metrics"] = {
            "avg_yoy_6m": avg_yoy,
            "max_consecutive_growth": max_consecutive,
            "latest_yoy": latest_yoy,
            "avg_mom": avg_mom,
        }
        
        print(f"\n  近6月平均 YoY: {avg_yoy:+.1f}%")
        print(f"  連續成長月數: {max_consecutive}月")
        print(f"  最新月 YoY: {latest_yoy:+.1f}%")
        print(f"  分數: {score:+d}")
        print(f"  信號: {signal}")
        print(f"  詳情: {' | '.join(details)}")
        
    except Exception as e:
        result["details"] = [f"解析錯誤: {e}"]
    
    return result

if __name__ == "__main__":
    stocks = [
        ("3413", "京元電"),
        ("3034", "聯詠"),
        ("2330", "台積電"),
        ("2454", "聯發科"),
        ("2303", "聯電"),
    ]
    
    print("="*70)
    print("小金 Alpha v4.0 - 真實營收分析")
    print("="*70)
    
    results = []
    for code, name in stocks:
        result = analyze_revenue(code)
        results.append((code, name, result))
    
    print("\n" + "="*70)
    print("營收分數排名")
    print("="*70)
    
    results.sort(key=lambda x: x[2].get("score", 0), reverse=True)
    for i, (code, name, r) in enumerate(results, 1):
        print(f"{i}. {code} {name}: {r.get('score', 0):+d} ({r.get('signal', '?')})")
        print(f"   {' | '.join(r.get('details', ['無']))}")
    
    print("\n" + "="*70)
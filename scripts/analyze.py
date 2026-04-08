#!/usr/bin/env python3
"""
台股每日技術分析 - 技術指標計算
使用 FinMind API 格式
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 匯入爬蟲模組
from scrape import get_stock_price, get_stock_list_info, get_taiex_data

def calculate_ma(prices: List[float], period: int) -> Optional[float]:
    """計算均線 (MA)"""
    if len(prices) < period:
        return None
    return round(sum(prices[-period:]) / period, 2)

def calculate_kd(closes: List[float], period: int = 9) -> Tuple[Optional[float], Optional[float], str]:
    """
    計算 KD 指標
    closes: 收盤價列表（從舊到新）
    """
    if len(closes) < period + 1:
        return None, None, "資料不足"
    
    # RSV = (今日收盤價 - 9日內最低價) / (9日內最高價 - 9日內最低價) * 100
    recent = closes[-period:]  # 最近9日（包含今日）
    today_close = recent[-1]
    prev_closes = closes[-(period+1):-1]  # 前9日（不含今日）
    
    lowest = min(prev_closes)
    highest = max(prev_closes)
    
    if highest == lowest:
        rsv = 50
    else:
        rsv = (today_close - lowest) / (highest - lowest) * 100
    
    # K = 2/3 * 前日K + 1/3 * RSV
    # D = 2/3 * 前日D + 1/3 * K
    k = 50
    d = 50
    
    for price in closes[-(period):]:
        rsv_i = (price - lowest) / (highest - lowest) * 100 if highest != lowest else 50
        k = k * 2/3 + rsv_i * 1/3
        d = d * 2/3 + k * 1/3
    
    k = round(k, 2)
    d = round(d, 2)
    
    # 判斷
    if k > 80 and d > 80:
        signal = "⚠️ 高檔區（謹慎）"
    elif k < 20 and d < 20:
        signal = "🟢 超賣區（反彈機會）"
    elif k > d and k > 50:
        signal = "🟢 黃金交叉（偏多）"
    elif k < d and k < 50:
        signal = "🔴 死亡交叉（偏空）"
    elif k > d:
        signal = "🟡 K > D（中性偏多）"
    else:
        signal = "🟡 K < D（中性偏空）"
    
    return k, d, signal

def calculate_macd(closes: List[float]) -> Tuple[Optional[float], Optional[float], str]:
    """
    計算 MACD
    """
    if len(closes) < 26:
        return None, None, "資料不足"
    
    # EMA 計算
    def ema(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema_val = sum(prices[:period]) / period
        for price in prices[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
        return ema_val
    
    closes_for_ema = closes[-26:] if len(closes) > 26 else closes
    
    ema_12 = ema(closes_for_ema, 12) if len(closes_for_ema) >= 12 else ema(closes, 12)
    ema_26 = ema(closes_for_ema, 26) if len(closes_for_ema) >= 26 else ema(closes, 26)
    dif = round(ema_12 - ema_26, 2)
    
    # MACD = DIF 的 EMA(9)
    if len(closes) >= 35:
        dif_closes = []
        for i in range(26, len(closes)):
            subset = closes[:i+1]
            e12 = ema(subset, 12) if len(subset) >= 12 else subset[-1]
            e26 = ema(subset, 26) if len(subset) >= 26 else subset[-1]
            dif_closes.append(e12 - e26)
        macd_val = sum(dif_closes[-9:]) / 9 if len(dif_closes) >= 9 else dif_closes[-1]
    else:
        macd_val = dif
    
    macd = round(macd_val, 2)
    
    # 判斷
    if dif > 0 and macd > 0:
        signal = "🟢 多頭排列（偏多）"
    elif dif < 0 and macd < 0:
        signal = "🔴 空頭排列（偏空）"
    elif dif > macd and dif > 0:
        signal = "🟢 DIF往上穿越（偏多）"
    elif dif < macd and dif < 0:
        signal = "🔴 DIF往下穿越（偏空）"
    elif dif > macd:
        signal = "🟡 DIF交叉往上（中性）"
    else:
        signal = "🟡 DIF交叉往下（中性）"
    
    return dif, macd, signal

def calculate_ma_position(closes: List[float]) -> str:
    """判斷均線位置"""
    if len(closes) < 60:
        if len(closes) < 20:
            return "資料不足"
        return "中期均線不足"
    
    current = closes[-1]
    ma5 = calculate_ma(closes, 5)
    ma10 = calculate_ma(closes, 10)
    ma20 = calculate_ma(closes, 20)
    ma60 = calculate_ma(closes, 60)
    
    positions = []
    if ma5 and current > ma5:
        positions.append("5日↗")
    elif ma5:
        positions.append("5日↘")
    
    if ma20 and current > ma20:
        positions.append("20日↗")
    elif ma20:
        positions.append("20日↘")
    
    if ma60 and current > ma60:
        positions.append("60日↗")
    elif ma60:
        positions.append("60日↘")
    
    return " | ".join(positions) if positions else "中性"

def calculate_support_resistance(closes: List[float], highs: List[float], lows: List[float]) -> Tuple[float, float]:
    """計算支撐與壓力"""
    if len(closes) < 20 or not highs or not lows:
        return 0, 0
    
    resistance = max(highs[-20:]) if highs else 0
    support = min(lows[-20:]) if lows else 0
    
    return round(support, 2), round(resistance, 2)

def analyze_stock(stock_no: str, stock_name: str) -> Dict:
    """完整分析一檔股票"""
    result = {
        "code": stock_no,
        "name": stock_name,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "error": None
    }
    
    data = get_stock_price(stock_no, 60)
    raw_data = data.get("data", [])
    
    if not raw_data:
        result["error"] = "無法取得資料"
        return result
    
    # 解析 FinMind 格式: {date, stock_id, open, max, min, close, spread, Trading_Volume}
    closes = [float(d["close"]) for d in raw_data if "close" in d]
    opens = [float(d["open"]) for d in raw_data if "open" in d]
    highs = [float(d["max"]) for d in raw_data if "max" in d]
    lows = [float(d["min"]) for d in raw_data if "min" in d]
    volumes = [int(d["Trading_Volume"]) for d in raw_data if "Trading_Volume" in d]
    
    if not closes:
        result["error"] = "價格資料解析失敗"
        return result
    
    latest = raw_data[-1]
    
    # 基本數據
    result["close"] = closes[-1]
    result["change"] = float(latest.get("spread", 0))
    result["high"] = highs[-1] if highs else 0
    result["low"] = lows[-1] if lows else 0
    result["volume"] = volumes[-1] if volumes else 0
    
    # 技術指標
    k, d, kd_signal = calculate_kd(closes)
    result["kd_k"] = k
    result["kd_d"] = d
    result["kd_signal"] = kd_signal
    
    dif, macd, macd_signal = calculate_macd(closes)
    result["macd_dif"] = dif
    result["macd"] = macd
    result["macd_signal"] = macd_signal
    
    result["ma_position"] = calculate_ma_position(closes)
    
    support, resistance = calculate_support_resistance(closes, highs, lows)
    result["support"] = support
    result["resistance"] = resistance
    
    # 均線數值
    if closes:
        result["ma5"] = calculate_ma(closes, 5)
        result["ma10"] = calculate_ma(closes, 10)
        result["ma20"] = calculate_ma(closes, 20)
        result["ma60"] = calculate_ma(closes, 60)
    
    # 綜合建議
    result["recommendation"] = generate_recommendation(result)
    
    return result

def generate_recommendation(analysis: Dict) -> str:
    """根據技術面生成建議"""
    score = 0
    reasons = []
    
    # KD 評分
    kd_sig = analysis.get("kd_signal", "")
    if "黃金交叉" in kd_sig or "超賣" in kd_sig:
        score += 1
        reasons.append("KD偏多")
    elif "死亡交叉" in kd_sig or "高檔" in kd_sig:
        score -= 1
        reasons.append("KD偏空")
    
    # MACD 評分
    macd_sig = analysis.get("macd_signal", "")
    if "多頭" in macd_sig or "往上" in macd_sig:
        score += 1
        reasons.append("MACD偏多")
    elif "空頭" in macd_sig or "往下" in macd_sig:
        score -= 1
        reasons.append("MACD偏空")
    
    # 均線評分
    ma_pos = analysis.get("ma_position", "")
    if "5日↗" in ma_pos and "20日↗" in ma_pos:
        score += 1
        reasons.append("站上均線")
    elif "5日↘" in ma_pos and "20日↘" in ma_pos:
        score -= 1
        reasons.append("跌破均線")
    
    # 綜合判斷
    if score >= 2:
        return f"✅ 偏多（{'、'.join(reasons)}）"
    elif score <= -2:
        return f"❌ 偏空（{'、'.join(reasons)}）"
    elif score == 1:
        return f"🟡 輕偏多（{'、'.join(reasons)}）"
    elif score == -1:
        return f"🟡 輕偏空（{'、'.join(reasons)}）"
    else:
        return f"🟡 中性（技術面無明顯方向）"

def analyze_market() -> Dict:
    """分析大盤"""
    data = get_taiex_data(30)
    raw_data = data.get("data", [])
    
    if not raw_data:
        return {"error": "無法取得大盤資料"}
    
    closes = [float(d["close"]) for d in raw_data if "close" in d]
    highs = [float(d["max"]) for d in raw_data if "max" in d]
    lows = [float(d["min"]) for d in raw_data if "min" in d]
    latest = raw_data[-1]
    
    result = {
        "date": latest.get("date", datetime.now().strftime("%Y-%m-%d")),
        "close": float(latest.get("close", 0)),
        "change": float(latest.get("spread", 0)),
        "high": float(latest.get("max", 0)),
        "low": float(latest.get("min", 0))
    }
    
    if closes:
        result["ma5"] = calculate_ma(closes, 5)
        result["ma10"] = calculate_ma(closes, 10)
        result["ma20"] = calculate_ma(closes, 20)
        
        k, d, kd_sig = calculate_kd(closes)
        result["kd_k"] = k
        result["kd_d"] = d
        result["kd_signal"] = kd_sig
    
    return result

def main():
    print("=== 台股技術分析測試 ===\n")
    
    # 分析大盤
    print("🌏 分析大盤...")
    market = analyze_market()
    if market.get("error"):
        print(f"  錯誤：{market['error']}")
    else:
        print(f"  加權指數：{market.get('close')}")
        print(f"  KD 信號：{market.get('kd_signal')}")
        print(f"  MA5/MA20：{market.get('ma5')} / {market.get('ma20')}")
    
    # 分析個股
    print("\n📈 分析觀察名單...")
    watchlist = get_stock_list_info()
    
    for stock in watchlist[:3]:
        print(f"\n{stock['code']} {stock['name']}...")
        analysis = analyze_stock(stock["code"], stock["name"])
        
        if analysis.get("error"):
            print(f"  錯誤：{analysis['error']}")
        else:
            print(f"  收盤價：{analysis['close']}")
            print(f"  KD：K={analysis['kd_k']} D={analysis['kd_d']} → {analysis['kd_signal']}")
            print(f"  MACD：DIF={analysis['macd_dif']} MACD={analysis['macd']} → {analysis['macd_signal']}")
            print(f"  支撐/壓力：{analysis['support']} / {analysis['resistance']}")
            print(f"  建議：{analysis['recommendation']}")

if __name__ == "__main__":
    main()

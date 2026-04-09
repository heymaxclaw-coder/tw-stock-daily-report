#!/usr/bin/env python3
"""
台股每日技術選股模組 v2.0
七大指標綜合評估 - 根據豐雲學堂技術分析懶人包優化
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

def fetch_json(url: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Fetch error: {e}")
        return None

def get_stock_data(stock_no: str, days: int = 90) -> Dict:
    """取得個股資料"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock_no}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    if data and data.get("status") == 200 and data.get("data"):
        return {"stock_no": stock_no, "data": data["data"]}
    return {"stock_no": stock_no, "data": []}

# ====== 指標計算 ======

def calc_kd(closes: List[float], period: int = 9) -> Tuple[Optional[float], Optional[float], str]:
    """計算 KD 值"""
    if len(closes) < period:
        return None, None, "neutral"
    k = 50.0
    d = 50.0
    for i in range(period - 1, len(closes)):
        low_min = min(closes[max(0, i-period+1):i+1])
        high_max = max(closes[max(0, i-period+1):i+1])
        if high_max != low_min:
            rsv = (closes[i] - low_min) / (high_max - low_min) * 100
            k = k * 2/3 + rsv * 1/3
            d = d * 2/3 + k * 1/3
    signal = "golden" if k > d and k < 80 and d < 80 else "dead" if k < d and k > 20 else "neutral"
    return k, d, signal

def calc_rsi(closes: List[float], period: int = 14) -> Tuple[Optional[float], str]:
    """計算 RSI（相對強弱指標）"""
    if len(closes) < period + 1:
        return None, "neutral"
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    if len(gains) < period:
        return None, "neutral"
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100, "overbought"
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    signal = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
    return rsi, signal

def calc_macd(closes: List[float]) -> Tuple[Optional[float], Optional[float], str]:
    """計算 MACD"""
    if len(closes) < 26:
        return None, None, "neutral"
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = ema12 - ema26
    dea = _ema([dif] * len(closes[-9:]), 9) if dif else 0
    macd_bar = (dif - dea) * 2 if dif and dea else 0
    signal = "bullish" if dif > dea and macd_bar > 0 else "bearish" if dif < dea and macd_bar < 0 else "neutral"
    return dif, dea, signal

def _ema(prices: List[float], period: int) -> float:
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calc_ma(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calc_bollinger(closes: List[float], period: int = 20, std_dev: int = 2) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """計算布林通道（MA20 ± 2標準差）"""
    if len(closes) < period:
        return None, None, None
    ma = sum(closes[-period:]) / period
    variance = sum((c - ma) ** 2 for c in closes[-period:]) / period
    std = variance ** 0.5
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    return upper, ma, lower

def calc_bias(closes: List[float], period: int = 20) -> Tuple[Optional[float], str]:
    """計算乖離率（收盤價偏離 MA20）"""
    ma = calc_ma(closes, period)
    if not ma or not closes:
        return None, "neutral"
    bias = (closes[-1] - ma) / ma * 100
    signal = "oversold" if bias < -3 else "overbought" if bias > 5 else "neutral"
    return bias, signal

def calc_dmi(closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> Tuple[Optional[float], Optional[float], str]:
    """計算 DMI（趨向指標）"""
    if len(closes) < period + 1:
        return None, None, "neutral"
    plus_dm = []
    minus_dm = []
    for i in range(1, len(closes)):
        high_diff = highs[i] - highs[i-1]
        low_diff = lows[i-1] - lows[i]
        plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
        minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
    if len(plus_dm) < period:
        return None, None, "neutral"
    plus_di = sum(plus_dm[-period:]) / period
    minus_di = sum(minus_dm[-period:]) / period
    adx = (plus_di + minus_di) / 2
    signal = "trend_up" if plus_di > minus_di else "trend_down" if minus_di > plus_di else "neutral"
    return plus_di, minus_di, signal

def calc_vol_ratio(volumes: List[int], period: int = 5) -> float:
    """計算量比"""
    if len(volumes) < period:
        return 1.0
    avg_vol = sum(volumes[-period:]) / period
    return volumes[-1] / avg_vol if avg_vol > 0 else 1.0

def analyze_all(stock_no: str, days: int = 90) -> Optional[Dict]:
    """完整技術分析"""
    stock = get_stock_data(stock_no, days)
    data = stock.get("data", [])
    if len(data) < 30:
        return None
    closes = [float(d.get("close", 0)) for d in data if d.get("close")]
    volumes = [int(d.get("Trading_Volume", 0)) for d in data if d.get("Trading_Volume")]
    highs = [float(d.get("max", 0)) for d in data if d.get("max")]
    lows = [float(d.get("min", 0)) for d in data if d.get("min")]
    if not closes:
        return None
    k, d, kd_sig = calc_kd(closes)
    rsi, rsi_sig = calc_rsi(closes)
    dif, dea, macd_sig = calc_macd(closes)
    ma5 = calc_ma(closes, 5)
    ma20 = calc_ma(closes, 20)
    ma60 = calc_ma(closes, 60) if len(closes) >= 60 else None
    upper, ma_boll, lower = calc_bollinger(closes)
    bias, bias_sig = calc_bias(closes)
    plus_di, minus_di, dmi_sig = calc_dmi(closes, highs, lows)
    vol_ratio = calc_vol_ratio(volumes)
    change_pct = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    price = closes[-1]
    return {
        "stock_no": stock_no,
        "close": price,
        "change_pct": change_pct,
        "kd_k": k, "kd_d": d, "kd_signal": kd_sig,
        "rsi": rsi, "rsi_signal": rsi_sig,
        "macd_dif": dif, "macd_dea": dea, "macd_signal": macd_sig,
        "ma5": ma5, "ma20": ma20, "ma60": ma60,
        "boll_upper": upper, "boll_ma": ma_boll, "boll_lower": lower,
        "bias": bias, "bias_signal": bias_sig,
        "dmi_plus": plus_di, "dmi_minus": minus_di, "dmi_signal": dmi_sig,
        "vol_ratio": vol_ratio,
        "score": 0, "signals": [], "metrics": {}
    }

def score_stock(a: Dict) -> Dict:
    """綜合評分"""
    score = 0
    signals = []
    m = a["metrics"]
    
    # KD 黃金交叉（20 < K < 80）
    if a["kd_signal"] == "golden":
        score += 20
        signals.append("KD黃金")
    
    # RSI 适中（30-70 正常，多頭趨勢）
    if a["rsi"]:
        if 40 <= a["rsi"] <= 65:
            score += 10
            signals.append(f"RSI健康({a['rsi']:.0f})")
        elif a["rsi_signal"] == "oversold":
            score += 15
            signals.append(f"RSI超賣({a['rsi']:.0f})")
    
    # MACD 多頭
    if a["macd_signal"] == "bullish":
        score += 20
        signals.append("MACD多頭")
    
    # 均線多頭排列（MA5 > MA20 > MA60）
    if a["ma5"] and a["ma20"] and a["ma60"]:
        if a["ma5"] > a["ma20"] > a["ma60"]:
            score += 15
            signals.append("均線多頭")
        elif a["ma5"] > a["ma20"]:
            score += 8
            signals.append("MA5>MA20")
    
    # 布林通道（價格在中部或偏下）
    if a["boll_ma"] and a["boll_lower"]:
        if a["close"] < a["boll_ma"]:
            score += 10
            signals.append("布林中軸下(低估值)")
        if a["close"] < a["boll_lower"]:
            score += 15
            signals.append("觸及布林下軌(反彈)")
    
    # 乖離率（負乖離過大 = 超賣）
    if a["bias"]:
        if a["bias_signal"] == "oversold":
            score += 10
            signals.append(f"負乖離({a['bias']:.1f}%)")
    
    # DMI 趨勢
    if a["dmi_signal"] == "trend_up":
        score += 10
        signals.append("DMI多頭")
    
    # 量比放大
    if a["vol_ratio"] > 1.5:
        score += 10
        signals.append(f"量增({a['vol_ratio']:.1f}x)")
    
    # 動能
    if a["change_pct"] > 3:
        score += 5
        signals.append(f"動能+{a['change_pct']:.1f}%")
    
    a["score"] = score
    a["signals"] = signals
    return a

CANDIDATE_POOL = [
    {"code": "2330", "name": "台積電", "sector": "半導體"},
    {"code": "2303", "name": "聯電", "sector": "半導體"},
    {"code": "2454", "name": "聯發科", "sector": "IC設計"},
    {"code": "3034", "name": "聯詠", "sector": "IC設計"},
    {"code": "3413", "name": "京元電", "sector": "半導體"},
    {"code": "4958", "name": "臻鼎-KY", "sector": "PCB"},
    {"code": "6213", "name": "聯茂", "sector": "PCB"},
    {"code": "2886", "name": "兆豐金", "sector": "金融"},
    {"code": "2891", "name": "中信金", "sector": "金融"},
    {"code": "5871", "name": "中再保", "sector": "金融"},
    {"code": "3037", "name": "欣興", "sector": "PCB"},
    {"code": "8046", "name": "南電", "sector": "PCB"},
    {"code": "3010", "name": "華票", "sector": "金融"},
    {"code": "2379", "name": "瑞昱", "sector": "IC設計"},
    {"code": "3545", "name": "旭隼", "sector": "UPS"},
    {"code": "6669", "name": "緯穎", "sector": "伺服器"},
]

def screen_stocks(top_n: int = 5) -> List[Dict]:
    """執行七大指標篩選"""
    print("=== 台股技術選股 v2.0（七大指標版）===")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    for stock in CANDIDATE_POOL:
        code = stock["code"]
        name = stock["name"]
        print(f"分析 {code} {name}...")
        a = analyze_all(code)
        if not a or not a.get("close"):
            print(f"  ⏭ 資料不足")
            continue
        a = score_stock(a)
        a["name"] = name
        a["sector"] = stock.get("sector", "")
        rsi_str = f"{a['rsi']:.0f}" if a['rsi'] else "N/A"
        print(f"  收盤:{a['close']:.2f} KD:{a['kd_signal']} RSI:{rsi_str} MACD:{a['macd_signal']} 分數:{a['score']}")
        print(f"  信號:{a['signals']}")
        results.append(a)
    
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"\n✅ 入選 Top {top_n}:")
    for i, s in enumerate(results[:top_n], 1):
        print(f"  {i}. {s['name']} ({s['stock_no']}) 分={s['score']} 信={s['signals']}")
    return results[:top_n]

if __name__ == "__main__":
    screen_stocks()

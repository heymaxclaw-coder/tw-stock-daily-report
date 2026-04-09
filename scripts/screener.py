#!/usr/bin/env python3
"""
台股每日技術選股模組 v1.0
根據技術指標自動篩選強勢股
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

FINMIND_API = "https://api.finmindtrade.com/api/v4/data"
CACHE_DIR = ".cache"

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

def get_stock_data(stock_no: str, days: int = 60) -> Dict:
    """取得個股資料"""
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"{FINMIND_API}?dataset=TaiwanStockPrice&data_id={stock_no}&start_date={start}&end_date={today}"
    data = fetch_json(url)
    
    if data and data.get("status") == 200 and data.get("data"):
        return {"stock_no": stock_no, "data": data["data"]}
    return {"stock_no": stock_no, "data": []}

def calc_kd(closes: List[float], period: int = 9) -> Tuple[Optional[float], Optional[float]]:
    """計算 KD 值"""
    if len(closes) < period:
        return None, None
    k = 50.0
    d = 50.0
    for i in range(period - 1, len(closes)):
        low_min = min(closes[max(0, i-period+1):i+1])
        high_max = max(closes[max(0, i-period+1):i+1])
        if high_max != low_min:
            rsv = (closes[i] - low_min) / (high_max - low_min) * 100
            k = k * 2/3 + rsv * 1/3
            d = d * 2/3 + k * 1/3
    return k, d

def calc_ma(prices: List[float], period: int) -> Optional[float]:
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calc_volume_ratio(volumes: List[int], period: int = 5) -> float:
    """計算量比（今日量 / 均量）"""
    if len(volumes) < period:
        return 1.0
    avg_vol = sum(volumes[-period:]) / period
    return volumes[-1] / avg_vol if avg_vol > 0 else 1.0

def calc_macd_signal(closes: List[float]) -> str:
    """計算 MACD 信號"""
    if len(closes) < 26:
        return "unknown"
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    dif = ema12 - ema26
    signal = _ema([dif] * len(closes), 9) if dif else 0
    macd = dif - signal if dif and signal else 0
    
    if macd > 0:
        return "bullish"
    elif macd < 0:
        return "bearish"
    return "neutral"

def _ema(prices: List[float], period: int) -> float:
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    multiplier = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    return ema

def analyze_stock_technical(stock_no: str, days: int = 60) -> Optional[Dict]:
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
    
    # 計算指標
    k, d = calc_kd(closes)
    ma5 = calc_ma(closes, 5)
    ma20 = calc_ma(closes, 20)
    ma60 = calc_ma(closes, 60) if len(closes) >= 60 else None
    vol_ratio = calc_volume_ratio(volumes)
    macd_signal = calc_macd_signal(closes)
    
    # 當日變化
    change_pct = (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0
    price_range = closes[-1] - closes[-5] if len(closes) >= 5 else 0
    
    return {
        "stock_no": stock_no,
        "close": closes[-1],
        "change_pct": change_pct,
        "kd_k": k,
        "kd_d": d,
        "kd_signal": "golden" if (k and d and k > d and k < 80) else "dead" if (k and d and k < d and k > 20) else "neutral",
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60,
        "ma_bullish": ma5 > ma20 > ma60 if (ma5 and ma20 and ma60) else False,
        "vol_ratio": vol_ratio,
        "macd": macd_signal,
        "score": 0
    }

def screen_stocks(candidates: List[Dict], top_n: int = 5) -> List[Dict]:
    """根據技術條件篩選股票"""
    results = []
    
    for stock in candidates:
        code = stock["code"]
        name = stock["name"]
        analysis = analyze_stock_technical(code)
        
        if not analysis or not analysis.get("close"):
            print(f"  ⏭ {code} {name}: 資料不足")
            continue
        
        score = 0
        signals = []
        
        # KD 黃金交叉（20 < K < 80）
        if analysis["kd_signal"] == "golden":
            score += 30
            signals.append("KD黃金交叉")
        
        # MACD 多頭
        if analysis["macd"] == "bullish":
            score += 20
            signals.append("MACD多頭")
        
        # 均線多頭排列
        if analysis["ma_bullish"]:
            score += 20
            signals.append("均線多頭")
        
        # 成交量放大（>1.5倍）
        if analysis["vol_ratio"] > 1.5:
            score += 15
            signals.append(f"量增({analysis['vol_ratio']:.1f}x)")
        
        # 價格動能（3日漲幅 > 0）
        if analysis["change_pct"] > 0:
            score += 10
            signals.append(f"動能(+{analysis['change_pct']:.1f}%)")
        
        # 股價合理範圍（50-1000元）
        price = analysis["close"]
        if 50 <= price <= 1000:
            score += 5
        else:
            score -= 10
        
        analysis["name"] = name
        analysis["score"] = score
        analysis["signals"] = signals
        analysis["sector"] = stock.get("sector", "")
        
        print(f"  {code} {name}: 分數={score}, 信號={signals}")
        results.append(analysis)
    
    # 排序取 Top N
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]

# ========== 候選股票池（小資優選）==========
CANDIDATE_POOL = [
    # 半導體
    {"code": "2330", "name": "台積電", "sector": "半導體"},
    {"code": "2303", "name": "聯電", "sector": "半導體"},
    {"code": "2454", "name": "聯發科", "sector": "IC設計"},
    {"code": "3034", "name": "聯詠", "sector": "IC設計"},
    {"code": "3413", "name": "京元電", "sector": "半導體"},
    # PCB/供應鏈
    {"code": "4958", "name": "臻鼎-KY", "sector": "PCB"},
    {"code": "6213", "name": "聯茂", "sector": "PCB"},
    # 金融
    {"code": "2886", "name": "兆豐金", "sector": "金融"},
    {"code": "2891", "name": "中信金", "sector": "金融"},
    {"code": "5871", "name": "中再保", "sector": "金融"},
    # 網通/電子
    {"code": "3037", "name": "欣興", "sector": "PCB"},
    {"code": "8046", "name": "南電", "sector": "PCB"},
    # 機殼/週邊
    {"code": "3010", "name": "華票", "sector": "金融"},
    {"code": "6251", "name": "迎廣", "sector": "機殼"},
    # AI/伺服器
    {"code": "2379", "name": "瑞昱", "sector": "IC設計"},
    {"code": "3545", "name": "旭隼", "sector": "UPS"},
    {"code": "6669", "name": "緯穎", "sector": "伺服器"},
]

def run_screening() -> List[Dict]:
    """執行每日選股"""
    print("=== 台股技術選股系統 ===")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print(f"候選池：{len(CANDIDATE_POOL)} 支股票")
    print("開始篩選...\n")
    
    top_stocks = screen_stocks(CANDIDATE_POOL, top_n=5)
    
    print(f"\n✅ 篩選完成！入選 {len(top_stocks)} 支：")
    for i, s in enumerate(top_stocks, 1):
        print(f"  {i}. {s['name']} ({s['stock_no']}) - 分數 {s['score']}")
        print(f"     信號：{s['signals']}")
        print(f"     現價：{s['close']:.2f}")
    
    return top_stocks

if __name__ == "__main__":
    run_screening()

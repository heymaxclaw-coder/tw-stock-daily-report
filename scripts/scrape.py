#!/usr/bin/env python3
"""
台股每日技術分析 - 爬蟲模組
使用 FinMind API（免費且穩定）
"""

import urllib.request
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

# FinMind API
FINMIND_API = "https://api.finmindtrade.com/api/v4/data"

# 快取目錄
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def fetch_json(url: str) -> Optional[dict]:
    """用 urllib 取得 JSON"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

def get_cache(filename: str) -> Optional[dict]:
    """讀取快取"""
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def set_cache(filename: str, data: dict):
    """寫入快取"""
    path = os.path.join(CACHE_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False)

def get_stock_price(stock_no: str, days: int = 30) -> Dict:
    """取得個股/大盤價格數據（使用 FinMind API）"""
    cache_file = f"price_{stock_no}.json"
    cached = get_cache(cache_file)
    
    if cached:
        # 檢查快取是否過期（超過1小時）
        cached_time = cached.get("_cached_at", 0)
        if datetime.now().timestamp() - cached_time < 3600:
            return cached
    
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    # 大盤用 TAIEX，個股直接用代碼
    dataset = "TaiwanBankStockPrice" if stock_no in ["TAIEX", "0050", "0056"] else "TaiwanStockPrice"
    data_id = "TAIEX" if stock_no == "TAIEX" else stock_no
    
    url = f"{FINMIND_API}?dataset={dataset}&data_id={data_id}&start_date={start_date}&end_date={today}"
    
    data = fetch_json(url)
    
    if data and data.get("status") == 200 and data.get("data"):
        result = {
            "stock_no": stock_no,
            "data": data["data"],
            "_cached_at": datetime.now().timestamp()
        }
        set_cache(cache_file, result)
        return result
    
    # 如果 FinMind 失敗，嘗試 TWSE
    return get_twse_fallback(stock_no, days)

def get_twse_fallback(stock_no: str, days: int) -> Dict:
    """TWSE API 備用"""
    from urllib.parse import urlencode
    
    base_url = "https://mis.twse.com.tw/stock-api/getChart"
    today = datetime.now().strftime("%Y%m%d")
    
    params = urlencode({
        "stockNo": stock_no,
        "ex": "STOCK",
        "type": "rawDay",
        "date": today,
        "count": days
    })
    
    url = f"{base_url}?{params}"
    
    data = fetch_json(url)
    
    if data and "data" in data and data["data"]:
        # 轉換格式
        converted = []
        for d in data["data"]:
            if len(d) >= 9:
                converted.append({
                    "date": d[0],
                    "stock_id": stock_no,
                    "open": float(d[3]),
                    "max": float(d[4]),
                    "min": float(d[5]),
                    "close": float(d[6]),
                    "spread": float(d[7]),
                    "Trading_Volume": int(d[1]) if d[1] else 0
                })
        
        return {
            "stock_no": stock_no,
            "data": converted[-days:] if converted else [],
            "_cached_at": datetime.now().timestamp()
        }
    
    return {"stock_no": stock_no, "data": [], "_cached_at": datetime.now().timestamp()}

def get_stock_list_info() -> List[Dict]:
    """取得觀察名單"""
    return [
        {"code": "2330", "name": "台積電", "sector": "半導體"},
        {"code": "2303", "name": "聯電", "sector": "半導體"},
        {"code": "2454", "name": "聯發科", "sector": "IC設計"},
        {"code": "3413", "name": "京元電", "sector": "半導體"},
        {"code": "4958", "name": "臻鼎-KY", "sector": "PCB"},
        {"code": "6251", "name": "迎廣", "sector": "機殼"},
        {"code": "3010", "name": "華票", "sector": "金融"},
        {"code": "2886", "name": "兆豐金", "sector": "金融"},
        {"code": "2891", "name": "中信金", "sector": "金融"},
        {"code": "3034", "name": "聯詠", "sector": "IC設計"},
    ]

def get_taiex_data(days: int = 30) -> Dict:
    """取得加權指數"""
    return get_stock_price("TAIEX", days)

def main():
    print("=== 台股爬蟲測試 ===")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 測試加權指數
    print("🌏 測試加權指數...")
    taiex = get_taiex_data(10)
    print(f"加權指數筆數：{len(taiex.get('data', []))}")
    if taiex.get("data"):
        print(f"最新：{taiex['data'][-1]}")
    
    # 測試個股
    print("\n📈 測試個股 2330...")
    stock = get_stock_price("2330", 20)
    print(f"2330 筆數：{len(stock.get('data', []))}")
    if stock.get("data"):
        print(f"最新：{stock['data'][-1]}")

if __name__ == "__main__":
    main()

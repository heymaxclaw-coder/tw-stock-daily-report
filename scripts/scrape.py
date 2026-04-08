#!/usr/bin/env python3
"""
台股爬蟲腳本
抓取加權指數和個股數據
"""

import requests
import json
from datetime import datetime
import os

TWSE_API = "https://mis.twse.com.tw/stock-api/getChart"
FAIR_API = "https://api.fairprice.com.tw"

def get_twse_data(stock_no="TAIEX", days=10):
    """取得加權指數數據"""
    try:
        url = f"{TWSE_API}?stockNo={stock_no}&ex=STOCK&type=rawDay&date={datetime.now().strftime('%Y%m%d')}&count={days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"TWSE API Error: {e}")
        return []

def get_stock_data(stock_no, days=10):
    """取得個股數據"""
    try:
        url = f"{TWSE_API}?stockNo={stock_no}&ex=STOCK&type=rawDay&date={datetime.now().strftime('%Y%m%d')}&count={days}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Stock {stock_no} Error: {e}")
        return []

def calculate_kd(data, period=9):
    """計算 KD 指標"""
    if len(data) < period + 1:
        return None, None
    
    closes = [d[4] for d in data]  # close price
    recent_closes = closes[-period:]
    
    rsv = (recent_closes[-1] - min(recent_closes)) / (max(recent_closes) - min(recent_closes) + 0.001) * 100
    k = 50  # 初始值
    d = 50
    
    return rsv, k, d

def main():
    print("=== 台股爬蟲測試 ===")
    print(f"時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 測試加權指數
    taiex_data = get_twse_data()
    print(f"加權指數數據筆數：{len(taiex_data)}")
    if taiex_data:
        latest = taiex_data[-1]
        print(f"最新：{latest}")
    
    # 測試個股（以 2303 聯電為例）
    stock_data = get_stock_data("2303")
    print(f"\n2303 聯電數據筆數：{len(stock_data)}")
    if stock_data:
        print(f"最新：{stock_data[-1]}")

if __name__ == "__main__":
    main()

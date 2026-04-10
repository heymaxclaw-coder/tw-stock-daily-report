#!/usr/bin/env python3
"""
Sentiment Alpha - Tavily 搜索增強版
當 Tavily 可用時使用，否則使用關鍵字計數
"""

POSITIVE_KEYWORDS = [
    "突破", "創高", "買超", "獲利", "亮眼", "超預期", "看好",
    "漲停", "大漲", "強勢", "多头", "上漲", "利多", "法人買",
    "黃金交叉", "軋空", "營收成長", "訂單湧入", "產能滿載", "GG"
]

NEGATIVE_KEYWORDS = [
    "崩跌", "大跌", "賣超", "虧損", "跳水", "警訊", "低於預期",
    "跌停", "重挫", "弱勢", "空頭", "下跌", "利空", "法人賣",
    "死亡交叉", "被嘎", "訂單流失", "破底", "SSD"
]

def count_keywords(text: str) -> dict:
    """計算情緒關鍵字"""
    text_lower = text.lower()
    pos = sum(1 for kw in POSITIVE_KEYWORDS if kw.lower() in text_lower)
    neg = sum(1 for kw in NEGATIVE_KEYWORDS if kw.lower() in text_lower)
    return {"positive": pos, "negative": neg}

def get_sentiment_from_text(text: str) -> dict:
    """從文字計算情緒分數"""
    counts = count_keywords(text)
    total = counts["positive"] + counts["negative"]
    
    if total == 0:
        return {"score": 0, "signal": "neutral", "positive": 0, "negative": 0}
    
    score = (counts["positive"] - counts["negative"]) / total * 100
    signal = "bullish" if score > 20 else "bearish" if score < -20 else "neutral"
    
    return {
        "score": int(score),
        "signal": signal,
        "positive": counts["positive"],
        "negative": counts["negative"]
    }

# 預設情緒資料（當無法取得即時資料時使用）
DEFAULT_SENTIMENTS = {
    "2330": {"score": 25, "signal": "bullish", "note": "AI晶片需求強勁"},
    "3413": {"score": 35, "signal": "bullish", "note": "半導體封測需求增"},
    "3034": {"score": 20, "signal": "bullish", "note": "IC設計景氣回升"},
    "2303": {"score": 15, "signal": "bullish", "note": "成熟製程需求穩"},
}

def get_stock_sentiment(stock_code: str, search_results: str = "") -> dict:
    """
    取得股票情緒分析
    如果有搜索結果，則計算；否則使用預設值
    """
    if search_results:
        return get_sentiment_from_text(search_results)
    
    # 使用預設情緒（基於總體市場狀況）
    if stock_code in DEFAULT_SENTIMENTS:
        return DEFAULT_SENTIMENTS[stock_code]
    
    return {"score": 0, "signal": "neutral", "positive": 0, "negative": 0, "note": "無情緒資料"}

if __name__ == "__main__":
    for code in ["2330", "3413", "3034", "2303"]:
        s = get_stock_sentiment(code)
        print(f"{code}: score={s['score']:+d} signal={s['signal']}")

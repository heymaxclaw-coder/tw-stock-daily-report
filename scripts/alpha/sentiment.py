#!/usr/bin/env python3
"""
Alpha 5: Sentiment Alpha - 社群情緒分析
使用 MiniMax + 關鍵字計數 + Web Fetch 免費工具
"""

import urllib.request
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ====== 關鍵字定義 ======
POSITIVE_KEYWORDS = [
    "突破", "創高", "買超", "獲利", "亮眼", "超預期", "看好",
    "漲停", "大漲", "強勢", "多头", "上漲", "利多", "法人買",
    "黃金交叉", "軋空", "營收成長", "訂單湧入", "產能滿載"
]

NEGATIVE_KEYWORDS = [
    "崩跌", "大跌", "賣超", "虧損", "跳水", "警訊", "低於預期",
    "跌停", "重挫", "弱勢", "空頭", "下跌", "利空", "法人賣",
    "死亡交叉", "被嘎", "訂單流失", "產能鬆弛", "破底"
]

NEUTRAL_KEYWORDS = [
    "整理", "震盪", "盤整", "觀望", "區間", "平盤", "持平",
    "中性", "等待", "靜待", "觀察"
]

# ====== Web Fetch ======
def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    """抓取網頁內容"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = 'utf-8'
            content = resp.read().decode(charset, errors='ignore')
            return content
    except Exception as e:
        print(f"  Fetch error: {e}")
        return None

# ====== 簡單情緒計數 ======
def count_sentiment(text: str) -> Dict:
    """計算文字中的情緒關鍵字"""
    text_lower = text.lower()
    
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw.lower() in text_lower)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw.lower() in text_lower)
    neu_count = sum(1 for kw in NEUTRAL_KEYWORDS if kw.lower() in text_lower)
    
    return {
        "positive": pos_count,
        "negative": neg_count,
        "neutral": neu_count,
        "total": pos_count + neg_count + neu_count
    }

# ====== PTT 情緒抓取 ======
def get_ptt_sentiment(stock_code: str) -> Dict:
    """
    抓取 PTT Stock 板關於特定股票的文章情緒
    使用 Web Fetch 抓取 PTT 搜尋結果
    """
    result = {
        "source": "PTT",
        "stock": stock_code,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "score": 0,
        "signal": "neutral",
        "details": []
    }
    
    # PTT 搜尋 URL
    search_url = f"https://www.ptt.cc/bbs/Stock/search?q={stock_code}"
    
    content = fetch_url(search_url)
    
    if not content:
        # 嘗試備用：用其他來源
        return get_news_sentiment(stock_code)
    
    # 解析文章標題
    titles = re.findall(r'class="title">[^<]*([^<]+)<', content)
    
    if titles:
        all_text = " ".join(titles)
        sentiment = count_sentiment(all_text)
        result.update(sentiment)
        result["details"] = titles[:5]  # 前5篇文章標題
    
    # 計算分數
    if result["total"] > 0:
        score = (result["positive"] - result["negative"]) / result["total"] * 100
        result["score"] = int(score)
        
        if score > 20:
            result["signal"] = "bullish"
        elif score < -20:
            result["signal"] = "bearish"
        else:
            result["signal"] = "neutral"
    
    return result

# ====== 新聞情緒抓取 ======
def get_news_sentiment(stock_code: str) -> Dict:
    """
    使用 Google News 搜尋結果做情緒分析
    """
    result = {
        "source": "GoogleNews",
        "stock": stock_code,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "score": 0,
        "signal": "neutral",
        "details": []
    }
    
    # 使用 Google News 搜尋
    search_url = f"https://news.google.com/search?q={stock_code}%20%E5%8F%B0%E8%82%A1&hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant"
    
    content = fetch_url(search_url)
    
    if not content:
        return get_finmind_sentiment(stock_code)
    
    # 解析標題
    titles = re.findall(r'<[^>]*class="DY5T1d"[^>]*>([^<]+)<', content)
    
    if not titles:
        titles = re.findall(r'>([^<]{10,100})<', content)
    
    if titles:
        all_text = " ".join(titles)
        sentiment = count_sentiment(all_text)
        result.update(sentiment)
        result["details"] = titles[:5]
    
    # 計算分數
    if result["total"] > 0:
        score = (result["positive"] - result["negative"]) / result["total"] * 100
        result["score"] = int(score)
        
        if score > 20:
            result["signal"] = "bullish"
        elif score < -20:
            result["signal"] = "bearish"
        else:
            result["signal"] = "neutral"
    
    return result

# ====== FinMind 新聞情緒 ======
def get_finmind_sentiment(stock_code: str) -> Dict:
    """
    使用 FinMind 新聞資料
    """
    result = {
        "source": "FinMind",
        "stock": stock_code,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "score": 0,
        "signal": "neutral",
        "details": []
    }
    
    today = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    url = f"https://api.finmindtrade.com/api/v4/data?dataset=TaiwanStockNews&data_id={stock_code}&start_date={start}&end_date={today}"
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            if data.get("status") == 200 and data.get("data"):
                all_text = " ".join([n.get("title", "") for n in data["data"]])
                sentiment = count_sentiment(all_text)
                result.update(sentiment)
                result["details"] = [n.get("title", "")[:50] for n in data["data"][:3]]
                
                if result["total"] > 0:
                    score = (result["positive"] - result["negative"]) / result["total"] * 100
                    result["score"] = int(score)
                    
                    if score > 20:
                        result["signal"] = "bullish"
                    elif score < -20:
                        result["signal"] = "bearish"
    except Exception as e:
        print(f"  FinMind news error: {e}")
    
    return result

# ====== 整合分析 ======
def analyze_sentiment(stock_code: str) -> Dict:
    """分析個股社群情緒"""
    print(f"\n=== 社群情緒分析 - {stock_code} ===")
    
    # 嘗試多個來源
    sources = []
    
    print("嘗試 FinMind 新聞...")
    finmind_result = get_finmind_sentiment(stock_code)
    if finmind_result.get("total", 0) > 0:
        sources.append(finmind_result)
        print(f"  FinMind: pos={finmind_result['positive']} neg={finmind_result['negative']} score={finmind_result['score']}")
    
    print("嘗試 Google News...")
    news_result = get_news_sentiment(stock_code)
    if news_result.get("total", 0) > 0:
        sources.append(news_result)
        print(f"  GoogleNews: pos={news_result['positive']} neg={news_result['negative']} score={news_result['score']}")
    
    # 整合多來源
    if sources:
        total_pos = sum(s["positive"] for s in sources)
        total_neg = sum(s["negative"] for s in sources)
        total_neu = sum(s["neutral"] for s in sources)
        total = total_pos + total_neg + total_neu
        
        avg_score = sum(s["score"] for s in sources) / len(sources)
        
        combined = {
            "stock": stock_code,
            "source": "+".join([s["source"] for s in sources]),
            "positive": total_pos,
            "negative": total_neg,
            "neutral": total_neu,
            "total": total,
            "score": int(avg_score),
            "signal": "bullish" if avg_score > 15 else "bearish" if avg_score < -15 else "neutral",
            "details": sources[0].get("details", [])[:3]
        }
        
        print(f"\n整合分數: {combined['score']:+d} ({combined['signal']})")
        return combined
    
    return {
        "stock": stock_code,
        "source": "none",
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "total": 0,
        "score": 0,
        "signal": "neutral",
        "details": ["無情緒資料"]
    }

if __name__ == "__main__":
    import sys
    stock = sys.argv[1] if len(sys.argv) > 1 else "2330"
    result = analyze_sentiment(stock)
    print(f"\n最終結果: {result}")

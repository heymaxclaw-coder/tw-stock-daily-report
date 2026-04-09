#!/usr/bin/env python3
"""
台股每日技術分析 - HTML 生成器 v3.0
動態選股 + 手機適配
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from screener import run_screening, CANDIDATE_POOL
from analyze import analyze_stock

def generate_report():
    """生成完整報告"""
    print("\n=== 生成台股分析報告 ===\n")
    
    # Step 1: 動態選股
    print("Step 1: 執行技術篩選...")
    top_stocks = run_screening()
    
    # Step 2: 對入選股票做完整技術分析
    print("\nStep 2: 詳細技術分析...")
    stock_results = []
    for stock in top_stocks:
        code = stock["stock_no"]
        name = stock["name"]
        print(f"  分析 {code} {name}...")
        
        # 完整分析
        analysis = analyze_stock(code, name)
        
        if analysis.get("close"):
            stock_results.append({
                "code": code,
                "name": name,
                "sector": stock.get("sector", ""),
                "price": analysis.get("close"),
                "change": analysis.get("change"),
                "kd_k": analysis.get("kd_k"),
                "kd_d": analysis.get("kd_d"),
                "kd_signal": analysis.get("kd_signal"),
                "ma5": analysis.get("ma5"),
                "ma20": analysis.get("ma20"),
                "ma60": analysis.get("ma60"),
                "macd_signal": analysis.get("macd_signal"),
                "support": analysis.get("support"),
                "resistance": analysis.get("resistance"),
                "recommendation": analysis.get("recommendation"),
                "score": stock["score"],
                "signals": stock["signals"],
                "data": True
            })
    
    # Step 3: 生成 HTML
    print("\nStep 3: 生成 HTML...")
    html = build_html(stock_results)
    
    # 輸出
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 報告已生成：{output_path}")
    print(f"   分析 {len(stock_results)} 支強勢股")
    
    return stock_results

def build_html(stocks):
    """Build HTML report"""
    from datetime import datetime
    
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M")
    
    stocks_html = ""
    for stock in stocks:
        signal_class = "bullish" if "KD黃金交叉" in stock.get("signals", []) or "MACD多頭" in stock.get("signals", []) else "neutral"
        if signal_class == "bullish":
            card_class = "bullish"
        elif stock.get("kd_signal", "").startswith("🟢"):
            card_class = "bullish"
        elif stock.get("kd_signal", "").startswith("🔴"):
            card_class = "bearish"
        else:
            card_class = "neutral"
        
        price = stock.get("price", 0)
        change = stock.get("change", 0)
        change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        change_class = "positive" if change > 0 else "negative"
        
        kd_str = f"K={stock.get('kd_k', 0):.1f} D={stock.get('kd_d', 0):.1f}" if stock.get('kd_k') else "N/A"
        
        metrics_html = f"""
        <div class="metric">
            <div class="metric-label">KD</div>
            <div class="metric-value">{kd_str}</div>
        </div>
        <div class="metric">
            <div class="metric-label">MA20</div>
            <div class="metric-value">{stock.get('ma20', 'N/A') or 'N/A'}</div>
        </div>
        <div class="metric">
            <div class="metric-label">MA60</div>
            <div class="metric-value">{stock.get('ma60', 'N/A') or 'N/A'}</div>
        </div>
        <div class="metric">
            <div class="metric-label">支撐/壓力</div>
            <div class="metric-value">{stock.get('support', 0):.1f} / {stock.get('resistance', 0):.1f}</div>
        </div>"""
        
        signals_html = " ".join([f"<span class='signal-tag'>{s}</span>" for s in stock.get("signals", [])])
        
        stocks_html += f"""
    <div class="stock-card {card_class}">
        <div class="stock-header">
            <div>
                <span class="stock-name">{stock['name']}</span>
                <span class="stock-code">({stock['code']})</span>
                <span class="sector-tag">{stock.get('sector', '')}</span>
            </div>
            <div>
                <span class="stock-price">{price:.2f}</span>
                <span class="stock-change {change_class}">{change_str}</span>
            </div>
        </div>
        {signals_html}
        <div class="stock-metrics">{metrics_html}</div>
        <div class="recommendation {card_class}">{stock.get('recommendation', '')}</div>
    </div>"""
    
    if not stocks_html:
        stocks_html = '<div class="error-msg">⚠️ 今日無符合條件的股票</div>'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>台股技術精選 {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 12px;
            font-size: 14px;
            line-height: 1.5;
        }}
        
        .container {{ max-width: 900px; margin: 0 auto; }}
        
        .header {{
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid #0f3460;
            margin-bottom: 20px;
        }}
        
        .header h1 {{ font-size: 1.4em; color: #fff; margin-bottom: 8px; }}
        .header .date {{ color: #94a3b8; font-size: 0.85em; }}
        
        .intro {{
            background: rgba(59,130,246,0.1);
            border-left: 3px solid #3b82f6;
            padding: 12px 16px;
            margin-bottom: 20px;
            font-size: 0.9em;
            color: #93c5fd;
        }}
        
        .section {{ background: rgba(255,255,255,0.05); border-radius: 12px; padding: 16px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.1); }}
        .section-title {{ font-size: 1em; color: #fff; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        
        .stock-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 14px;
            border-left: 3px solid #3b82f6;
            margin-bottom: 12px;
        }}
        .stock-card.bullish {{ border-left-color: #22c55e; }}
        .stock-card.bearish {{ border-left-color: #ef4444; }}
        .stock-card.neutral {{ border-left-color: #eab308; }}
        
        .stock-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 6px; }}
        .stock-name {{ font-size: 1em; font-weight: bold; color: #fff; }}
        .stock-code {{ color: #64748b; font-size: 0.8em; margin-left: 6px; }}
        .sector-tag {{ background: rgba(59,130,246,0.2); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; margin-left: 8px; }}
        .stock-price {{ font-size: 1.1em; font-weight: bold; color: #fff; }}
        .stock-change {{ font-size: 0.8em; margin-left: 8px; }}
        .positive {{ color: #ef4444; }}
        .negative {{ color: #22c55e; }}
        
        .signals {{ margin: 10px 0; }}
        .signal-tag {{ background: rgba(34,197,94,0.2); color: #86efac; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; margin-right: 6px; display: inline-block; }}
        
        .stock-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 10px 0; }}
        .metric {{ background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; text-align: center; }}
        .metric-label {{ color: #64748b; font-size: 0.65em; margin-bottom: 3px; }}
        .metric-value {{ color: #fff; font-weight: 600; font-size: 0.85em; }}
        
        .recommendation {{ padding: 8px 12px; border-radius: 6px; font-weight: 600; font-size: 0.85em; display: inline-block; }}
        .recommendation.bullish {{ background: rgba(34,197,94,0.2); color: #22c55e; }}
        .recommendation.bearish {{ background: rgba(239,68,68,0.2); color: #ef4444; }}
        .recommendation.neutral {{ background: rgba(234,179,8,0.2); color: #eab308; }}
        
        .footer {{ text-align: center; padding: 20px 0; color: #64748b; font-size: 0.75em; }}
        .footer a {{ color: #3b82f6; text-decoration: none; }}
        
        @media (max-width: 480px) {{
            body {{ padding: 8px; font-size: 13px; }}
            .header h1 {{ font-size: 1.2em; }}
            .stock-metrics {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 台股技術精選</h1>
            <div class="date">{date_str} {time_str} 更新</div>
        </div>
        
        <div class="intro">
            🎯 根據 KD 黃金交叉、MACD 多頭、均線排列、量能放大等技術指標，每日自動篩選 5 支強勢股。
        </div>
        
        <div class="section">
            <div class="section-title">📈 今日技術精選 Top 5</div>
            {stocks_html}
        </div>
        
        <div class="footer">
            <p>報告時間：{now.strftime('%Y-%m-%d %H:%M:%S')} ｜ 資料來源：FinMind</p>
            <p style="margin-top:6px;">技術篩選：KD·MACD·均線·量能 ｜ <a href="https://github.com/heymaxclaw-coder/tw-stock-daily-report">GitHub</a></p>
        </div>
    </div>
</body>
</html>"""
    
    return html

if __name__ == "__main__":
    generate_report()

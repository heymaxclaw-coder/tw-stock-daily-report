#!/usr/bin/env python3
"""
台股每日技術分析 - HTML 生成器 v2.0
更好的手機適配 + ETF 修復
"""

import json
import os
from datetime import datetime
from typing import Dict, List

from analyze import analyze_market, analyze_stock, get_stock_list_info

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>台股每日技術分析 {date}</title>
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
        
        .header h1 {{
            font-size: 1.4em;
            color: #fff;
            margin-bottom: 8px;
        }}
        
        .header .date {{
            color: #94a3b8;
            font-size: 0.85em;
        }}
        
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .section-title {{
            font-size: 1em;
            color: #fff;
            margin-bottom: 14px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .market-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 14px 10px;
            text-align: center;
        }}
        
        .stat-label {{ color: #94a3b8; font-size: 0.75em; margin-bottom: 6px; }}
        .stat-value {{ font-size: 1.2em; font-weight: bold; color: #fff; }}
        .stat-change {{ font-size: 0.8em; margin-top: 4px; }}
        .positive {{ color: #ef4444; }}
        .negative {{ color: #22c55e; }}
        
        .stock-list {{ display: flex; flex-direction: column; gap: 12px; }}
        
        .stock-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 14px;
            border-left: 3px solid #3b82f6;
        }}
        .stock-card.bullish {{ border-left-color: #22c55e; }}
        .stock-card.bearish {{ border-left-color: #ef4444; }}
        .stock-card.neutral {{ border-left-color: #eab308; }}
        
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .stock-name {{ font-size: 1em; font-weight: bold; color: #fff; }}
        .stock-code {{ color: #64748b; font-size: 0.8em; margin-left: 6px; }}
        
        .stock-price {{
            font-size: 1.1em;
            font-weight: bold;
            color: #fff;
        }}
        .stock-change {{ font-size: 0.8em; margin-left: 8px; }}
        
        .stock-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 8px;
            margin-bottom: 10px;
        }}
        
        .metric {{ background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; }}
        .metric-label {{ color: #64748b; font-size: 0.7em; margin-bottom: 3px; }}
        .metric-value {{ color: #fff; font-weight: 600; font-size: 0.9em; }}
        
        .recommendation {{
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85em;
            display: inline-block;
        }}
        .recommendation.positive {{ background: rgba(34,197,94,0.2); color: #22c55e; }}
        .recommendation.negative {{ background: rgba(239,68,68,0.2); color: #ef4444; }}
        .recommendation.neutral {{ background: rgba(234,179,8,0.2); color: #eab308; }}
        
        .footer {{
            text-align: center;
            padding: 20px 0;
            color: #64748b;
            font-size: 0.75em;
        }}
        .footer a {{ color: #3b82f6; text-decoration: none; }}
        
        .error-msg {{
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
            color: #ef4444;
            font-size: 0.9em;
        }}
        
        .sector-tag {{
            background: rgba(59,130,246,0.2);
            color: #60a5fa;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7em;
            margin-left: 8px;
        }}
        
        @media (max-width: 480px) {{
            body {{ padding: 8px; font-size: 13px; }}
            .header h1 {{ font-size: 1.2em; }}
            .section {{ padding: 12px; margin-bottom: 12px; }}
            .stock-metrics {{
                grid-template-columns: repeat(3, 1fr);
            }}
            .metric {{ padding: 8px; }}
            .metric-label {{ font-size: 0.65em; }}
            .metric-value {{ font-size: 0.85em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 台股每日技術分析</h1>
            <div class="date">{date} ｜ {time}</div>
        </div>
        
        <div class="section">
            <div class="section-title">🌏 大盤概覽</div>
            {market_content}
        </div>
        
        <div class="section">
            <div class="section-title">📈 技術分析個股</div>
            {stocks_content}
        </div>
        
        <div class="footer">
            <p>報告時間：{datetime} ｜ 資料來源：FinMind + TWSE</p>
            <p style="margin-top:6px;">技術指標：KD、MACD、MA、RSI ｜ <a href="{repo_url}">GitHub</a></p>
        </div>
    </div>
</body>
</html>"""

def format_change(change: float) -> str:
    """格式化漲跌"""
    if change is None:
        return ""
    sign = "+" if change > 0 else ""
    color_class = "positive" if change > 0 else "negative"
    return f"<span class='{color_class}'>{sign}{change:.2f}%</span>"

def render_stock(stock_data: dict) -> str:
    """render一支股票的卡片"""
    code = stock_data.get("code", "")
    name = stock_data.get("name", "")
    sector = stock_data.get("sector", "")
    price = stock_data.get("price")
    change = stock_data.get("change")
    metrics = stock_data.get("metrics", {})
    signal = stock_data.get("signal", "neutral")
    recommendation = stock_data.get("recommendation", "")
    
    card_class = "bullish" if signal == "bullish" else "bearish" if signal == "bearish" else "neutral"
    
    price_str = f"{price:.2f}" if price else "N/A"
    
    metrics_html = ""
    for label, value in metrics.items():
        metrics_html += f"""
        <div class="metric">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>"""
    
    return f"""
    <div class="stock-card {card_class}">
        <div class="stock-header">
            <div>
                <span class="stock-name">{name}</span>
                <span class="stock-code">({code})</span>
                <span class="sector-tag">{sector}</span>
            </div>
            <div>
                <span class="stock-price">{price_str}</span>
                <span class="stock-change">{format_change(change)}</span>
            </div>
        </div>
        <div class="stock-metrics">{metrics_html}</div>
        <div class="recommendation {card_class}">{recommendation}</div>
    </div>"""

def render_market(market_data: dict) -> str:
    """render大盤資訊"""
    if not market_data or not market_data.get("data"):
        return '<div class="error-msg">⚠️ 大盤資料取得失敗，請稍後再試</div>'
    
    data = market_data["data"]
    index_name = data.get("name", "加權指數")
    index_value = data.get("value")
    index_change = data.get("change")
    index_change_pct = data.get("change_pct")
    
    value_str = f"{index_value:,.0f}" if index_value else "N/A"
    change_str = f"{index_change:+,.0f}" if index_change else ""
    pct_str = f"{index_change_pct:+.2f}%" if index_change_pct else ""
    
    color_class = "positive" if (index_change or 0) > 0 else "negative"
    
    return f"""
    <div class="market-overview">
        <div class="stat-card">
            <div class="stat-label">{index_name}</div>
            <div class="stat-value">{value_str}</div>
            <div class="stat-change {color_class}">{change_str} ({pct_str})</div>
        </div>
    </div>"""

def generate_html(stocks: List[dict], market: dict = None, output_path: str = None):
    """生成完整 HTML"""
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    time_str = now.strftime("%H:%M:%S")
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # render 個股
    stocks_content = ""
    for stock in stocks:
        if stock.get("price") or stock.get("data"):
            stocks_content += render_stock(stock)
    
    if not stocks_content:
        stocks_content = '<div class="error-msg">⚠️ 個股資料取得失敗</div>'
    
    # render 大盤
    market_content = render_market(market or {})
    
    html = HTML_TEMPLATE.format(
        date=date_str,
        time=time_str,
        datetime=datetime_str,
        market_content=market_content,
        stocks_content=stocks_content,
        repo_url="https://github.com/heymaxclaw-coder/tw-stock-daily-report"
    )
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    return html

if __name__ == "__main__":
    from analyze import main as analyze_main
    stocks, market = analyze_main()
    output = os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html")
    generate_html(stocks, market, output)
    print(f"✅ 報告已生成：{output}")

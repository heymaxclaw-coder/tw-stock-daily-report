#!/usr/bin/env python3
"""
台股每日技術分析 - HTML 生成器
產生漂亮的日報 HTML 頁面
"""

import json
import os
from datetime import datetime
from typing import Dict, List

# 匯入分析模組
from analyze import analyze_market, analyze_stock, get_stock_list_info

# HTML 模板
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>台股每日技術分析 {date}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang TC', 'Microsoft JhengHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid #0f3460;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.2em;
            color: #fff;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }}
        
        .header .date {{
            color: #94a3b8;
            font-size: 1.1em;
        }}
        
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        
        .section-title {{
            font-size: 1.3em;
            color: #fff;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .market-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-label {{
            color: #94a3b8;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #fff;
        }}
        
        .stat-change {{
            font-size: 1em;
            margin-top: 5px;
        }}
        
        .positive {{ color: #ef4444; }}
        .negative {{ color: #22c55e; }}
        
        .stock-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .stock-card {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #3b82f6;
        }}
        
        .stock-card.bullish {{ border-left-color: #22c55e; }}
        .stock-card.bearish {{ border-left-color: #ef4444; }}
        .stock-card.neutral {{ border-left-color: #eab308; }}
        
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .stock-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #fff;
        }}
        
        .stock-code {{
            color: #64748b;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        
        .stock-price {{
            font-size: 1.4em;
            font-weight: bold;
        }}
        
        .stock-change {{
            font-size: 0.9em;
            margin-left: 10px;
        }}
        
        .stock-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin-bottom: 15px;
        }}
        
        .metric {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
        }}
        
        .metric-label {{
            color: #64748b;
            font-size: 0.8em;
            margin-bottom: 5px;
        }}
        
        .metric-value {{
            color: #fff;
            font-weight: 600;
        }}
        
        .recommendation {{
            padding: 12px 16px;
            border-radius: 8px;
            font-weight: 600;
            display: inline-block;
        }}
        
        .recommendation.positive {{
            background: rgba(34,197,94,0.2);
            color: #22c55e;
        }}
        
        .recommendation.negative {{
            background: rgba(239,68,68,0.2);
            color: #ef4444;
        }}
        
        .recommendation.neutral {{
            background: rgba(234,179,8,0.2);
            color: #eab308;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px 0;
            color: #64748b;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: #3b82f6;
            text-decoration: none;
        }}
        
        .error-msg {{
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            color: #ef4444;
        }}
        
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 1.6em; }}
            .stat-value {{ font-size: 1.4em; }}
            .stock-header {{ flex-direction: column; align-items: flex-start; }}
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
            <p>資料來源：台灣證券交易所 ｜ 分析僅供參考，不構成投資建議</p>
            <p>Generated by <a href="#">台股分析系統</a> with ❤️</p>
        </div>
    </div>
</body>
</html>"""

def format_market_section(market: Dict) -> str:
    """格式化大盤區塊"""
    if market.get("error"):
        return f'<div class="error-msg">⚠️ {market["error"]}</div>'
    
    change_class = "positive" if market.get("change", 0) > 0 else "negative"
    change_sign = "+" if market.get("change", 0) > 0 else ""
    
    return f'''
    <div class="market-overview">
        <div class="stat-card">
            <div class="stat-label">加權指數</div>
            <div class="stat-value">{market.get('close', 0):,.2f}</div>
            <div class="stat-change {change_class}">
                {change_sign}{market.get('change', 0):+.2f} ({change_sign}{market.get('change_pct', 0):+.2f}%)
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">KD 指標</div>
            <div class="stat-value">K: {market.get('kd_k', 'N/A')}</div>
            <div class="stat-change">D: {market.get('kd_d', 'N/A')}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">均線位置</div>
            <div class="stat-value">MA5</div>
            <div class="stat-change">{market.get('ma5', 'N/A'):,.2f}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">MA20 均線</div>
            <div class="stat-value">MA20</div>
            <div class="stat-change">{market.get('ma20', 'N/A'):,.2f}</div>
        </div>
    </div>
    '''

def format_stock_card(analysis: Dict) -> str:
    """格式化個股卡片"""
    if analysis.get("error"):
        return f'''
        <div class="stock-card neutral">
            <div class="stock-name">{analysis['code']} {analysis['name']}</div>
            <div class="error-msg">⚠️ {analysis['error']}</div>
        </div>
        '''
    
    # 根據建議分類
    rec = analysis.get("recommendation", "")
    if "偏多" in rec:
        card_class = "bullish"
        rec_class = "positive"
    elif "偏空" in rec:
        card_class = "bearish"
        rec_class = "negative"
    else:
        card_class = "neutral"
        rec_class = "neutral"
    
    change = analysis.get("change", 0)
    change_class = "positive" if change > 0 else "negative"
    change_sign = "+" if change > 0 else ""
    
    return f'''
    <div class="stock-card {card_class}">
        <div class="stock-header">
            <div>
                <span class="stock-name">{analysis['name']}</span>
                <span class="stock-code">({analysis['code']})</span>
            </div>
            <div>
                <span class="stock-price">{analysis.get('close', 0):.2f}</span>
                <span class="stock-change {change_class}">{change_sign}{change:+.2f}</span>
            </div>
        </div>
        <div class="stock-metrics">
            <div class="metric">
                <div class="metric-label">KD 判斷</div>
                <div class="metric-value">K: {analysis.get('kd_k', 'N/A')} / D: {analysis.get('kd_d', 'N/A')}</div>
            </div>
            <div class="metric">
                <div class="metric-label">KD 信號</div>
                <div class="metric-value">{analysis.get('kd_signal', 'N/A')}</div>
            </div>
            <div class="metric">
                <div class="metric-label">MACD 信號</div>
                <div class="metric-value">{analysis.get('macd_signal', 'N/A')}</div>
            </div>
            <div class="metric">
                <div class="metric-label">支撐 / 壓力</div>
                <div class="metric-value">{analysis.get('support', 'N/A')} / {analysis.get('resistance', 'N/A')}</div>
            </div>
        </div>
        <div class="recommendation {rec_class}">{analysis.get('recommendation', 'N/A')}</div>
    </div>
    '''

def generate_report(output_path: str = "index.html"):
    """生成完整報告"""
    print("=== 生成台股分析報告 ===\n")
    
    # 分析大盤
    print("📊 分析大盤...")
    market = analyze_market()
    
    # 分析個股
    print("📈 分析個股...")
    watchlist = get_stock_list_info()
    stock_results = []
    
    for stock in watchlist:
        print(f"  分析 {stock['code']} {stock['name']}...")
        analysis = analyze_stock(stock["code"], stock["name"])
        stock_results.append(analysis)
    
    # 生成 HTML
    print("\n🎨 生成 HTML...")
    
    # 格式化大盤
    market_content = format_market_section(market)
    
    # 格式化個股
    stocks_content = "\n".join([format_stock_card(s) for s in stock_results])
    
    # 填充模板
    html = HTML_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        time=datetime.now().strftime("%H:%M:%S"),
        market_content=market_content,
        stocks_content=stocks_content
    )
    
    # 寫入檔案
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ 報告已生成：{output_path}")
    return html

def main():
    output = os.path.join(os.path.dirname(__file__), "..", "index.html")
    generate_report(output)
    print(f"\n打開 {output} 查看報告")

if __name__ == "__main__":
    main()

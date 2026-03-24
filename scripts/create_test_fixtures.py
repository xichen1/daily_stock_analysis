#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create static JSON test fixtures for local UI testing of the /reports page.
No project dependencies required — uses only the standard library.

Usage:
    python3 scripts/create_test_fixtures.py

Writes sample JSON files to apps/dsa-web/public/data/ so you can run
'npm run dev' and test the /reports page immediately.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "apps" / "dsa-web" / "public" / "data"

(OUTPUT_DIR / "dates").mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)

STOCKS = [
    ("600519", "贵州茅台"),
    ("000001", "平安银行"),
    ("300750", "宁德时代"),
    ("AAPL", "苹果"),
    ("hk00700", "腾讯控股"),
]
ADVICES = ["买入", "持有", "观望", "减仓", "卖出"]
TRENDS = ["强势上涨", "震荡上行", "横盘整理", "震荡下行", "弱势下跌"]

today = datetime.now()
record_id = 1
all_items_by_date: dict = {}
all_stocks: dict = {}

for day_offset in range(5):
    dt = today - timedelta(days=day_offset)
    date_str = dt.strftime("%Y-%m-%d")
    day_items = []

    for i, (code, name) in enumerate(STOCKS):
        score = 45 + (i * 7 + day_offset * 3) % 45
        advice = ADVICES[(i + day_offset) % len(ADVICES)]
        trend = TRENDS[(i * 2 + day_offset) % len(TRENDS)]
        created_at = dt.strftime("%Y-%m-%dT18:00:00")

        summary_item = {
            "id": record_id,
            "queryId": f"test-{day_offset}-{code}",
            "stockCode": code,
            "stockName": name,
            "reportType": "detailed",
            "sentimentScore": score,
            "operationAdvice": advice,
            "trendPrediction": trend,
            "createdAt": created_at,
        }
        day_items.append(summary_item)

        # full report detail
        detail = {
            "meta": {
                "id": record_id,
                "queryId": f"test-{day_offset}-{code}",
                "stockCode": code,
                "stockName": name,
                "reportType": "detailed",
                "createdAt": created_at,
                "modelUsed": "test-model",
            },
            "summary": {
                "analysisSummary": f"{name} 近期{trend}，建议关注。技术面{trend}，量能配合良好，短期情绪评分 {score}。",
                "operationAdvice": advice,
                "trendPrediction": trend,
                "sentimentScore": score,
                "sentimentLabel": (
                    "极度乐观" if score > 80 else
                    "乐观" if score > 60 else
                    "中性" if score > 40 else
                    "悲观" if score > 20 else "极度悲观"
                ),
            },
            "strategy": {
                "idealBuy": f"{1800 + i * 10:.2f}",
                "secondaryBuy": f"{1760 + i * 10:.2f}",
                "stopLoss": f"{1720 + i * 10:.2f}",
                "takeProfit": f"{1900 + i * 10:.2f}",
            },
            "details": {
                "newsContent": (
                    f"【{name}】近期新闻摘要：\n"
                    f"1. 公司公告显示季度营收同比增长 15%，超预期。\n"
                    f"2. 行业政策持续偏暖，龙头企业受益明显。\n"
                    f"3. 机构持仓小幅增加，外资净流入。"
                ),
                "rawResult": {
                    "dashboard": {
                        "core_conclusion": {
                            "one_sentence": f"{name} 短期{trend}，建议{advice}",
                            "signal_type": "buy" if "买" in advice else "hold",
                            "time_sensitivity": "近期",
                        },
                        "data_perspective": {
                            "trend_status": {"bias_status": trend, "bias_strength": "中等"},
                            "volume_analysis": {"volume_ratio": 1.2, "signal": "量能温和放大"},
                        },
                        "battle_plan": {
                            "sniper_points": {
                                "ideal_buy": f"{1800 + i * 10:.2f}",
                                "secondary_buy": f"{1760 + i * 10:.2f}",
                                "stop_loss": f"{1720 + i * 10:.2f}",
                                "take_profit": f"{1900 + i * 10:.2f}",
                            }
                        },
                    },
                    "trend_analysis": "均线多头排列，短期趋势向上，支撑位稳固。",
                    "technical_analysis": "MACD 金叉信号出现，RSI 处于合理区间（55），KDJ 底部金叉。",
                    "fundamental_analysis": "ROE 稳定，营收持续增长，行业竞争格局良好。",
                    "sentiment_score": score,
                    "operation_advice": advice,
                    "trend_prediction": trend,
                },
            },
        }

        report_path = OUTPUT_DIR / "reports" / f"{record_id}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, separators=(",", ":"))

        all_stocks[code] = {"code": code, "name": name, "count": all_stocks.get(code, {}).get("count", 0) + 1}
        record_id += 1

    all_items_by_date[date_str] = day_items
    date_path = OUTPUT_DIR / "dates" / f"{date_str}.json"
    with open(date_path, "w", encoding="utf-8") as f:
        json.dump(day_items, f, ensure_ascii=False, separators=(",", ":"))

# Write index
index = {
    "dates": [
        {"date": d, "count": len(items)}
        for d, items in sorted(all_items_by_date.items(), reverse=True)
    ],
    "stocks": sorted(all_stocks.values(), key=lambda x: -x["count"]),
}
with open(OUTPUT_DIR / "index.json", "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

total_reports = record_id - 1
print(f"Created {total_reports} report fixtures across {len(all_items_by_date)} dates.")
print(f"Files written to: {OUTPUT_DIR}")
print("\nNext: cd apps/dsa-web && npm run dev  →  open http://localhost:5173/reports")

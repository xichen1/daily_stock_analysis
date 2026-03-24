#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed the local SQLite DB with sample analysis records for UI testing.

Usage:
    python scripts/seed_test_data.py

Creates a few days of sample reports across several stocks so the /reports
page can be tested locally without running actual analysis.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.makedirs(PROJECT_ROOT / "data", exist_ok=True)

from src.storage import DatabaseManager, AnalysisHistory, Base

STOCKS = [
    ("600519", "贵州茅台"),
    ("000001", "平安银行"),
    ("300750", "宁德时代"),
    ("AAPL", "苹果"),
    ("hk00700", "腾讯控股"),
]

ADVICES = ["买入", "持有", "观望", "减仓", "卖出"]
TRENDS = ["强势上涨", "震荡上行", "横盘整理", "震荡下行", "弱势下跌"]


def make_raw(code, name, score, advice, trend):
    return json.dumps({
        "dashboard": {
            "core_conclusion": {
                "one_sentence": f"{name} 短期{trend}，建议{advice}",
                "signal_type": "buy" if "买" in advice else "hold",
            },
            "battle_plan": {
                "sniper_points": {
                    "ideal_buy": "1800.00",
                    "secondary_buy": "1760.00",
                    "stop_loss": "1720.00",
                    "take_profit": "1900.00",
                }
            },
        },
        "sentiment_score": score,
        "operation_advice": advice,
        "trend_prediction": trend,
        "analysis_summary": f"{name} 近期{trend}，情绪评分 {score}。",
        "trend_analysis": "均线多头排列，短期趋势向上。",
        "technical_analysis": "MACD 金叉，RSI 处于合理区间，量能温和放大。",
        "news_summary": "近期无重大利空消息，行业政策偏暖。",
        "model_used": "test-model",
    }, ensure_ascii=False)


def main():
    db = DatabaseManager.get_instance()
    Base.metadata.create_all(db.engine)

    today = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    records_inserted = 0

    for day_offset in range(5):  # 5 trading days
        dt = today - timedelta(days=day_offset)
        for i, (code, name) in enumerate(STOCKS):
            score = 45 + (i * 7 + day_offset * 3) % 45
            advice = ADVICES[(i + day_offset) % len(ADVICES)]
            trend = TRENDS[(i * 2 + day_offset) % len(TRENDS)]

            record = AnalysisHistory(
                query_id=f"test-{day_offset}-{code}",
                code=code,
                name=name,
                report_type="detailed",
                sentiment_score=score,
                operation_advice=advice,
                trend_prediction=trend,
                analysis_summary=f"{name} 近期{trend}，情绪评分 {score}。",
                raw_result=make_raw(code, name, score, advice, trend),
                news_content=f"{name} 相关新闻摘要：近期行业动态平稳，公司基本面无重大变化。",
                ideal_buy=1800.0 + i * 10,
                secondary_buy=1760.0 + i * 10,
                stop_loss=1720.0 + i * 10,
                take_profit=1900.0 + i * 10,
                created_at=dt,
            )
            with db.get_session() as session:
                session.add(record)
                session.commit()
            records_inserted += 1

    print(f"Seeded {records_inserted} records across 5 days.")
    print("Next: python scripts/export_reports_json.py")


if __name__ == "__main__":
    main()

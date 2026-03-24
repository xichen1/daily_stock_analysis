#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export analysis history from SQLite to static JSON files for Cloudflare Pages deployment.

Reads the SQLite database and writes JSON files into apps/dsa-web/public/data/:
  index.json           - list of all dates and stocks with counts
  dates/<date>.json    - all report summaries for a given date
  reports/<id>.json    - full report detail for a given record ID

Run after python main.py in the GitHub Action.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure the project root is on the path so src/ imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import DatabaseManager, AnalysisHistory
from src.services.history_service import HistoryService
from src.utils.data_processing import parse_json_field, normalize_model_used
from sqlalchemy import select, func, desc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = PROJECT_ROOT / "apps" / "dsa-web" / "public" / "data"


def ensure_dirs():
    (OUTPUT_DIR / "dates").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "reports").mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def build_index(db: DatabaseManager) -> dict:
    """Build index.json: list of dates (desc) and stocks with counts."""
    with db.get_session() as session:
        # Dates with counts
        date_rows = session.execute(
            select(
                func.date(AnalysisHistory.created_at).label("date"),
                func.count(AnalysisHistory.id).label("count"),
            )
            .group_by(func.date(AnalysisHistory.created_at))
            .order_by(desc("date"))
        ).all()

        # Stock codes with counts
        stock_rows = session.execute(
            select(
                AnalysisHistory.code,
                AnalysisHistory.name,
                func.count(AnalysisHistory.id).label("count"),
            )
            .group_by(AnalysisHistory.code)
            .order_by(desc("count"))
        ).all()

    dates = [{"date": str(r.date), "count": r.count} for r in date_rows]
    stocks = [
        {"code": r.code, "name": r.name or r.code, "count": r.count}
        for r in stock_rows
    ]
    return {"dates": dates, "stocks": stocks}


def build_date_file(db: DatabaseManager, date_str: str) -> list:
    """Build dates/<date>.json: summary list of all reports on that date."""
    records, _ = db.get_analysis_history_paginated(
        start_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        end_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        offset=0,
        limit=500,
    )
    items = []
    for r in records:
        items.append({
            "id": r.id,
            "queryId": r.query_id,
            "stockCode": r.code,
            "stockName": r.name or r.code,
            "reportType": r.report_type,
            "sentimentScore": r.sentiment_score,
            "operationAdvice": r.operation_advice,
            "trendPrediction": r.trend_prediction,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
        })
    return items


def build_report_file(service: HistoryService, record_id: int) -> dict:
    """Build reports/<id>.json: full report detail."""
    detail = service.get_history_detail_by_id(record_id)
    if not detail:
        return {}

    raw_result = detail.get("raw_result")
    model_used = None
    if isinstance(raw_result, dict):
        model_used = normalize_model_used(raw_result.get("model_used"))

    return {
        "meta": {
            "id": detail.get("id"),
            "queryId": detail.get("query_id"),
            "stockCode": detail.get("stock_code"),
            "stockName": detail.get("stock_name"),
            "reportType": detail.get("report_type"),
            "createdAt": detail.get("created_at"),
            "modelUsed": model_used,
        },
        "summary": {
            "analysisSummary": detail.get("analysis_summary"),
            "operationAdvice": detail.get("operation_advice"),
            "trendPrediction": detail.get("trend_prediction"),
            "sentimentScore": detail.get("sentiment_score"),
            "sentimentLabel": detail.get("sentiment_label"),
        },
        "strategy": {
            "idealBuy": detail.get("ideal_buy"),
            "secondaryBuy": detail.get("secondary_buy"),
            "stopLoss": detail.get("stop_loss"),
            "takeProfit": detail.get("take_profit"),
        },
        "details": {
            "newsContent": detail.get("news_content"),
            "rawResult": raw_result,
        },
    }


def main():
    logger.info("Starting report export...")
    ensure_dirs()

    db = DatabaseManager.get_instance()
    service = HistoryService(db)

    # 1. Build index
    logger.info("Building index.json...")
    index = build_index(db)
    write_json(OUTPUT_DIR / "index.json", index)
    logger.info(f"  {len(index['dates'])} dates, {len(index['stocks'])} stocks")

    # 2. Build per-date files and collect all record IDs
    all_record_ids = set()
    for date_entry in index["dates"]:
        date_str = date_entry["date"]
        logger.info(f"Building dates/{date_str}.json ...")
        items = build_date_file(db, date_str)
        write_json(OUTPUT_DIR / "dates" / f"{date_str}.json", items)
        for item in items:
            all_record_ids.add(item["id"])

    # 3. Build per-report detail files
    logger.info(f"Building {len(all_record_ids)} report detail files...")
    for record_id in all_record_ids:
        report = build_report_file(service, record_id)
        write_json(OUTPUT_DIR / "reports" / f"{record_id}.json", report)

    logger.info(f"Export complete. Files written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

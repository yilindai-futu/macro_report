"""
Lambda: 每天 UTC 14:00 拉取 FRED 宏观数据序列，快照存 S3。

环境变量:
  FRED_API_KEY  - FRED API 密钥（https://fred.stlouisfed.org/docs/api/api_key.html）
  S3_BUCKET     - 存储桶名称，例如 macro-report-dev-data
"""
import json
import logging
import os
import time
from datetime import date, datetime, timezone
from typing import Any

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ["FRED_API_KEY"]
S3_BUCKET = os.environ["S3_BUCKET"]

# (series_id, 中文名, 频率, 拉取期数)
SERIES: list[tuple[str, str, str, int]] = [
    ("FEDFUNDS", "联邦基金利率",         "monthly",   24),
    ("CPIAUCSL", "CPI全项",             "monthly",   24),
    ("PCEPILFE", "核心PCE物价指数",      "monthly",   24),
    ("T10YIE",   "10年TIPS通胀预期",     "daily",     90),
    ("GDPC1",    "实际GDP季调年化",      "quarterly", 12),
    ("MANEMP",   "制造业就业",           "monthly",   24),
    ("JTSJOL",   "JOLTS职位空缺",        "monthly",   24),
    ("UNRATE",   "失业率",              "monthly",   24),
    ("PAYEMS",   "非农就业NFP",          "monthly",   24),
    ("ISRATIO",  "零售库存销售比",        "monthly",   24),
    ("T10Y2Y",   "10年-2年利差",         "daily",     90),
    ("T10YFF",   "10年-联邦基金利率利差", "daily",     90),
    ("VIXCLS",   "VIX收盘价",           "daily",     90),
]

s3 = boto3.client("s3")


def _fetch_with_retry(series_id: str, limit: int, max_retries: int = 3) -> dict[str, Any]:
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "limit": limit,
        "sort_order": "desc",
        "file_type": "json",
    }
    for attempt in range(max_retries):
        try:
            resp = requests.get(FRED_BASE, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning(f"{series_id} attempt {attempt + 1} failed: {e}, retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")  # 满足类型检查


def _parse_observations(raw: list[dict]) -> tuple[list[dict], str | None, str | None]:
    """清理 FRED 观测值，将 '.' 替换为 None，返回 (observations, latest_value, latest_date)。"""
    cleaned = []
    for obs in raw:
        value = obs["value"]
        cleaned.append({
            "date": obs["date"],
            "value": None if value == "." else value,
        })
    latest = cleaned[0] if cleaned else {}
    return cleaned, latest.get("value"), latest.get("date")


def handler(event: dict, context: Any) -> dict:
    snapshot_date = date.today().isoformat()
    fetched_at = datetime.now(timezone.utc).isoformat()

    success: list[str] = []
    failed: list[dict] = []

    for series_id, series_name, frequency, lookback in SERIES:
        try:
            data = _fetch_with_retry(series_id, lookback)
            observations, latest_value, latest_data_time = _parse_observations(
                data.get("observations", [])
            )

            payload = {
                "series_id": series_id,
                "series_name": series_name,
                "frequency": frequency,
                "snapshot_date": snapshot_date,
                "fetched_at": fetched_at,
                "latest_value": latest_value,
                "latest_data_time": latest_data_time,
                "observations": observations,
            }

            s3_key = f"fred/snapshots/{snapshot_date}/{series_id}.json"
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(payload, ensure_ascii=False, indent=2),
                ContentType="application/json",
            )

            logger.info(f"OK {series_id}: {len(observations)} obs → s3://{S3_BUCKET}/{s3_key}")
            success.append(series_id)

        except Exception as e:
            logger.error(f"FAIL {series_id}: {e}")
            failed.append({"series_id": series_id, "error": str(e)})

    summary = {
        "snapshot_date": snapshot_date,
        "success_count": len(success),
        "failed_count": len(failed),
        "success": success,
        "failed": failed,
    }
    logger.info(f"Summary: {summary}")
    return summary

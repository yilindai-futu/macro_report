"""
Lambda: 每天 UTC 14:00 拉取 FRED 宏观数据序列，快照存 S3。

环境变量:
  FRED_API_KEY  - FRED API 密钥（https://fred.stlouisfed.org/docs/api/api_key.html）
  S3_BUCKET     - 存储桶名称，例如 macro-report-dev-data（为空则写本地文件）
  LOCAL_DATA_DIR - 本地 fallback 目录（默认 ./data/fred_snapshots）
"""
import json
import logging
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ["FRED_API_KEY"]
S3_BUCKET = os.environ.get("S3_BUCKET", "")
LOCAL_DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", "./data/fred_snapshots"))

# (series_id, 中文名, 频率, 拉取期数)
SERIES: list[tuple[str, str, str, int]] = [
    # 第一大类：增长类指标
    ("GDPC1",         "实际GDP季调年化",              "quarterly", 12),
    ("GDPNOW",        "亚特兰大联储GDPNow预测",       "daily",     90),
    ("MANEMP",        "制造业就业",                   "monthly",   24),
    #("NAPMNOI",       "ISM制造业新订单指数",           "monthly",   24),
    #("NAPMII",        "ISM制造业库存指数",             "monthly",   24),
    ("INDPRO",        "工业生产指数",                  "monthly",   24),
    ("TCU",           "产能利用率",                    "monthly",   24),
    ("RSAFS",         "零售销售（除食品服务）",         "monthly",   24),
    ("DGORDER",       "耐用品订单",                   "monthly",   24),

    # 第二大类：通胀类指标
    ("CPIAUCSL",      "CPI全项",                     "monthly",   24),
    ("CPILFESL",      "核心CPI（剔除食品能源）",       "monthly",   24),
    ("PCEPILFE",      "核心PCE物价指数",              "monthly",   24),
    ("T5YIE",         "5年盈亏平衡通胀率",            "daily",     90),
    ("PPIACO",        "PPI生产者价格指数",            "monthly",   24),
    ("CES0500000003", "平均时薪（私人非农）",          "monthly",   24),

    # 第三大类：就业类指标
    ("PAYEMS",        "非农就业NFP",                  "monthly",   24),
    ("UNRATE",        "失业率",                       "monthly",   24),
    ("SAHMREALTIME",  "Sahm Rule实时衰退指标",        "monthly",   24),
    ("ICSA",          "初请失业金人数",                "weekly",    52),
    ("CCSA",          "持续领取失业金人数",            "weekly",    52),
    ("JTSJOL",        "JOLTS职位空缺",               "monthly",   24),
    ("JTSQUR",        "JOLTS离职率",                  "monthly",   24),
    ("CIVPART",       "劳动参与率",                   "monthly",   24),

    # 第四大类：货币政策与利率指标
    ("FEDFUNDS",      "联邦基金利率",                 "monthly",   24),
    ("DGS10",         "10年期国债收益率",              "daily",     90),
    ("T10Y2Y",        "10年-2年利差",                 "daily",     90),
    ("DFII10",        "10年实际利率（TIPS）",          "daily",     90),
    ("M2SL",          "M2货币供应量",                 "monthly",   24),
    ("WALCL",         "美联储资产负债表总资产",        "weekly",    52),

    # 第五大类：信用与金融压力指标
    ("BAMLC0A0CM",    "投资级信用利差（IG OAS）",      "daily",     90),
    ("BAMLH0A0HYM2",  "高收益信用利差（HY OAS）",      "daily",     90),
    ("DCPF3M",        "3个月商业票据利率",             "daily",     90),
    ("STLFSI4",       "圣路易斯联储金融压力指数",      "weekly",    52),

    # 第六大类：市场信号与情绪指标
    ("VIXCLS",        "VIX收盘价",                    "daily",     90),

    # 第七大类：库存与投资周期指标
    ("ISRATIO",       "库存销售比",                   "monthly",   24),
    ("HOUST",         "新屋开工",                     "monthly",   24),
    ("PERMIT",        "营建许可",                     "monthly",   24),
    ("NEWORDER",      "制造业新订单",                  "monthly",   24),

    # 第八大类：全球与外部冲击指标
    ("DTWEXBGS",      "贸易加权美元指数",              "daily",     90),
]
SERIES = SERIES[:3]
s3 = boto3.client("s3") if S3_BUCKET else None


def _save(snapshot_date: str, series_id: str, payload: dict) -> str:
    """写入 S3 或本地文件，返回存储路径描述。"""
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    key = f"tmp/fred/snapshots/{snapshot_date}/{series_id}.json"
    if S3_BUCKET and s3:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ContentType="application/json")
        return f"s3://{S3_BUCKET}/{key}"
    else:
        raise Exception(f"AWS - S3 failed: S3_BUCKET={S3_BUCKET},s3={s3}")
    local_path = LOCAL_DATA_DIR / f"{series_id}.json"
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(body, encoding="utf-8")
    return str(local_path)


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

            dest = _save(snapshot_date, series_id, payload)
            logger.info(f"OK {series_id}: {len(observations)} obs → {dest}")
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

"""S3 helpers for reading FRED snapshot files，本地开发时 fallback 到本地目录。"""
import asyncio
import json
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from config import settings

PREFIX = "tmp/fred/snapshots/"
LOCAL_DATA_DIR = Path(settings.local_data_dir)


def _use_local() -> bool:
    return not settings.s3_bucket or settings.s3_bucket == "local"


@lru_cache(maxsize=1)
def _s3():
    session = (
        boto3.Session(profile_name=settings.aws_profile)
        if settings.aws_profile
        else boto3.Session()
    )
    return session.client("s3", region_name=settings.aws_region)


def list_snapshot_dates() -> list[str]:
    if _use_local():
        if not LOCAL_DATA_DIR.exists():
            return []
        for f in LOCAL_DATA_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if d := data.get("snapshot_date"):
                    return [d]
            except Exception:
                continue
        return []

    paginator = _s3().get_paginator("list_objects_v2")
    dates: set[str] = set()
    for page in paginator.paginate(
        Bucket=settings.s3_bucket, Prefix=PREFIX, Delimiter="/"
    ):
        for cp in page.get("CommonPrefixes", []):
            date_part = cp["Prefix"].removeprefix(PREFIX).rstrip("/")
            if date_part:
                dates.add(date_part)
    return sorted(dates)


def get_series_snapshot(snapshot_date: str, series_id: str) -> dict | None:
    if _use_local():
        path = LOCAL_DATA_DIR / f"{series_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    key = f"{PREFIX}{snapshot_date}/{series_id}.json"
    try:
        obj = _s3().get_object(Bucket=settings.s3_bucket, Key=key)
        return json.loads(obj["Body"].read())
    except ClientError as e:
        if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
            return None
        raise


async def get_all_series_for_date(snapshot_date: str, series_ids: list[str]) -> list[dict]:
    loop = asyncio.get_event_loop()

    async def _fetch(sid: str) -> dict | None:
        return await loop.run_in_executor(None, get_series_snapshot, snapshot_date, sid)

    results = await asyncio.gather(*[_fetch(sid) for sid in series_ids])
    return [r for r in results if r is not None]

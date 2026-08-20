"""本地测试：不需要 AWS 凭证，数据写入本地文件。"""
import os
import sys
from pathlib import Path

# 共享数据目录：FastAPI 和 Lambda 都从这里读写
SHARED_DATA_DIR = str(Path(__file__).resolve().parents[3] / "data" / "fred_snapshots")

os.environ["FRED_API_KEY"] = "a9a70fc1cbe4dcc8cdafe9b070f347cc"
os.environ["LOCAL_DATA_DIR"] = SHARED_DATA_DIR
# S3_BUCKET 不设 → handler 自动走本地文件 fallback

from handler import handler, SERIES, _fetch_with_retry, _parse_observations

print(f"数据目录: {SHARED_DATA_DIR}\n")

print("=== 单序列快速验证（前3个）===")
for series_id, series_name, frequency, lookback in SERIES:
    try:
        data = _fetch_with_retry(series_id, 3)
        obs, latest_value, latest_date = _parse_observations(data.get("observations", []))
        print(f"  {series_id:12s} {series_name:16s}  最新值={latest_value}  日期={latest_date}")
    except Exception as e:
        print(f"  {series_id:12s} FAIL: {e}", file=sys.stderr)

print("\n=== 全量采集（写入本地文件）===")
result = handler({}, None)

print(f"\n  成功: {result['success_count']} 个序列")
print(f"  失败: {result['failed_count']} 个序列")
if result["failed"]:
    for f in result["failed"]:
        print(f"    FAIL {f['series_id']}: {f['error']}")
print("\n=== 完成 ===")

"""本地测试：模拟 Lambda 调用，不需要真实 AWS 环境。"""
import os
import sys

os.environ["FRED_API_KEY"] = "a9a70fc1cbe4dcc8cdafe9b070f347cc"
os.environ["S3_BUCKET"] = "dry-run"  # 本地不真实写 S3

# 替换 boto3.client("s3") 为空操作，避免需要 AWS 凭证
import unittest.mock as mock

with mock.patch("boto3.client") as mock_boto:
    mock_s3 = mock.MagicMock()
    mock_boto.return_value = mock_s3

    from handler import _fetch_with_retry, _parse_observations, SERIES

    print("=== 单序列快速验证 ===")
    for series_id, series_name, frequency, lookback in SERIES:
        try:
            data = _fetch_with_retry(series_id, 3)
            obs, latest_value, latest_date = _parse_observations(data.get("observations", []))
            print(f"  {series_id:12s} {series_name:16s}  最新值={latest_value}  日期={latest_date}")
        except Exception as e:
            print(f"  {series_id:12s} FAIL: {e}", file=sys.stderr)

    print("\n=== 全量 handler 调用（dry-run，S3 写入已 mock）===")
    from handler import handler
    result = handler({}, None)

    print(f"\n  成功: {result['success_count']} 个序列")
    print(f"  失败: {result['failed_count']} 个序列")
    if result["failed"]:
        for f in result["failed"]:
            print(f"    FAIL {f['series_id']}: {f['error']}")

    print("\n  S3 put_object 调用次数:", mock_s3.put_object.call_count)
    print("\n=== 完成 ===")

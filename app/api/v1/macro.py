from fastapi import APIRouter, HTTPException

from core.s3 import get_all_series_for_date, get_series_snapshot, list_snapshot_dates
from models.schemas import SnapshotDatesResponse, SnapshotResponse, SeriesSnapshot

SERIES_IDS = [
    # 增长
    "GDPC1", "GDPNOW", "MANEMP", "NAPMNOI", "NAPMII", "INDPRO", "TCU", "RSAFS", "DGORDER",
    # 通胀
    "CPIAUCSL", "CPILFESL", "PCEPILFE", "T5YIE", "PPIACO", "CES0500000003",
    # 就业
    "PAYEMS", "UNRATE", "SAHMREALTIME", "ICSA", "CCSA", "JTSJOL", "JTSQUR", "CIVPART",
    # 货币政策与利率
    "FEDFUNDS", "DGS10", "T10Y2Y", "DFII10", "M2SL", "WALCL",
    # 信用与金融压力
    "BAMLC0A0CM", "BAMLH0A0HYM2", "DCPF3M", "STLFSI4",
    # 市场情绪
    "VIXCLS",
    # 库存与投资周期
    "ISRATIO", "HOUST", "PERMIT", "NEWORDER",
    # 全球与外部冲击
    "DTWEXBGS",
]

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/snapshots", response_model=SnapshotDatesResponse)
async def list_snapshots() -> SnapshotDatesResponse:
    try:
        dates = list_snapshot_dates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return SnapshotDatesResponse(dates=dates)


@router.get("/snapshots/latest", response_model=SnapshotResponse)
async def get_latest_snapshot() -> SnapshotResponse:
    try:
        dates = list_snapshot_dates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not dates:
        raise HTTPException(status_code=404, detail="暂无快照数据，请先运行 Lambda 采集")
    latest = dates[-1]
    return await _build_snapshot_response(latest)


@router.get("/snapshots/{snapshot_date}", response_model=SnapshotResponse)
async def get_snapshot(snapshot_date: str) -> SnapshotResponse:
    return await _build_snapshot_response(snapshot_date)


@router.get("/series/{series_id}", response_model=SeriesSnapshot)
async def get_series(series_id: str) -> SeriesSnapshot:
    dates = list_snapshot_dates()
    if not dates:
        raise HTTPException(status_code=404, detail="暂无快照数据")
    latest = dates[-1]
    data = get_series_snapshot(latest, series_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"序列 {series_id} 不存在")
    return SeriesSnapshot(**data)


async def _build_snapshot_response(date: str) -> SnapshotResponse:
    try:
        raw_list = await get_all_series_for_date(date, SERIES_IDS)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not raw_list:
        raise HTTPException(status_code=404, detail=f"日期 {date} 无数据")
    return SnapshotResponse(
        snapshot_date=date,
        series=[SeriesSnapshot(**r) for r in raw_list],
    )

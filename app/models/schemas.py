from pydantic import BaseModel


class Observation(BaseModel):
    date: str
    value: str | None


class SeriesSnapshot(BaseModel):
    series_id: str
    series_name: str
    frequency: str
    snapshot_date: str
    fetched_at: str
    latest_value: str | None
    latest_data_time: str | None
    observations: list[Observation]


class SnapshotResponse(BaseModel):
    snapshot_date: str
    series: list[SeriesSnapshot]


class SnapshotDatesResponse(BaseModel):
    dates: list[str]

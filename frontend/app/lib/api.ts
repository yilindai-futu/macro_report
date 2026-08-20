export interface Observation {
  date: string;
  value: string | null;
}

export interface SeriesSnapshot {
  series_id: string;
  series_name: string;
  frequency: string;
  snapshot_date: string;
  fetched_at: string;
  latest_value: string | null;
  latest_data_time: string | null;
  observations: Observation[];
}

export interface SnapshotResponse {
  snapshot_date: string;
  series: SeriesSnapshot[];
}

export async function fetchLatestSnapshot(): Promise<SnapshotResponse> {
  const res = await fetch("/api/v1/macro/snapshots/latest");
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

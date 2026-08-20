"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { SeriesSnapshot } from "../lib/api";

interface Props {
  series: SeriesSnapshot;
}

export default function SeriesChart({ series }: Props) {
  const data = [...series.observations]
    .reverse()
    .slice(-30)
    .map((o) => ({
      date: o.date,
      value: o.value !== null ? parseFloat(o.value) : null,
    }))
    .filter((o) => o.value !== null);

  const latestDisplay =
    series.latest_value !== null
      ? `${parseFloat(series.latest_value).toFixed(2)}`
      : "N/A";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col gap-2">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-mono text-gray-400">{series.series_id}</p>
          <h3 className="text-sm font-semibold text-gray-800">{series.series_name}</h3>
        </div>
        <div className="text-right">
          <p className="text-xl font-bold text-indigo-600">{latestDisplay}</p>
          <p className="text-xs text-gray-400">{series.latest_data_time}</p>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 9 }}
            tickFormatter={(d: string) => d.slice(5)}
            interval="preserveStartEnd"
          />
          <YAxis tick={{ fontSize: 9 }} width={36} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ fontSize: 11 }}
            formatter={(v: number) => [v.toFixed(2), series.series_name]}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#6366f1"
            strokeWidth={1.5}
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

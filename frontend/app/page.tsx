"use client";

import { useEffect, useState } from "react";
import { fetchLatestSnapshot, SnapshotResponse, SeriesSnapshot } from "./lib/api";
import { CATEGORIES } from "./lib/categories";
import SeriesChart from "./components/SeriesChart";

export default function Home() {
  const [data, setData] = useState<SnapshotResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLatestSnapshot()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  const seriesMap = new Map<string, SeriesSnapshot>(
    data?.series.map((s) => [s.series_id, s]) ?? []
  );

  return (
    <main className="max-w-7xl mx-auto px-4 py-8">
      {/* 头部 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">美股宏观数据仪表板</h1>
        {data && (
          <p className="text-sm text-gray-500 mt-1">
            数据快照日期：{data.snapshot_date} · {data.series.length} 个指标
          </p>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6 text-sm">
          <strong>加载失败：</strong>{error}
          <p className="mt-1 text-xs text-red-500">
            请确保 FastAPI 已在 localhost:8000 启动，且本地数据已采集。
          </p>
        </div>
      )}

      {/* 骨架屏 */}
      {!data && !error && (
        <div className="space-y-10">
          {CATEGORIES.map((cat) => (
            <section key={cat.name}>
              <div className="h-5 w-32 bg-gray-200 rounded animate-pulse mb-4" />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {cat.seriesIds.map((id) => (
                  <div key={id} className="bg-white rounded-xl border border-gray-200 p-4 h-48 animate-pulse" />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {/* 分类展示 */}
      {data && (
        <div className="space-y-10">
          {CATEGORIES.map((cat) => {
            const items = cat.seriesIds
              .map((id) => seriesMap.get(id))
              .filter((s): s is SeriesSnapshot => s !== undefined);

            if (items.length === 0) return null;

            return (
              <section key={cat.name}>
                <h2 className="text-base font-semibold text-gray-700 border-b border-gray-200 pb-2 mb-4">
                  {cat.name}
                  <span className="ml-2 text-xs font-normal text-gray-400">{items.length} 个指标</span>
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map((s) => (
                    <SeriesChart key={s.series_id} series={s} />
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      <footer className="mt-12 text-center text-xs text-gray-400">
        数据来源：FRED（美联储经济数据库）· 仅供参考，不构成投资建议
      </footer>
    </main>
  );
}

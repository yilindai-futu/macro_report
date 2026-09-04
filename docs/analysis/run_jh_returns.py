import numpy as np
import pandas as pd
import yfinance as yf

# ============================================================
# 1. 参数
# ============================================================

# 当前日期：2026-09-04
AS_OF = pd.Timestamp("2026-09-04")

EVENTS = [
    {"年份": 2026, "演讲人": "Kevin Warsh",       "会议日期": "2026-08-28"},
    {"年份": 2025, "演讲人": "Jerome H. Powell", "会议日期": "2025-08-22"},
    {"年份": 2024, "演讲人": "Jerome H. Powell", "会议日期": "2024-08-23"},
    {"年份": 2023, "演讲人": "Jerome H. Powell", "会议日期": "2023-08-25"},
    {"年份": 2022, "演讲人": "Jerome H. Powell", "会议日期": "2022-08-26"},
    {"年份": 2021, "演讲人": "Jerome H. Powell", "会议日期": "2021-08-27"},
    {"年份": 2020, "演讲人": "Jerome H. Powell", "会议日期": "2020-08-27"},
    {"年份": 2019, "演讲人": "Jerome H. Powell", "会议日期": "2019-08-23"},
    {"年份": 2018, "演讲人": "Jerome H. Powell", "会议日期": "2018-08-24"},
    {"年份": 2017, "演讲人": "Janet L. Yellen",  "会议日期": "2017-08-25"},
]

ETFS = ["SPY", "QQQ", "TLT", "HYG", "GLD", "EEM", "IWM"]

HORIZONS = {
    "1W": pd.DateOffset(weeks=1),
    "1M": pd.DateOffset(months=1),
    "3M": pd.DateOffset(months=3),
    "6M": pd.DateOffset(months=6),
    "1Y": pd.DateOffset(years=1),
}

# ============================================================
# 2. 下载复权价格
# auto_adjust=True：
# 下载的 Close 已按拆股及现金分红进行调整，可用于计算 total return
# ============================================================

download_start = (
    min(pd.Timestamp(x["会议日期"]) for x in EVENTS)
    - pd.Timedelta(days=10)
)

# yfinance 的 end 参数不包含当天，所以增加1天
download_end = AS_OF + pd.Timedelta(days=1)

prices = {}

for ticker in ETFS:
    raw = yf.download(
        ticker,
        start=download_start.strftime("%Y-%m-%d"),
        end=download_end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise RuntimeError(f"{ticker} 没有下载到任何价格数据。")

    close = raw["Close"]

    # 兼容不同版本yfinance返回的多层列结构
    if isinstance(close, pd.DataFrame):
        if ticker in close.columns:
            close = close[ticker]
        else:
            close = close.iloc[:, 0]

    close = close.dropna().astype(float)
    close.index = pd.to_datetime(close.index)

    if close.index.tz is not None:
        close.index = close.index.tz_localize(None)

    prices[ticker] = close.sort_index()

# ============================================================
# 3. 日期匹配函数
# 目标日不是交易日时，使用其后的第一个交易日
# ============================================================

def first_trading_day_on_or_after(series, target_date):
    target_date = pd.Timestamp(target_date)
    position = series.index.searchsorted(target_date, side="left")

    if position >= len(series.index):
        return None

    return series.index[position]

# ============================================================
# 4. 计算各次会议后的Total Return
# ============================================================

rows = []

for event in EVENTS:
    event_date = pd.Timestamp(event["会议日期"])

    for ticker in ETFS:
        px = prices[ticker]

        entry_date = first_trading_day_on_or_after(px, event_date)

        row = {
            "年份": event["年份"],
            "演讲人": event["演讲人"],
            "会议日期": event_date,
            "ETF": ticker,
            "起始交易日": entry_date,
        }

        # 如果无法获得起始价格，则所有期限为空
        if entry_date is None or entry_date > AS_OF:
            for horizon in HORIZONS:
                row[horizon] = np.nan
                row[f"{horizon}终点"] = pd.NaT

            rows.append(row)
            continue

        entry_price = px.loc[entry_date]

        for horizon, offset in HORIZONS.items():
            target_date = event_date + offset

            # 尚未到达目标观察日
            if target_date > AS_OF:
                row[horizon] = np.nan
                row[f"{horizon}终点"] = pd.NaT
                continue

            exit_date = first_trading_day_on_or_after(px, target_date)

            # 尚没有对应交易日的收盘数据
            if exit_date is None or exit_date > AS_OF:
                row[horizon] = np.nan
                row[f"{horizon}终点"] = pd.NaT
                continue

            exit_price = px.loc[exit_date]
            total_return = exit_price / entry_price - 1

            row[horizon] = total_return
            row[f"{horizon}终点"] = exit_date

        rows.append(row)

result = pd.DataFrame(rows)

# 固定ETF排序
result["ETF"] = pd.Categorical(
    result["ETF"],
    categories=ETFS,
    ordered=True
)

result = result.sort_values(
    ["年份", "ETF"],
    ascending=[False, True]
)

return_columns = ["1W", "1M", "3M", "6M", "1Y"]
exit_columns = [f"{x}终点" for x in return_columns]

result = result[
    [
        "年份",
        "演讲人",
        "会议日期",
        "ETF",
        "起始交易日",
        *return_columns,
        *exit_columns,
    ]
]

# ============================================================
# 5. 生成统计汇总
# ============================================================

average_return = (
    result.groupby("ETF", observed=True)[return_columns]
    .mean()
    .reset_index()
)

median_return = (
    result.groupby("ETF", observed=True)[return_columns]
    .median()
    .reset_index()
)

positive_rate = (
    result.groupby("ETF", observed=True)[return_columns]
    .agg(lambda x: (x.dropna() > 0).mean() if len(x.dropna()) else np.nan)
    .reset_index()
)

sample_count = (
    result.groupby("ETF", observed=True)[return_columns]
    .count()
    .reset_index()
)

# ============================================================
# 6. 输出Excel并设置格式
# ============================================================

output_file = "Jackson_Hole_ETF_Total_Return.xlsx"

with pd.ExcelWriter(
    output_file,
    engine="xlsxwriter",
    datetime_format="yyyy-mm-dd",
) as writer:

    # 明细
    result.to_excel(
        writer,
        sheet_name="回测明细",
        index=False,
        na_rep="N/A",
    )

    # 汇总
    average_return.to_excel(
        writer,
        sheet_name="平均回报",
        index=False,
        na_rep="N/A",
    )

    median_return.to_excel(
        writer,
        sheet_name="中位数回报",
        index=False,
        na_rep="N/A",
    )

    positive_rate.to_excel(
        writer,
        sheet_name="上涨概率",
        index=False,
        na_rep="N/A",
    )

    sample_count.to_excel(
        writer,
        sheet_name="样本数量",
        index=False,
        na_rep="N/A",
    )

    workbook = writer.book

    header_format = workbook.add_format({
        "bold": True,
        "font_color": "white",
        "bg_color": "#1F4E78",
        "border": 1,
        "align": "center",
        "valign": "vcenter",
    })

    percent_format = workbook.add_format({
        "num_format": "0.00%",
        "align": "center",
    })

    date_format = workbook.add_format({
        "num_format": "yyyy-mm-dd",
        "align": "center",
    })

    center_format = workbook.add_format({
        "align": "center",
    })

    # 回测明细格式
    ws = writer.sheets["回测明细"]
    ws.freeze_panes(1, 5)
    ws.autofilter(0, 0, len(result), len(result.columns) - 1)
    ws.set_row(0, 24)

    for col_num, column_name in enumerate(result.columns):
        ws.write(0, col_num, column_name, header_format)

    ws.set_column(0, 0, 8, center_format)       # 年份
    ws.set_column(1, 1, 22)                     # 演讲人
    ws.set_column(2, 2, 13, date_format)        # 会议日期
    ws.set_column(3, 3, 9, center_format)       # ETF
    ws.set_column(4, 4, 13, date_format)        # 起始交易日

    for column_name in return_columns:
        col_num = result.columns.get_loc(column_name)
        ws.set_column(col_num, col_num, 11, percent_format)

    for column_name in exit_columns:
        col_num = result.columns.get_loc(column_name)
        ws.set_column(col_num, col_num, 13, date_format)

    # 汇总表格式
    for sheet_name, df in [
        ("平均回报", average_return),
        ("中位数回报", median_return),
        ("上涨概率", positive_rate),
        ("样本数量", sample_count),
    ]:
        sheet = writer.sheets[sheet_name]
        sheet.freeze_panes(1, 1)
        sheet.set_column(0, 0, 10, center_format)

        for col_num, column_name in enumerate(df.columns):
            sheet.write(0, col_num, column_name, header_format)

        if sheet_name != "样本数量":
            sheet.set_column(1, len(df.columns) - 1, 13, percent_format)
        else:
            sheet.set_column(1, len(df.columns) - 1, 13, center_format)

print(f"已生成：{output_file}")
"""
步骤 2：探索性数据分析（EDA）
读取合并后的 AirCondition.csv，输出城市 AQI 均值、90 天趋势和相关性热力图
"""

from pathlib import Path
import sys

import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Windows 终端编码修复（防止中文乱码）
if sys.platform == "win32":
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


DATA_CANDIDATES = [
    Path("data") / "AirCondition.csv",
    Path("output") / "merged_data" / "AirCondition.csv",
]
EDA_OUTPUT_DIR = Path("output") / "eda"
TREND_FIG = EDA_OUTPUT_DIR / "aqi_trend_90days.png"
HEATMAP_FIG = EDA_OUTPUT_DIR / "aqi_correlation_heatmap.png"


def ensure_output_dir():
    EDA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def locate_data_file():
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "未找到 AirCondition.csv，请先运行步骤 1（src/1_data_process.py）生成数据。"
    )


def set_chinese_font():
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def load_data():
    data_file = locate_data_file()
    print(f"读取数据文件: {data_file}")
    df = pd.read_csv(data_file)
    if "date" not in df.columns or "AQI" not in df.columns:
        raise ValueError("数据缺少 `date` 或 `AQI` 列，无法进行 EDA。")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    return df


def report_city_aqi_mean(df: pd.DataFrame):
    print("\n各城市 AQI 均值：")
    city_mean = df.groupby("city")["AQI"].mean().sort_values(ascending=False)
    for city, value in city_mean.items():
        print(f"  - {city}: {value:.2f}")
    summary_file = EDA_OUTPUT_DIR / "city_aqi_mean.csv"
    city_mean.to_frame(name="AQI_mean").to_csv(summary_file, encoding="utf-8-sig")
    print(f"均值统计已保存到 {summary_file}")


def plot_aqi_trend(df: pd.DataFrame, days: int = 90):
    if df.empty:
        print("数据为空，跳过 AQI 趋势图绘制。")
        return
    max_date = df["date"].max()
    min_date = max_date - pd.Timedelta(days=days - 1)
    filtered = df[df["date"].between(min_date, max_date)]

    if filtered.empty:
        print("筛选后的 90 天数据为空，无法绘制趋势图。")
        return

    unique_cities = filtered["city"].unique()
    num_cities = len(unique_cities)
    cols = 3
    rows = math.ceil(num_cities / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 3.5 * rows), sharex=False, sharey=True)
    if not isinstance(axes, np.ndarray):
        axes = np.array([axes])
    axes = axes.flatten()
    cmap = plt.get_cmap("tab20")
    color_positions = np.linspace(0, 1, num_cities) if num_cities > 1 else [0]

    for idx, (city, group) in enumerate(filtered.groupby("city")):
        ax = axes[idx]
        color = cmap(color_positions[idx % len(color_positions)])
        ax.plot(
            group["date"],
            group["AQI"],
            color=color,
            linewidth=1.5,
            marker="o",
            markersize=2,
        )
        ax.set_title(city, fontsize=11)
        ax.set_xlabel("日期")
        ax.set_ylabel("AQI")
        ax.grid(alpha=0.3, linestyle="--")
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    for idx in range(num_cities, len(axes)):
        axes[idx].axis("off")

    fig.suptitle(f"各城市最近 {days} 天 AQI 趋势", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(TREND_FIG, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"✓ 已保存 AQI 趋势图: {TREND_FIG}")


def plot_correlation_heatmap(df: pd.DataFrame):
    feature_cols = ["PM2.5", "PM10", "O3", "SO2", "NO2", "CO", "AQI"]
    available = [col for col in feature_cols if col in df.columns]
    if len(available) < 2:
        print("可用于相关性的列不足，跳过热力图绘制。")
        return

    corr_matrix = df[available].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn_r",
        square=True,
        cbar_kws={"label": "相关系数"},
    )
    plt.title("污染物与 AQI 相关性热力图", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(HEATMAP_FIG, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✓ 已保存相关性热力图: {HEATMAP_FIG}")


def main():
    set_chinese_font()
    ensure_output_dir()
    df = load_data()
    report_city_aqi_mean(df)
    plot_aqi_trend(df, days=90)
    plot_correlation_heatmap(df)


if __name__ == "__main__":
    main()

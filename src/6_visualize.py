"""阶段 6：预测结果可视化

- 读取 `output/predictions/AirPrediction.pkl`
- 生成 17 个城市的历史 AQI + 预测值折线子图保存为 `output/visualization/AirPrediction.png`
- 生成湖北省预测 AQI 热力图（带自动降级方案）输出 `output/visualization/map_hubei.html`
"""

from __future__ import annotations

import io
import math
import pickle
import sys
from pathlib import Path
from typing import List, Sequence

import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from map_visualization_helper import create_map_with_fallback


if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

PRED_FILE = Path("output") / "predictions" / "AirPrediction.pkl"
VIS_OUTPUT_DIR = Path("output") / "visualization"
VIS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SUBPLOT_FILE = VIS_OUTPUT_DIR / "AirPrediction.png"
MAP_FILE = VIS_OUTPUT_DIR / "map_hubei.html"


def set_chinese_font():
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def load_prediction_data():
    if not PRED_FILE.exists():
        raise FileNotFoundError(
            f"未找到 {PRED_FILE}，请先运行阶段 5（src/5_evaluate_predict.py）。"
        )
    with PRED_FILE.open("rb") as f:
        data = pickle.load(f)
    required_keys = {"省市地区", "大气质量预测", "历史大气质量"}
    if not required_keys.issubset(data.keys()):
        missing = required_keys - data.keys()
        raise ValueError(f"AirPrediction.pkl 缺少以下键: {missing}")
    return data


def plot_city_subplots(cities: Sequence[str], history: Sequence[Sequence[float]], preds: Sequence[float]):
    set_chinese_font()
    num_cities = len(cities)
    cols = 4
    rows = math.ceil(num_cities / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows), sharex=False)
    axes = axes.flatten()

    def normalize_history(item):
        if isinstance(item, (list, tuple, np.ndarray)):
            arr = np.array(item, dtype=float)
            if arr.ndim == 0:
                return arr.flatten().tolist()
            return arr.tolist()
        try:
            return [float(item)]
        except Exception:
            return []

    for idx, city in enumerate(cities):
        ax = axes[idx]
        hist_raw = history[idx] if idx < len(history) else []
        hist_list = normalize_history(hist_raw)
        hist = np.array(hist_list, dtype=float)
        x_hist = np.arange(len(hist))
        if hist.size > 0:
            ax.plot(x_hist, hist, label="历史 AQI", color="#1f77b4")
            last_value = hist[-1]
        else:
            last_value = np.nan
        pred_val = preds[idx]
        ax.scatter(len(hist), pred_val, color="#d62728", label="预测 AQI")
        if not np.isnan(last_value):
            ax.plot([len(hist) - 1, len(hist)], [last_value, pred_val], color="#d62728", linestyle="--", linewidth=1)
        ax.set_title(city, fontsize=10)
        ax.grid(alpha=0.3, linestyle="--")

    # 隐藏多余子图
    for extra_idx in range(num_cities, len(axes)):
        axes[extra_idx].axis("off")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=2,
        bbox_to_anchor=(0.5, -0.02),
        frameon=False,
    )
    fig.suptitle("湖北省各城市历史 AQI 与预测值", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(SUBPLOT_FILE, dpi=300)
    plt.close(fig)
    print(f"✓ 城市折线图已保存至 {SUBPLOT_FILE}")


def render_map(cities: Sequence[str], preds: Sequence[float]):
    data_pair = list(zip(cities, preds))
    success = create_map_with_fallback(data_pair, output_file=str(MAP_FILE))
    if success:
        print(f"✓ 地图可视化已保存至 {MAP_FILE}")
    else:
        print("⚠ 地图生成失败，请查看 map_visualization_helper 的日志。")


def main():
    print("开始阶段 6：可视化展示...")
    data = load_prediction_data()
    cities = data["省市地区"]
    preds = data["大气质量预测"]
    history = data["历史大气质量"]

    plot_city_subplots(cities, history, preds)
    render_map(cities, preds)
    print("阶段 6 完成！")


if __name__ == "__main__":
    main()

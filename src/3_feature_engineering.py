"""
阶段 3：特征工程与数据预处理
- 日期转换、标准化
- 时间/季节特征 & AQI 滞后特征
- SelectKBest 选择前 10 个特征
- 保存特征数据与 scaler 供后续建模使用
该程序代码完成人：张思浩，杨佳澄
"""

from __future__ import annotations

import io
import json
import pickle
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler


# 兼容 Windows 终端输出中文
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass

DATA_CANDIDATES = [
    Path("data") / "AirCondition.csv",
    Path("output") / "merged_data" / "AirCondition.csv",
]
NUMERIC_COLUMNS = ["PM2.5", "PM10", "O3", "SO2", "NO2", "CO", "AQI"]
FEATURE_OUTPUT_DIR = Path("output") / "features"
PROCESSED_FEATURE_FILE = FEATURE_OUTPUT_DIR / "processed_features.csv"
SELECTED_FEATURE_FILE = FEATURE_OUTPUT_DIR / "selected_features.csv"
FEATURE_METADATA_FILE = FEATURE_OUTPUT_DIR / "feature_metadata.json"
SCALER_FILE = Path("models") / "aqi_scaler.pkl"
TOP_K = 10


def ensure_output_dirs():
    FEATURE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCALER_FILE.parent.mkdir(parents=True, exist_ok=True)


def locate_data_file() -> Path:
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "未找到 AirCondition.csv，请先运行 src/1_data_process.py 合并数据。"
    )


def load_and_prepare_data() -> pd.DataFrame:
    data_file = locate_data_file()
    print(f"读取数据文件: {data_file}")
    df = pd.read_csv(data_file)
    missing = [col for col in NUMERIC_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"数据缺少以下必需列，无法执行特征工程: {missing}")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    return df


def scale_numeric_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, StandardScaler]:
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(df[NUMERIC_COLUMNS])
    df_scaled = df.copy()
    df_scaled[NUMERIC_COLUMNS] = scaled_values
    return df_scaled, scaler


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date"].dt.month
    df["day"] = df["date"].dt.day
    df["day_of_week"] = df["date"].dt.dayofweek
    df["season"] = df["month"] % 12 // 3 + 1
    return df


def add_lag_features(df: pd.DataFrame, target_col: str = "AQI", max_lag: int = 7) -> pd.DataFrame:
    df = df.copy()
    for lag in range(1, max_lag + 1):
        df[f"{target_col}_lag_{lag}"] = (
            df.groupby("city")[target_col].shift(lag)
        )
    return df


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna(0)


def select_top_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    feature_cols = [col for col in df.columns if col not in {"city", "date", "AQI"}]
    if not feature_cols:
        raise ValueError("没有可用的特征列，无法执行 SelectKBest。")

    X = df[feature_cols]
    y = df["AQI"]
    k = min(TOP_K, X.shape[1])
    selector = SelectKBest(score_func=f_regression, k=k)
    selector.fit(X, y)
    selected_mask = selector.get_support()
    selected_features = list(X.columns[selected_mask])
    selected_df = X[selected_features]
    return selected_df, selected_features


def inverse_aqi(aqi_scaled: np.ndarray, scaler: StandardScaler) -> np.ndarray:
    """利用 scaler 的均值与方差将 AQI 从标准化尺度还原。"""
    idx = NUMERIC_COLUMNS.index("AQI")
    mean = scaler.mean_[idx]
    std = np.sqrt(scaler.var_[idx])
    return aqi_scaled * std + mean


def save_outputs(
    df_full: pd.DataFrame,
    selected_df: pd.DataFrame,
    selected_features: List[str],
    scaler: StandardScaler,
):
    ensure_output_dirs()

    processed_df = pd.concat([
        df_full[["city", "date", "AQI"]].reset_index(drop=True),
        selected_df.reset_index(drop=True),
    ], axis=1)
    processed_df.to_csv(PROCESSED_FEATURE_FILE, index=False, encoding="utf-8-sig")
    selected_df.to_csv(SELECTED_FEATURE_FILE, index=False, encoding="utf-8-sig")

    metadata = {
        "selected_features": selected_features,
        "numeric_columns": NUMERIC_COLUMNS,
        "top_k": len(selected_features),
    }
    with FEATURE_METADATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    with SCALER_FILE.open("wb") as f:
        pickle.dump({"scaler": scaler, "numeric_columns": NUMERIC_COLUMNS}, f)

    print(f"✓ 已保存处理后的特征数据到 {PROCESSED_FEATURE_FILE}")
    print(f"✓ 已保存精选特征数据到 {SELECTED_FEATURE_FILE}")
    print(f"✓ 已保存特征元数据到 {FEATURE_METADATA_FILE}")
    print(f"✓ 已保存 StandardScaler 至 {SCALER_FILE}")


def main():
    print("开始阶段 3：特征工程与预处理...")
    df_raw = load_and_prepare_data()
    df_scaled, scaler = scale_numeric_features(df_raw)
    df_with_time = add_time_features(df_scaled)
    df_with_lags = add_lag_features(df_with_time, target_col="AQI", max_lag=7)
    df_filled = fill_missing_values(df_with_lags)
    selected_df, selected_features = select_top_features(df_filled)
    save_outputs(df_filled, selected_df, selected_features, scaler)
    print("阶段 3 完成！")


if __name__ == "__main__":
    main()

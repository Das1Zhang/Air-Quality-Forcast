"""阶段 5：模型评估与预测结果保存

主要功能：
1. 读取阶段 4 的训练产物（测试集预测、模型权重、未来预测序列、Scaler）。
2. 计算测试集 MSE / R²，并绘制真实值 vs 预测值折线图。
3. 使用训练好的 LSTM 模型对每个城市最新 30 天数据进行下一日 AQI 预测，反归一化至真实尺度。
4. 汇总城市名称、预测值、历史真实 AQI，保存为 `output/predictions/AirPrediction.pkl`，供后续可视化使用。
"""

from __future__ import annotations

import io
import json
import pickle
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_squared_error, r2_score


if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


# 路径与常量
TEST_PRED_FILE = Path("output") / "models" / "test_predictions.csv"
PROCESSED_FEATURE_FILE = Path("output") / "features" / "processed_features.csv"
SCALER_FILE = Path("models") / "aqi_scaler.pkl"
MODEL_CONFIG_FILE = Path("models") / "lstm_model_config.json"
MODEL_WEIGHTS_FILE = Path("models") / "lstm_model.pth"
PREDICTION_SEQS_FILE = Path("models") / "prediction_sequences.pkl"

PLOT_FILE = Path("output") / "models" / "test_vs_pred.png"
PREDICTION_OUTPUT_DIR = Path("output") / "predictions"
PREDICTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AIR_PRED_FILE = PREDICTION_OUTPUT_DIR / "AirPrediction.pkl"


def set_chinese_font():
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


class LSTMModel(torch.nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int = 1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = torch.nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = torch.nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.size(0)
        device = x.device
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]
        out = self.fc(out)
        return out.squeeze(-1)


def ensure_inputs():
    required = [
        TEST_PRED_FILE,
        PROCESSED_FEATURE_FILE,
        SCALER_FILE,
        MODEL_CONFIG_FILE,
        MODEL_WEIGHTS_FILE,
        PREDICTION_SEQS_FILE,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("以下输入文件缺失，请先完成阶段 3/4：\n" + "\n".join(missing))


def load_scaler() -> Dict:
    with SCALER_FILE.open("rb") as f:
        scaler_data = pickle.load(f)
    scaler = scaler_data.get("scaler")
    numeric_cols = scaler_data.get("numeric_columns")
    if scaler is None or numeric_cols is None:
        raise ValueError("aqi_scaler.pkl 内容缺失 scaler 或 numeric_columns")
    return {"scaler": scaler, "numeric_columns": numeric_cols}


def inverse_aqi(values: np.ndarray, scaler_info: Dict) -> np.ndarray:
    scaler = scaler_info["scaler"]
    numeric_cols = scaler_info["numeric_columns"]
    if "AQI" not in numeric_cols:
        raise ValueError("numeric_columns 中未包含 AQI")
    idx = numeric_cols.index("AQI")
    mean = scaler.mean_[idx]
    std = np.sqrt(scaler.var_[idx])
    return values * std + mean


def evaluate_test_predictions() -> Dict[str, float]:
    df = pd.read_csv(TEST_PRED_FILE)
    if not {"true_aqi", "pred_aqi"}.issubset(df.columns):
        raise ValueError("test_predictions.csv 缺少 true_aqi / pred_aqi 列")
    y_true = df["true_aqi"].to_numpy()
    y_pred = df["pred_aqi"].to_numpy()
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    plt.figure(figsize=(10, 6))
    plt.plot(y_true, label="真实 AQI", linewidth=2)
    plt.plot(y_pred, label="预测 AQI", linewidth=2)
    plt.xlabel("样本序号")
    plt.ylabel("AQI")
    plt.title("测试集真实值 vs 预测值")
    plt.legend()
    plt.grid(alpha=0.3, linestyle="--")
    plt.tight_layout()
    plt.savefig(PLOT_FILE, dpi=300)
    plt.close()

    print(f"测试集指标：MSE={mse:.2f}, R2={r2:.4f}")
    print(f"✓ 测试集对比图已保存至 {PLOT_FILE}")

    return {"mse": float(mse), "r2": float(r2)}


def load_model(selected_features: List[str], hidden_size: int, num_layers: int, device: torch.device) -> LSTMModel:
    model = LSTMModel(
        input_size=len(selected_features),
        hidden_size=hidden_size,
        num_layers=num_layers,
    ).to(device)
    state = torch.load(MODEL_WEIGHTS_FILE, map_location=device)
    model.load_state_dict(state)
    model.eval()
    return model


def predict_next_day(model: LSTMModel, device: torch.device, scaler_info: Dict) -> Dict[str, Dict]:
    with MODEL_CONFIG_FILE.open("r", encoding="utf-8") as f:
        config = json.load(f)
    selected_features = config["selected_features"]
    time_steps = config["time_steps"]

    with PREDICTION_SEQS_FILE.open("rb") as f:
        sequences = pickle.load(f)

    predictions = {}
    with torch.no_grad():
        for item in sequences:
            city = item["city"]
            features = np.array(item["features"], dtype=np.float32)
            if features.shape != (time_steps, len(selected_features)):
                print(f"警告: {city} 的预测序列形状 {features.shape} 不满足要求，已跳过")
                continue
            tensor = torch.from_numpy(features).unsqueeze(0).to(device)
            pred_scaled = model(tensor).cpu().numpy()[0]
            pred_actual = inverse_aqi(np.array([pred_scaled]), scaler_info)[0]
            predictions[city] = {
                "pred_aqi": float(pred_actual),
                "last_date": item.get("last_date"),
            }
    return predictions


def load_processed_actual(scaler_info: Dict) -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_FEATURE_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["AQI_actual"] = inverse_aqi(df["AQI"].to_numpy(), scaler_info)
    return df


def get_latest_actual_aqi(df_actual: pd.DataFrame) -> Dict[str, float]:
    latest = df_actual.groupby("city").tail(1)
    return dict(zip(latest["city"], latest["AQI_actual"].astype(float)))


def get_history_actual_aqi(df_actual: pd.DataFrame, days: int = 90) -> Dict[str, List[float]]:
    history = {}
    for city, group in df_actual.groupby("city"):
        series = group["AQI_actual"].tolist()
        history[city] = series[-days:] if len(series) > days else series
    return history


def save_prediction_pickle(
    predictions: Dict[str, Dict],
    latest_actual: Dict[str, float],
    history_actual: Dict[str, List[float]],
) -> None:
    cities = []
    pred_values = []
    history_values = []

    for city in latest_actual.keys():
        if city in predictions:
            cities.append(city)
            pred_values.append(predictions[city]["pred_aqi"])
            history_values.append(history_actual.get(city, []))
        else:
            print(f"警告: {city} 缺少预测结果，已跳过该城市。")

    data = {
        "省市地区": cities,
        "大气质量预测": pred_values,
        "历史大气质量": history_values,
    }
    with AIR_PRED_FILE.open("wb") as f:
        pickle.dump(data, f)
    print(f"✓ 预测结果已保存至 {AIR_PRED_FILE}")


def main():
    print("开始阶段 5：模型评估与结果保存...")
    ensure_inputs()
    scaler_info = load_scaler()
    set_chinese_font()
    df_actual = load_processed_actual(scaler_info)

    metrics = evaluate_test_predictions()

    with MODEL_CONFIG_FILE.open("r", encoding="utf-8") as f:
        config = json.load(f)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(
        selected_features=config["selected_features"],
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"],
        device=device,
    )

    predictions = predict_next_day(model, device, scaler_info)
    latest_actual = get_latest_actual_aqi(df_actual)
    history_actual = get_history_actual_aqi(df_actual, days=90)
    save_prediction_pickle(predictions, latest_actual, history_actual)

    print(
        "阶段 5 完成！指标：MSE={:.2f}, R2={:.4f}".format(
            metrics["mse"], metrics["r2"]
        )
    )


if __name__ == "__main__":
    main()

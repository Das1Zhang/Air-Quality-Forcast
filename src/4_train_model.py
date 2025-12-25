"""阶段 4：LSTM 模型构建与训练

流程概述：
1. 读取阶段 3 产出（processed_features.csv + metadata）。
2. 依据 SelectKBest 的特征构造 30 天序列样本，聚合 17 城市数据。
3. 以 8:2 比例划分训练 / 测试集，使用 PyTorch LSTM 训练 200 epoch。
4. 评估指标包含缩放域 / 反归一化域的 MSE 与 R2，并保存模型与预测文件。
5. 额外保存每个城市最新 30 天序列，供阶段 5 做未来预测。

该程序代码完成人：张思浩，胡家润
"""

from __future__ import annotations

import io
import json
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


# Windows 终端输出中文兼容
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


# 常量设置
TIME_STEPS = 30
BATCH_SIZE = 32
HIDDEN_SIZE = 64
NUM_LAYERS = 2
EPOCHS = 200
LEARNING_RATE = 1e-4
TEST_SIZE = 0.2
RANDOM_STATE = 42

PROCESSED_FEATURE_FILE = Path("output") / "features" / "processed_features.csv"
FEATURE_METADATA_FILE = Path("output") / "features" / "feature_metadata.json"
SCALER_FILE = Path("models") / "aqi_scaler.pkl"

MODEL_DIR = Path("models")
MODEL_WEIGHTS_FILE = MODEL_DIR / "lstm_model.pth"
MODEL_CONFIG_FILE = MODEL_DIR / "lstm_model_config.json"
PREDICTION_SEQS_FILE = MODEL_DIR / "prediction_sequences.pkl"
METRIC_FILE = MODEL_DIR / "training_metrics.json"

OUTPUT_MODEL_DIR = Path("output") / "models"
OUTPUT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
TEST_PREDICTION_FILE = OUTPUT_MODEL_DIR / "test_predictions.csv"


@dataclass
class SequenceData:
    features: np.ndarray
    targets: np.ndarray
    cities: List[str]


class LSTMModel(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, output_size: int = 1):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.size(0)
        device = x.device
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_size, device=device)
        out, _ = self.lstm(x, (h0, c0))
        out = out[:, -1, :]
        out = self.fc(out)
        return out.squeeze(-1)


def ensure_inputs_exist():
    if not PROCESSED_FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"未找到 {PROCESSED_FEATURE_FILE}，请先运行 src/3_feature_engineering.py"
        )
    if not FEATURE_METADATA_FILE.exists():
        raise FileNotFoundError(
            f"未找到 {FEATURE_METADATA_FILE}，请先运行 src/3_feature_engineering.py"
        )
    if not SCALER_FILE.exists():
        raise FileNotFoundError(
            f"未找到 {SCALER_FILE}，请确保阶段 3 已保存 StandardScaler"
        )


def load_data() -> Tuple[pd.DataFrame, List[str]]:
    ensure_inputs_exist()
    processed_df = pd.read_csv(PROCESSED_FEATURE_FILE)
    processed_df["date"] = pd.to_datetime(processed_df["date"])
    processed_df = processed_df.sort_values(["city", "date"]).reset_index(drop=True)

    with FEATURE_METADATA_FILE.open("r", encoding="utf-8") as f:
        metadata = json.load(f)
    selected_features = metadata.get("selected_features")
    if not selected_features:
        raise ValueError("metadata 中未找到 selected_features")

    missing = [col for col in selected_features if col not in processed_df.columns]
    if missing:
        raise ValueError(f"处理后的数据缺少以下精选特征列: {missing}")

    return processed_df, selected_features


def load_scaler() -> Dict[str, np.ndarray]:
    with SCALER_FILE.open("rb") as f:
        scaler_data = pickle.load(f)
    scaler_obj = scaler_data.get("scaler")
    numeric_cols = scaler_data.get("numeric_columns")
    if scaler_obj is None or numeric_cols is None:
        raise ValueError("Scaler 数据格式不正确，缺少 scaler 或 numeric_columns")
    return {"scaler": scaler_obj, "numeric_columns": numeric_cols}


def inverse_aqi(values: np.ndarray, scaler_info: Dict[str, np.ndarray]) -> np.ndarray:
    scaler = scaler_info["scaler"]
    numeric_cols = scaler_info["numeric_columns"]
    if "AQI" not in numeric_cols:
        raise ValueError("numeric_columns 中未包含 AQI，无法反归一化")
    idx = numeric_cols.index("AQI")
    mean = scaler.mean_[idx]
    std = np.sqrt(scaler.var_[idx])
    return values * std + mean


def create_sequences(
    df: pd.DataFrame, feature_cols: List[str], time_steps: int
) -> Tuple[SequenceData, List[Dict]]:
    sequences: List[np.ndarray] = []
    targets: List[np.ndarray] = []
    city_labels: List[str] = []
    prediction_sequences: List[Dict] = []

    for city, group in df.groupby("city"):
        group = group.sort_values("date")
        feature_array = group[feature_cols].to_numpy(dtype=np.float32)
        target_array = group["AQI"].to_numpy(dtype=np.float32)

        if len(group) <= time_steps:
            print(f"警告: {city} 数据量不足以构建 {time_steps} 天序列，已跳过预测输入。")
            continue

        for i in range(len(group) - time_steps):
            seq_x = feature_array[i : i + time_steps]
            seq_y = target_array[i + time_steps]
            sequences.append(seq_x)
            targets.append(seq_y)
            city_labels.append(city)

        # 保存未来预测所需的最后 time_steps 天特征
        pred_seq = feature_array[-time_steps:]
        prediction_sequences.append(
            {
                "city": city,
                "features": pred_seq,
                "last_date": group["date"].iloc[-1].isoformat(),
            }
        )

    if not sequences:
        raise ValueError("未能生成任何序列，请检查输入数据量是否充足。")

    seq_data = SequenceData(
        features=np.stack(sequences),
        targets=np.array(targets, dtype=np.float32),
        cities=city_labels,
    )
    return seq_data, prediction_sequences


def build_dataloaders(features: np.ndarray, targets: np.ndarray) -> Tuple[DataLoader, DataLoader, np.ndarray, np.ndarray]:
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        targets,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        shuffle=True,
    )

    train_dataset = TensorDataset(
        torch.from_numpy(X_train).float(), torch.from_numpy(y_train).float()
    )
    test_dataset = TensorDataset(
        torch.from_numpy(X_test).float(), torch.from_numpy(y_test).float()
    )

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    return train_loader, test_loader, y_train, y_test


def train_model(model: nn.Module, train_loader: DataLoader, device: torch.device) -> None:
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    model.train()
    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * batch_x.size(0)

        epoch_loss /= len(train_loader.dataset)
        if epoch % 20 == 0 or epoch == 1:
            print(f"Epoch {epoch:03d}/{EPOCHS} - Train MSE: {epoch_loss:.6f}")


def evaluate_model(
    model: nn.Module,
    test_loader: DataLoader,
    device: torch.device,
    scaler_info: Dict[str, np.ndarray],
) -> Dict[str, float]:
    model.eval()
    preds = []
    trues = []
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            outputs = model(batch_x)
            preds.append(outputs.cpu().numpy())
            trues.append(batch_y.cpu().numpy())

    y_pred = np.concatenate(preds)
    y_true = np.concatenate(trues)

    mse_scaled = mean_squared_error(y_true, y_pred)
    r2_scaled = r2_score(y_true, y_pred)

    y_pred_actual = inverse_aqi(y_pred, scaler_info)
    y_true_actual = inverse_aqi(y_true, scaler_info)
    mse_actual = mean_squared_error(y_true_actual, y_pred_actual)
    r2_actual = r2_score(y_true_actual, y_pred_actual)

    metrics = {
        "mse_scaled": float(mse_scaled),
        "r2_scaled": float(r2_scaled),
        "mse_actual": float(mse_actual),
        "r2_actual": float(r2_actual),
    }
    return metrics, y_true_actual, y_pred_actual


def save_artifacts(
    model: nn.Module,
    metrics: Dict[str, float],
    config: Dict,
    prediction_sequences: List[Dict],
    y_true_actual: np.ndarray,
    y_pred_actual: np.ndarray,
) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    torch.save(model.state_dict(), MODEL_WEIGHTS_FILE)
    with MODEL_CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    with METRIC_FILE.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    with PREDICTION_SEQS_FILE.open("wb") as f:
        pickle.dump(prediction_sequences, f)

    pd.DataFrame(
        {
            "true_aqi": y_true_actual,
            "pred_aqi": y_pred_actual,
        }
    ).to_csv(TEST_PREDICTION_FILE, index=False, encoding="utf-8-sig")

    print(f"✓ 模型权重已保存到 {MODEL_WEIGHTS_FILE}")
    print(f"✓ 训练配置已保存到 {MODEL_CONFIG_FILE}")
    print(f"✓ 指标已保存到 {METRIC_FILE}")
    print(f"✓ 测试集预测已保存到 {TEST_PREDICTION_FILE}")
    print(f"✓ 未来预测序列已保存到 {PREDICTION_SEQS_FILE}")


def main():
    print("开始阶段 4：LSTM 模型训练...")
    processed_df, selected_features = load_data()
    scaler_info = load_scaler()

    seq_data, prediction_sequences = create_sequences(
        processed_df, selected_features, TIME_STEPS
    )

    train_loader, test_loader, _, _ = build_dataloaders(
        seq_data.features, seq_data.targets
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LSTMModel(
        input_size=len(selected_features),
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
    ).to(device)

    train_model(model, train_loader, device)
    metrics, y_true_actual, y_pred_actual = evaluate_model(
        model, test_loader, device, scaler_info
    )

    config = {
        "time_steps": TIME_STEPS,
        "batch_size": BATCH_SIZE,
        "hidden_size": HIDDEN_SIZE,
        "num_layers": NUM_LAYERS,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "selected_features": selected_features,
        "device": str(device),
    }

    save_artifacts(
        model,
        metrics,
        config,
        prediction_sequences,
        y_true_actual,
        y_pred_actual,
    )

    print("阶段 4 已完成！")
    print(
        f"测试集指标（实际 AQI）：MSE={metrics['mse_actual']:.2f}, R2={metrics['r2_actual']:.4f}"
    )


if __name__ == "__main__":
    main()

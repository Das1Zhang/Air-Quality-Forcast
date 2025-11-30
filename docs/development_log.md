# 开发日志

## 2025-11-21

### 阶段 0：项目结构整理
- 整理仓库结构，创建 `src/`, `src/utils/`, `models/`, `docs/`, `tools/` 等目录，确保与 README 规划一致。
- 将 `step1_data_merging.py` 移动至 `src/1_data_process.py`，统一脚本命名与分层。
- 将环境/工具类脚本集中至 `tools/`（如 `check_dependencies.py`），保持根目录整洁。

### 阶段 1：数据整合
- 脚本：`src/1_data_process.py`。
- 主要工作：
  - 读取 `data/` 下 17 个城市 Excel（缺失文件会提示）。
  - 支持多种列名映射，按时间正序合并。
  - 输出合并结果 `data/AirCondition.csv`，并在控制台打印总览与各城市记录数。
- 输出：`data/AirCondition.csv`（同时可复制到 `output/merged_data/` 使用）。

### 阶段 2：探索性数据分析（EDA）
- 脚本：`src/2_eda.py`。
- 主要工作：
  - 自动定位合并后的 `AirCondition.csv`，转换日期类型并按城市排序。
  - 统计各城市 AQI 均值并输出 `output/eda/city_aqi_mean.csv`。
  - 绘制最近 90 天所有城市 AQI 折线图，X 轴按月份刻度，输出 `output/eda/aqi_trend_90days.png`。
  - 绘制污染物与 AQI 的相关性热力图，输出 `output/eda/aqi_correlation_heatmap.png`。
- 运行命令：`python src/2_eda.py`。

### 阶段 3：特征工程与预处理
- 脚本：`src/3_feature_engineering.py`。
- 主要工作：
  - 读取合并后的 `AirCondition.csv`，进行日期排序与空值检查。
  - 使用 `StandardScaler` 对 `PM2.5~AQI` 数值列归一化，并保留 scaler 以备反归一化。
  - 构造时间特征（month/day/day_of_week/season）和 AQI_lag_1~7 滞后特征。
  - 将新增特征与数值列进行缺失值填充（0），使用 `SelectKBest(f_regression, k=10)` 选择最优特征。
  - 输出完整特征集与精选特征，并保存 scaler/元数据。
- 产出文件：
  - `output/features/processed_features.csv`
  - `output/features/selected_features.csv`
  - `output/features/feature_metadata.json`
  - `models/aqi_scaler.pkl`
- 运行命令：`python src/3_feature_engineering.py`。

### 阶段 4：LSTM 模型构建与训练
- 脚本：`src/4_train_model.py`。
- 主要工作：
  - 读取阶段 3 产出的精选特征，生成 30 天时间序列样本。
  - 按 8:2 划分训练/测试集，构建两层 LSTM（hidden_size=64）训练 200 epoch。
  - 计算标准化域与反归一化域的 MSE、R²，并保存测试预测结果。
  - 将模型权重、配置、训练指标与未来预测序列写入 `models/` 目录。
- 产出文件：
  - `models/lstm_model.pth`
  - `models/lstm_model_config.json`
  - `models/training_metrics.json`
  - `models/prediction_sequences.pkl`
  - `output/models/test_predictions.csv`
- 运行命令：`python src/4_train_model.py`。

### 阶段 5：模型评估与预测保存
- 脚本：`src/5_evaluate_predict.py`。
- 主要工作：
  - 读取测试集预测、模型权重、未来预测序列以及 scaler。
  - 计算真实 AQI 域的 MSE / R²，并绘制“真实 vs 预测”折线图。
  - 加载 LSTM 模型，对各城市最近 30 天数据预测下一日 AQI，并反归一化。
  - 将城市、预测值、历史真实 AQI 整理为字典并保存，供阶段 6 可视化。
- 产出文件：
  - `output/models/test_vs_pred.png`
  - `output/predictions/AirPrediction.pkl`
- 运行命令：`python src/5_evaluate_predict.py`。

### 阶段 6：预测结果可视化
- 脚本：`src/6_visualize.py`。
- 主要工作：
  - 读取阶段 5 生成的 `AirPrediction.pkl`，绘制 17 个城市历史 AQI + 预测值折线子图。
  - 使用 `map_visualization_helper` 生成湖北省预测热力图（若地图包缺失则自动降级到中国地图或柱状图）。
  - 输出最终可视化文件，供展示与汇报使用。
- 产出文件：
  - `output/visualization/AirPrediction.png`
  - `output/visualization/map_hubei.html`
- 运行命令：`python src/6_visualize.py`。

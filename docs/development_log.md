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

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

## 2025-12-01

### 阶段 7：Web 前端工作台与 Flask API 集成
- 新增前端界面：
  - 创建 `webui/index.html`、`webui/styles.css`、`webui/app.js`，采用 “Monet's Garden” 主题配色，实现：
    - 选择单个市区并上传对应 `.xlsx` 数据文件至暂存区。
    - 触发“训练并预测”按钮，调用后端 API 执行完整的 1~6 阶段流水线。
    - 通过“刷新状态”按钮轮询阶段状态，展示各阶段输出文件的链接（如 EDA 图、测试集对比图、湖北热力图）。
- 新增后端服务：
  - 增加 `server.py`（Flask），提供：
    - `POST /api/upload`：接收前端上传的单个文件和城市名，将其保存为 `data/历史日数据_{city}.xlsx`，与 `src/1_data_process.py` 的读取逻辑保持一致。
    - `POST /api/run_pipeline`：在项目根目录下依次运行 `src/1_data_process.py` ~ `src/6_visualize.py`，完成数据整合、EDA、特征工程、训练、评估与可视化。
    - `GET /api/status`：返回各阶段的简要状态与主要输出文件路径，用于前端展示。
- 数据与模型文件管理：
  - 为避免在仓库中暴露本地训练产物和地图缓存数据，将以下文件类型加入 `.gitignore`：
    - `resources/geo/*.geojson`（城市级 GeoJSON 缓存）。
    - `models/*.pkl`, `models/*.json`, `models/*.pth`, `models/*.pt`, `models/*.h5`, `models/*.model` 等模型与中间结果文件。
  - 使用 `git rm --cached` 将原有已跟踪的模型中间文件从版本库中移除，同时保留本地文件，确保他人在克隆仓库后可通过重新运行阶段 3~6 生成所需模型与预测结果。

## 2025-12-03

### Docker 化与 Web 工作台完善
- Docker 支持：
  - 编写 `Dockerfile`，基于官方 `pytorch/pytorch:latest` 镜像，预装 PyTorch 及项目依赖，便于在无本地 Python 环境的机器上快速运行完整流水线。
  - 提取 Docker 专用依赖文件 `requirements-docker.txt`（不包含 `torch`），避免在容器内重复安装 PyTorch，缩短构建时间。
  - 在镜像构建过程中安装中文字体 `fonts-wqy-zenhei`，并在 `src/2_eda.py`、`src/5_evaluate_predict.py`、`src/6_visualize.py` 中统一优先使用 `WenQuanYi Zen Hei`，解决容器内生成图表中文显示为方块的问题。
- Web 工作台与 API 完善：
  - 在 `server.py` 中新增：
    - 根路由 `/`，直接返回 `webui/index.html`，方便通过 `http://localhost:5000` 访问前端工作台。
    - 静态资源路由 `/styles.css` 与 `/app.js`，确保前端样式与脚本在容器环境下可正常加载。
    - 输出文件路由 `/output/<path:subpath>`，统一对外暴露 `output/` 目录下的 EDA 图、模型评估图和湖北地图 HTML，可通过 Web UI 的“查看输出”按钮直接访问。
  - 调整前端 `webui/app.js`：
    - 将 `API_BASE` 从硬编码的 `http://localhost:5000` 改为相对路径 `""`，避免在 Docker 环境中因端口映射差异导致 `TypeError: Failed to fetch` 问题。
    - 保持 `/api/upload`、`/api/run_pipeline`、`/api/status` 的调用逻辑不变，在本机与容器中实现一致的行为。
- Docker 运行与数据持久化：
  - 通过 README 中新增的 Docker 使用说明，整理了镜像构建、端口映射以及挂载 `data/` 目录的推荐命令，支持用户在容器中通过 Web UI 上传 Excel 并将数据持久化到宿主机。
  - 在说明文档中明确标注了 Docker 镜像体积较大（约 10GB）以及首构建/首次拉取的时间成本，便于使用者提前规划磁盘与网络资源。


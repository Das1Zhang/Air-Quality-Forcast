# 基于 LSTM 的湖北省空气质量预测系统

基于机器学习（LSTM 神经网络）的湖北省各主要城市空气质量指数（AQI）时间序列分析与预测系统。

## 项目概述

本项目利用深度学习技术对湖北省17个主要城市的空气质量进行预测，涵盖数据获取、预处理、特征工程、模型构建（PyTorch）、模型评估以及可视化（Matplotlib 和 Pyecharts）全流程。想了解阶段性进展，可直接查看[开发日志](docs/development_log.md)。

## 技术栈

- **Python 3.x**
- **数据处理**: `pandas`, `numpy`
- **可视化**: `matplotlib`, `seaborn`, `pyecharts`
- **机器学习/深度学习**: `sklearn`, `torch` (PyTorch)
- **其他**: `pickle`, `openpyxl`

## 环境配置

### 方式一：使用 Conda（推荐，特别是使用 miniconda/anaconda）

#### 1. 创建并激活 conda 环境

```bash
# 使用 environment.yml 创建环境（推荐）
conda env create -f environment.yml

# 激活环境
conda activate air-quality-forecast
```

#### 2. 如果使用 environment.yml 创建环境，依赖已自动安装

如果需要手动安装，可以：

```bash
# 使用 conda 安装主要依赖（PyTorch 建议用 conda 安装）
conda install pytorch pandas numpy matplotlib seaborn scikit-learn openpyxl -c pytorch -c conda-forge

# 使用 pip 安装 PyEcharts 相关包
pip install pyecharts echarts-china-provinces-pypkg echarts-china-cities-pypkg
```

### 方式二：使用 pip（普通 Python 环境）

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 地图包（可选）

**地图包为可选依赖**，如果安装失败不影响项目运行。项目已提供替代可视化方案。

**尝试安装地图包**（可选）：

```bash
# 使用安装脚本
python install_echarts_maps.py
```

或者手动安装：

```bash
# 先安装构建依赖
pip install pyecharts-jupyter-installer

# 再安装地图包
pip install echarts-china-provinces-pypkg echarts-china-cities-pypkg
```

**如果地图包安装失败**（这是常见情况）：
- ✅ **项目仍可正常运行**，所有核心功能（数据处理、模型训练等）不受影响
- ✅ **已提供替代可视化方案**：使用 `map_visualization_helper.py` 可以：
  - 尝试使用 PyEcharts 内置地图
  - 使用 matplotlib 创建柱状图可视化
  - 生成文本报告作为备选
- 📖 详细说明请参考 `install_maps_alternative.md`

### 检查并安装缺失的依赖

如果你已经有一个 conda 环境（如 `air_quality`），可以使用依赖检查工具：

```bash
# 激活你的环境
conda activate air_quality

# 运行依赖检查脚本
python check_dependencies.py
```

该脚本会：
- 检查 `requirements.txt` 中列出的所有包
- 显示哪些已安装，哪些缺失
- 提供安装命令或自动安装缺失的包

### 环境管理提示

- **Conda 用户**：建议使用 `environment.yml` 创建独立环境，避免与系统 Python 环境冲突
- **激活环境**：每次使用前记得激活 conda 环境：`conda activate air_quality`（或你的环境名）
- **退出环境**：使用完毕后可以退出：`conda deactivate`
- **检查依赖**：使用 `check_dependencies.py` 快速检查环境配置

## 数据准备

1. 从湖北省生态环境厅获取数据：访问 [https://sthjt.hubei.gov.cn/hjsj/](https://sthjt.hubei.gov.cn/hjsj/)
2. 下载湖北省各地级市最近89天的数据，导出为 Excel 格式
3. 将数据文件放入 `data/` 目录，命名格式为：`历史日数据_{城市名}.xlsx`

### 城市列表

包含以下17个城市：
- 武汉市、黄石市、十堰市、宜昌市、襄阳市、鄂州市
- 荆门市、孝感市、荆州市、黄冈市、咸宁市、随州市
- 恩施土家族苗族自治州、仙桃市、潜江市、天门市、神农架林区

## 使用步骤

### 步骤 1：数据整合

运行数据整合脚本，将所有城市的数据合并为一个 CSV 文件：

```bash
python src/1_data_process.py
```

该脚本会：
- 读取 `data/` 目录下所有城市的 Excel 文件
- 按时间正序排列数据
- 提取所需列：`city`, `date`, `PM2.5`, `PM10`, `O3`, `SO2`, `NO2`, `CO`, `AQI`
- 生成 `data/AirCondition.csv`（可复制到 `output/merged_data/` 使用）

### 步骤 2：探索性数据分析（EDA）

```bash
python src/2_eda.py
```

输出：
- 城市 AQI 均值表：`output/eda/city_aqi_mean.csv`
- 最近 90 天 AQI 趋势图：`output/eda/aqi_trend_90days.png`
- 污染物与 AQI 相关性热力图：`output/eda/aqi_correlation_heatmap.png`

### 步骤 3：特征工程与预处理

```bash
python src/3_feature_engineering.py
```

主要流程：
- 日期转换、StandardScaler 归一化
- 构造月/日/星期/季节特征
- 生成 AQI_lag_1 ~ AQI_lag_7 滞后特征
- 填充缺失值（0），并用 SelectKBest 选出前 10 个特征

输出：
- `output/features/processed_features.csv`
- `output/features/selected_features.csv`
- `output/features/feature_metadata.json`
- `models/aqi_scaler.pkl`

### 步骤 4：LSTM 模型构建与训练

```
python src/4_train_model.py
```

主要流程：
- 使用阶段 3 的精选特征构造 30 天序列样本
- 按 8:2 划分训练/测试集，训练两层 LSTM（hidden_size=64, epochs=200）
- 在标准化域与反归一化域分别计算 MSE、R²
- 保存模型权重、配置、测试集预测以及未来预测所需序列

输出：
- `models/lstm_model.pth`
- `models/lstm_model_config.json`
- `models/training_metrics.json`
- `models/prediction_sequences.pkl`
- `output/models/test_predictions.csv`

### 步骤 5：模型评估与预测保存

```
python src/5_evaluate_predict.py
```

主要流程：
- 根据阶段 4 的测试集预测计算真实域 MSE/R²，并生成“真实 vs 预测”折线图
- 加载 LSTM 模型与未来预测序列，对 17 个城市进行下一日 AQI 预测
- 反归一化预测结果，整理成 `AirPrediction.pkl` 供阶段 6 可视化

输出：
- `output/models/test_vs_pred.png`
- `output/predictions/AirPrediction.pkl`
- 控制台打印最新评估指标

### 步骤 6：预测结果可视化

```
python src/6_visualize.py
```

主要流程：
- 读取 `AirPrediction.pkl`，绘制 17 个城市的历史 AQI + 预测值子图
- 调用 `map_visualization_helper` 生成湖北省预测热力图（若地图包缺失则自动降级）

输出：
- `output/visualization/AirPrediction.png`
- `output/visualization/map_hubei.html`

### 后续步骤

- 阶段 1~6 已实现；如需改进模型、替换可视化或撰写汇报，可在此基础上继续拓展。

## 项目结构

```
Air-Quality-Forcast/
├── data/                          # 数据目录（存放各城市原始 Excel 文件）
│   ├── 历史日数据_武汉市.xlsx
│   ├── 历史日数据_黄石市.xlsx
│   └── ...
├── output/                        # 输出目录（按功能分类存放生成的文件）
│   ├── merged_data/               # 合并数据：步骤1数据整合输出
│   │   └── AirCondition.csv       # 合并后的数据文件
│   ├── eda/                       # 数据探索：步骤2 EDA 分析输出
│   │   └── （可视化图表、统计报告）
│   ├── features/                  # 特征工程：步骤3特征处理输出
│   │   └── （处理后的特征数据）
│   ├── models/                    # 模型训练：步骤4模型训练输出
│   │   └── （模型权重、训练日志）
│   ├── predictions/               # 预测结果：步骤5模型评估输出
│   │   └── AirPrediction.pkl      # 预测结果文件
│   └── visualization/             # 可视化：步骤6最终可视化输出
│       └── map_hubei.html         # 地图可视化
├── src/                           # 核心脚本目录（1~4 阶段）
│   ├── 1_data_process.py
│   ├── 2_eda.py
│   ├── 3_feature_engineering.py
│   └── ...
├── tools/                         # 辅助脚本（依赖检查等）
│   └── check_dependencies.py
├── requirements.txt               # Python 依赖包列表（pip 安装）
├── environment.yml                # Conda 环境配置文件（推荐）
└── README.md                      # 项目说明文档
```

## 注意事项

1. 确保数据文件命名格式正确：`历史日数据_{城市名}.xlsx`
2. 数据文件应包含必需的列：`city`, `date`, `PM2.5`, `PM10`, `O3`, `SO2`, `NO2`, `CO`, `AQI`
3. 如果运行地图可视化报错，请确保已安装地图包（见环境配置部分）

## 许可证

本项目用于 WHU Python 课程 25fall。

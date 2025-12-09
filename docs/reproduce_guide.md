# 项目复现与快速体验指南

本文档面向最终使用者，帮助在最少配置的情况下快速复现本项目的空气质量预测流程。

---

## 一、使用 Docker 快速体验（推荐）

适合：不想配置 Python 环境，只需快速跑一遍完整流程的用户。

### 1. 前置条件

- 操作系统：Linux / macOS / Windows 均可  
- 已安装 Docker（建议 Docker Engine ≥ 20）

验证 Docker 是否可用：

```bash
docker version
```

能正常显示版本信息即可。

### 2. 拉取镜像

镜像已发布在 Docker Hub：

```bash
docker pull das1jason/air-quality-forecast:latest
```

> 首次拉取镜像约 10GB，时间取决于网络带宽。

### 3. 启动容器

在任意目录执行：

```bash
docker run -d --name air-quality \
  -p 5000:5000 \
  -v "$(pwd)/data:/app/data" \
  das1jason/air-quality-forecast:latest
```

说明：

- `-p 5000:5000`：将容器内 5000 端口映射到本机 5000 端口。
- `-v "$(pwd)/data:/app/data"`：
  - 宿主机当前目录下的 `data/` 作为数据目录。
  - 通过 Web 页面上传的 Excel 会保存到这个目录中，容器重启后不会丢失。

Windows PowerShell 下可写成：

```powershell
docker run -d --name air-quality `
  -p 5000:5000 `
  -v "${PWD}/data:/app/data" `
  das1jason/air-quality-forecast:latest
```

查看容器是否运行：

```bash
docker ps
```

应能看到 `air-quality` 状态为 `Up`，并有 `0.0.0.0:5000->5000/tcp` 映射。

### 4. 打开 Web 工作台

浏览器访问：

```text
http://localhost:5000
```

可见一个 Web 页面，包含：

- 数据上传区域
- 各阶段卡片（阶段 1–6）
- 控制台输出区域
- 查看项目流程图 / LSTM 原理图按钮

### 5. 通过 Web 工作台完成一次完整流程

1. **准备数据**

   - 用户需从湖北省生态环境厅网站下载 Excel 数据，或使用自有格式但字段兼容。
   - 单个城市的文件命名：`历史日数据_城市名.xlsx`  
     例如：`历史日数据_武汉市.xlsx`

2. **上传数据文件**

   在页面中：

   - 从下拉框选择「市区」（如“武汉市”）。
   - 将对应城市的 Excel 拖拽到上传区域。
   - 点击「上传到暂存区」，等待控制台提示“上传完成”。
   - 如需多城市训练，可对其他城市重复上述步骤。

3. **启动训练与预测**

   - 点击「训练并预测」按钮。
   - 后端会自动顺序执行：
     `1_data_process.py → 2_eda.py → 3_feature_engineering.py → 4_train_model.py → 5_evaluate_predict.py → 6_visualize.py`
   - 控制台会实时打印每个阶段的进度与日志。

4. **查看各阶段输出**

   - 训练完成后，点击「刷新状态」按钮。
   - 在阶段卡片底部可以看到“输出”区域的链接：
     - **阶段 2（EDA）**：
       - 城市 AQI 均值表（CSV）
       - 最近 90 天 AQI 趋势图
       - 污染物与 AQI 相关性热力图  
         （说明：该热力图是基于所有城市合并后的整体相关性）
     - **阶段 5：评估与预测**：
       - 测试集真实 vs 预测折线图
     - **阶段 6：可视化展示**：
       - 汇总折线图（全省 17 城市历史 + 预测）
       - 湖北省 AQI 预测热力图（HTML）

5. **停止容器（可选）**

如需停止服务：

```bash
docker stop air-quality
```

如需删除容器：

```bash
docker rm air-quality
```

镜像仍保留在本机，可以随时重新 `docker run` 启动。

---

## 二、在 VPS 上部署（可选）

适合：希望对外长期提供在线访问的场景。

### 1. 基本思路

在 VPS 上执行：

1. 安装 Docker。
2. 从 Docker Hub 拉取镜像，启动容器映射到 `localhost:5000`。
3. 使用 Cloudflare Tunnel 或 Nginx + 域名，将 `http://localhost:5000` 暴露为公网地址。

### 2. 核心命令示例（以 Ubuntu 为例）

```bash
# 安装 Docker（如已安装可跳过）
sudo apt update
sudo apt install -y docker.io

# 拉取镜像
docker pull das1jason/air-quality-forecast:latest

# 准备数据目录
mkdir -p ~/air-quality-data

# 启动容器
docker run -d --name air-quality \
  -p 5000:5000 \
  -v ~/air-quality-data:/app/data \
  das1jason/air-quality-forecast:latest
```

此后：

- 在 VPS 上 `curl http://localhost:5000` 应该能看到 HTML。
- 再按既有的域名方案（如 Cloudflare Tunnel）将 `http://localhost:5000` 暴露为 `https://<你的域名>` 即可。

---

## 三、直接使用本地 Python 环境复现（非 Docker）

如果不想使用 Docker，也可以按如下方式直接复现：

1. 安装 Conda 或 Python 3.10+。
2. 克隆项目代码：

   ```bash
   git clone https://github.com/Das1Zhang/Air-Quality-Forcast.git
   cd Air-Quality-Forcast
   ```

3. 使用 Conda 创建环境并安装依赖：

   ```bash
   conda env create -f environment.yml
   conda activate air-quality-forecast
   ```

   或者使用 pip：

   ```bash
   pip install -r requirements.txt
   ```

4. 直接启动 Web 工作台：

   ```bash
   python server.py
   ```

5. 浏览器访问：

   ```text
   http://localhost:5000
   ```

   后续操作（上传数据、训练与预测、查看阶段输出）与 Docker 方式完全一致。

# 使用官方 PyTorch 镜像（默认包含 CUDA，可在 CPU 上运行）
FROM pytorch/pytorch:latest

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装中文字体，避免 matplotlib 中文显示为方块
RUN apt-get update && \
    apt-get install -y --no-install-recommends fonts-wqy-zenhei && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-docker.txt ./requirements-docker.txt
RUN pip install --no-cache-dir -r requirements-docker.txt \
    && pip install --no-cache-dir flask flask-cors

# 再复制整个项目
COPY . .

# 容器内暴露的端口：
# 8080: 静态前端 (python -m http.server)
# 5000: Flask API (server.py)
EXPOSE 8080 5000

# 默认启动两个服务：
# - http://localhost:8080/webui/index.html   前端页面
# - http://localhost:5000/api/...           后端 API
CMD sh -c "python -m http.server 8080 & python server.py"
from pathlib import Path
import subprocess
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # 允许前端跨域访问

app = Flask(__name__)
CORS(app)  # 默认允许所有源，简单起步用

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

@app.get("/reproduce")
def reproduce_page():
    """复现指南页面：返回 webui/reproduce.html"""
    webui_dir = ROOT_DIR / "webui"
    return send_from_directory(webui_dir, "reproduce.html")

@app.get("/docs/<path:subpath>")
def docs_files(subpath: str):
    """提供 docs 目录下的静态文档文件（如 Markdown 复现指南）。"""
    docs_dir = ROOT_DIR / "docs"
    return send_from_directory(docs_dir, subpath)

@app.get("/")
def index_page():
    """返回前端主页面 webui/index.html"""
    webui_dir = ROOT_DIR / "webui"
    return send_from_directory(webui_dir, "index.html")

@app.get("/styles.css")
def styles_css():
    """提供前端样式表 webui/styles.css"""
    webui_dir = ROOT_DIR / "webui"
    return send_from_directory(webui_dir, "styles.css")

@app.get("/app.js")
def app_js():
    """提供前端脚本 webui/app.js"""
    webui_dir = ROOT_DIR / "webui"
    return send_from_directory(webui_dir, "app.js")

@app.get("/output/<path:subpath>")
def output_files(subpath: str):
    """提供 output 目录下的静态文件，如图表和地图 HTML。"""
    output_dir = ROOT_DIR / "output"
    return send_from_directory(output_dir, subpath)

@app.post("/api/upload")
def api_upload():
    """
    接收前端上传的单个文件 + city，保存为 data/历史日数据_{city}.xlsx
    """
    city = request.form.get("city")
    file = request.files.get("file")

    if not city or not file:
        return jsonify({"ok": False, "msg": "缺少 city 或 file"}), 400

    filename = f"历史日数据_{city}.xlsx"
    save_path = DATA_DIR / filename
    file.save(save_path)

    return jsonify({"ok": True, "city": city, "path": str(save_path)})


@app.post("/api/run_pipeline")
def api_run_pipeline():
    """
    串行运行阶段 1~6 的脚本。
    简单版本：阻塞直到全部完成。
    """
    cmds = [
        ["python", "src/1_data_process.py"],
        ["python", "src/2_eda.py"],
        ["python", "src/3_feature_engineering.py"],
        ["python", "src/4_train_model.py"],
        ["python", "src/5_evaluate_predict.py"],
        ["python", "src/6_visualize.py"],
    ]
    for cmd in cmds:
        # 在项目根目录下运行
        subprocess.run(cmd, check=True, cwd=ROOT_DIR)

    return jsonify({"ok": True})


@app.get("/api/status")
def api_status():
    """
    简化版状态接口：先写死为“已完成”，
    后续可以根据是否存在对应输出文件来动态判断。
    """
    def exists(rel_path: str) -> bool:
        return (ROOT_DIR / rel_path).exists()

    # 阶段二：汇总多个输出文件（如果存在）
    stage2_outputs = []
    if exists("output/eda/aqi_trend_90days.png"):
        stage2_outputs.append({
            "label": "AQI 趋势图",
            "path": "output/eda/aqi_trend_90days.png",
        })
    if exists("output/eda/aqi_correlation_heatmap.png"):
        stage2_outputs.append({
            "label": "相关性热力图",
            "path": "output/eda/aqi_correlation_heatmap.png",
        })
    if exists("output/eda/city_aqi_mean.csv"):
        stage2_outputs.append({
            "label": "城市 AQI 均值表 (CSV)",
            "path": "output/eda/city_aqi_mean.csv",
        })

    return jsonify({
        "stage1": {"status": "success", "text": "完成", "output": None},
        "stage2": {
            "status": "success",
            "text": "完成",
            "output": stage2_outputs or None,
        },
        "stage3": {"status": "success", "text": "完成", "output": None},
        "stage4": {"status": "success", "text": "完成", "output": None},
        "stage5": {"status": "success", "text": "完成",
                   "output": "output/models/test_vs_pred.png" if exists("output/models/test_vs_pred.png") else None},
        "stage6": {"status": "success", "text": "完成",
                   "output": "output/visualization/map_hubei.html" if exists("output/visualization/map_hubei.html") else None},
    })


if __name__ == "__main__":
    # 在 5000 端口启动 API 服务
    app.run(host="0.0.0.0", port=5000, debug=True)
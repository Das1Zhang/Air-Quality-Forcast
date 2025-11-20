# PyEcharts 地图包安装问题解决方案

## 问题说明

`echarts-china-provinces-pypkg` 和 `echarts-china-cities-pypkg` 在安装时可能遇到以下错误：
- `ModuleNotFoundError: No module named 'pyecharts_jupyter_installer'`
- 构建 wheel 失败

## 解决方案

### 方案 1: 使用安装脚本（推荐）

```bash
# 激活环境
conda activate air_quality

# 运行安装脚本
python install_echarts_maps.py
```

### 方案 2: 手动安装步骤

```bash
# 1. 确保 pip 可用
python -m ensurepip --upgrade

# 2. 安装构建依赖
pip install pyecharts-jupyter-installer

# 3. 安装地图包
pip install echarts-china-provinces-pypkg
pip install echarts-china-cities-pypkg
```

### 方案 3: 使用替代方法（如果安装失败）

如果地图包无法安装，可以在代码中手动处理地图数据：

```python
from pyecharts import options as opts
from pyecharts.charts import Map

# 方法 1: 使用 pyecharts 内置地图（如果支持）
map_chart = Map()
map_chart.add("AQI", data_pair, "china")  # 使用内置的中国地图

# 方法 2: 手动注册地图（需要下载地图 JSON 文件）
# 从 https://github.com/apache/echarts/tree/master/map/json 下载湖北省地图 JSON
# 然后使用 register_map() 注册
```

### 方案 4: 跳过地图包（临时方案）

如果地图包不是必需的，可以：
1. 暂时从 `requirements.txt` 中移除这两个包
2. 使用其他可视化方式（如 matplotlib）
3. 后续再处理地图可视化

## 验证安装

运行以下代码验证：

```python
try:
    import pyecharts
    print(f"✓ pyecharts 版本: {pyecharts.__version__}")
    
    # 尝试导入地图包
    try:
        import echarts_china_provinces_pypkg
        print("✓ echarts-china-provinces-pypkg 已安装")
    except ImportError:
        print("⚠ echarts-china-provinces-pypkg 未安装（可能不影响使用）")
    
    try:
        import echarts_china_cities_pypkg
        print("✓ echarts-china-cities-pypkg 已安装")
    except ImportError:
        print("⚠ echarts-china-cities-pypkg 未安装（可能不影响使用）")
        
except ImportError:
    print("✗ pyecharts 未安装")
```


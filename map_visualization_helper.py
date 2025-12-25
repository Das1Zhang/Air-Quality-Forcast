"""
地图可视化辅助工具：在缺少省级地图包时提供多级降级方案。

该程序代码完成人：张思浩
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
from urllib.error import URLError
from urllib.request import urlopen


GEO_DIR = Path("resources/geo")
HUBEI_GEO_URL = "https://geo.datav.aliyun.com/areas_v3/bound/geojson?code=420000"
LOCAL_GEO_PATH = GEO_DIR / "hubei.geojson"

CITY_ADCODE = {
    "武汉市": 420100,
    "黄石市": 420200,
    "十堰市": 420300,
    "宜昌市": 420500,
    "襄阳市": 420600,
    "鄂州市": 420700,
    "荆门市": 420800,
    "孝感市": 420900,
    "荆州市": 421000,
    "黄冈市": 421100,
    "咸宁市": 421200,
    "随州市": 421300,
    "恩施土家族苗族自治州": 422800,
    "仙桃市": 429004,
    "潜江市": 429005,
    "天门市": 429006,
    "神农架林区": 429021,
}


def check_map_packages() -> bool:
    """检查 echarts 省级地图包是否可用。"""
    try:
        import echarts_china_provinces_pypkg  # type: ignore

        return True
    except ImportError:
        return False


def _fetch_geojson(adcode: int) -> dict | None:
    cache_path = GEO_DIR / f"{adcode}.geojson"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    url = f"https://geo.datav.aliyun.com/areas_v3/bound/geojson?code={adcode}"
    try:
        with urlopen(url, timeout=10) as resp:
            geojson_text = resp.read().decode("utf-8")
        GEO_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(geojson_text, encoding="utf-8")
        return json.loads(geojson_text)
    except (URLError, OSError, json.JSONDecodeError):
        return None


def load_hubei_geojson() -> str | None:
    """尝试本地/网络加载湖北省 GeoJSON，用于无包时注册地图。"""

    if LOCAL_GEO_PATH.exists():
        try:
            return LOCAL_GEO_PATH.read_text(encoding="utf-8")
        except Exception:
            pass

    geo = _fetch_geojson(420000)
    if geo is None:
        return None
    LOCAL_GEO_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_GEO_PATH.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
    return json.dumps(geo, ensure_ascii=False)


def build_city_geojson(city_names: Sequence[str]) -> str | None:
    features: List[dict] = []
    for city in city_names:
        adcode = CITY_ADCODE.get(city)
        if not adcode:
            continue
        geo = _fetch_geojson(adcode)
        if not geo:
            continue
        for feature in geo.get("features", []):
            props = feature.setdefault("properties", {})
            props["name"] = city
            features.append(feature)

    if not features:
        return None

    combined = {"type": "FeatureCollection", "features": features}
    return json.dumps(combined, ensure_ascii=False)


def _visual_map_opts(data_pair: Sequence[Tuple[str, float]]):
    from pyecharts import options as opts

    values = [v for _, v in data_pair if v is not None]
    if not values:
        values = [0, 100]
    return opts.VisualMapOpts(
        min_=min(values),
        max_=max(values),
        range_text=["高", "低"],
        is_calculable=True,
        range_color=["#50a3ba", "#eac736", "#d94e5d"],
    )


def create_map_with_fallback(data_pair: Sequence[Tuple[str, float]], output_file: str = "map_hubei.html") -> bool:
    """创建湖北省 AQI 热力图，自动降级到尽可能可读的方案。"""

    from pyecharts import options as opts
    from pyecharts.charts import Map

    map_available = check_map_packages()

    init_opts = opts.InitOpts(width="1200px", height="650px")

    if map_available:
        print("使用 echarts-china-provinces-pypkg 创建地图...")
        map_chart = (
            Map(init_opts=init_opts)
            .add(
                "AQI预测值",
                data_pair,
                "湖北",
                is_roam=True,
                label_opts=opts.LabelOpts(is_show=True),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图"),
                visualmap_opts=_visual_map_opts(data_pair),
            )
        )
        map_chart.render(output_file)
        print(f"✓ 地图已保存到 {output_file}")
        return True

    print("地图包不可用，尝试使用城市级 GeoJSON...")
    city_geo = build_city_geojson([name for name, _ in data_pair])
    if city_geo:
        try:
            map_chart = Map(init_opts=init_opts)
            map_chart.add_js_funcs(f"echarts.registerMap('HubeiCities', {city_geo});")
            map_chart.add(
                "AQI预测值",
                data_pair,
                "HubeiCities",
                is_roam=True,
                label_opts=opts.LabelOpts(is_show=True),
            )
            map_chart.set_global_opts(
                title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图"),
                visualmap_opts=_visual_map_opts(data_pair),
            )
            map_chart.render(output_file)
            print(f"✓ 地图已保存到 {output_file}（城市级 GeoJSON）")
            return True
        except Exception as exc:  # pragma: no cover - 极少发生
            print(f"⚠ 自定义 GeoJSON 渲染失败: {exc}")

    print("城市级 GeoJSON 不可用，尝试省级 GeoJSON...")
    geo_json = load_hubei_geojson()
    if geo_json:
        try:
            map_chart = Map(init_opts=init_opts)
            map_chart.add_js_funcs(f"echarts.registerMap('HubeiProvince', {geo_json});")
            map_chart.add(
                "AQI预测值",
                data_pair,
                "HubeiProvince",
                is_roam=True,
                label_opts=opts.LabelOpts(is_show=True),
            )
            map_chart.set_global_opts(
                title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图"),
                visualmap_opts=_visual_map_opts(data_pair),
            )
            map_chart.render(output_file)
            print(f"✓ 地图已保存到 {output_file}（省级 GeoJSON）")
            return True
        except Exception as exc:
            print(f"⚠ 省级 GeoJSON 渲染失败: {exc}")

    print("使用中国地图 fallback，并居中放大湖北区域...")
    try:
        map_chart = (
            Map(init_opts=init_opts)
            .add(
                "AQI预测值",
                data_pair,
                "china",
                is_roam=True,
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图（中国地图视图）"),
                visualmap_opts=_visual_map_opts(data_pair),
                geo_opts=opts.GeoOpts(center=[112.3, 30.6], zoom=5, scale_limit=opts.ScaleLimit(max_=8, min_=1)),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        map_chart.render(output_file)
        print(f"✓ 地图已保存到 {output_file}（使用中国地图）")
        return True
    except Exception as e:
        print(f"⚠ PyEcharts 地图创建失败: {e}")
        print("将使用 matplotlib 创建替代可视化...")
        return create_matplotlib_map(data_pair, output_file)

def create_matplotlib_map(data_pair, output_file="map_hubei_matplotlib.png"):
    """
    使用 matplotlib 创建替代的地图可视化
    创建一个柱状图或条形图展示各城市的 AQI 值
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        matplotlib.rcParams['axes.unicode_minus'] = False
        
        # 提取城市名和 AQI 值
        cities = [item[0] for item in data_pair]
        aqi_values = [item[1] for item in data_pair]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 根据 AQI 值设置颜色
        colors = []
        for aqi in aqi_values:
            if aqi <= 50:
                colors.append('#50a3ba')  # 优 - 蓝色
            elif aqi <= 100:
                colors.append('#eac736')  # 良 - 黄色
            else:
                colors.append('#d94e5d')  # 污染 - 红色
        
        bars = ax.barh(cities, aqi_values, color=colors)
        
        # 添加数值标签
        for i, (city, aqi) in enumerate(zip(cities, aqi_values)):
            ax.text(aqi + 1, i, f'{aqi:.1f}', va='center', fontsize=9)
        
        ax.set_xlabel('AQI 预测值', fontsize=12)
        ax.set_title('湖北省各城市空气质量预测', fontsize=14, fontweight='bold')
        ax.set_xlim(0, max(aqi_values) * 1.2)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 添加图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='#50a3ba', label='优 (0-50)'),
            Patch(facecolor='#eac736', label='良 (51-100)'),
            Patch(facecolor='#d94e5d', label='污染 (>100)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ 替代可视化已保存到 {output_file}")
        plt.close()
        return True
    except Exception as e:
        print(f"✗ Matplotlib 可视化创建失败: {e}")
        return False

def create_simple_text_report(data_pair, output_file="map_hubei_report.txt"):
    """
    创建简单的文本报告作为最后的备选方案
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("湖北省各城市空气质量预测报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 按 AQI 值排序
            sorted_data = sorted(data_pair, key=lambda x: x[1], reverse=True)
            
            f.write("城市名称\t\tAQI预测值\t空气质量等级\n")
            f.write("-" * 60 + "\n")
            
            for city, aqi in sorted_data:
                if aqi <= 50:
                    level = "优"
                elif aqi <= 100:
                    level = "良"
                elif aqi <= 150:
                    level = "轻度污染"
                elif aqi <= 200:
                    level = "中度污染"
                elif aqi <= 300:
                    level = "重度污染"
                else:
                    level = "严重污染"
                
                f.write(f"{city}\t\t{aqi:.2f}\t\t{level}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("注：由于地图包安装问题，使用文本报告展示结果\n")
            f.write("=" * 60 + "\n")
        
        print(f"✓ 文本报告已保存到 {output_file}")
        return True
    except Exception as e:
        print(f"✗ 文本报告创建失败: {e}")
        return False

if __name__ == "__main__":
    # 测试数据
    test_data = [
        ("武汉市", 65.5),
        ("黄石市", 58.2),
        ("十堰市", 45.3),
    ]
    
    print("测试地图可视化功能...")
    result = create_map_with_fallback(test_data)
    if not result:
        create_simple_text_report(test_data)


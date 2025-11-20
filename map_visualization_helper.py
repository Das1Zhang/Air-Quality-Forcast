"""
地图可视化辅助工具
提供不依赖 echarts-china-provinces-pypkg 的地图可视化方案
"""

def check_map_packages():
    """检查地图包是否可用"""
    map_available = False
    try:
        import echarts_china_provinces_pypkg
        map_available = True
    except ImportError:
        pass
    
    return map_available

def create_map_with_fallback(data_pair, output_file="map_hubei.html"):
    """
    创建湖北省 AQI 热力地图
    如果地图包不可用，使用替代方案
    """
    from pyecharts.charts import Map
    from pyecharts import options as opts
    
    map_available = check_map_packages()
    
    if map_available:
        # 方案 1: 使用地图包（如果可用）
        print("使用 echarts-china-provinces-pypkg 创建地图...")
        map_chart = (
            Map()
            .add(
                "AQI预测值",
                data_pair,
                "湖北",  # 使用湖北省地图
                is_roam=True,
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图"),
                visualmap_opts=opts.VisualMapOpts(
                    min_=0,
                    max_=100,
                    range_text=["高", "低"],
                    is_calculable=True,
                    range_color=["#50a3ba", "#eac736", "#d94e5d"],
                ),
            )
        )
        map_chart.render(output_file)
        print(f"✓ 地图已保存到 {output_file}")
        return True
    else:
        # 方案 2: 尝试使用内置地图
        print("地图包不可用，尝试使用替代方案...")
        try:
            # 尝试使用中国地图
            map_chart = (
                Map()
                .add(
                    "AQI预测值",
                    data_pair,
                    "china",  # 使用中国地图
                    is_roam=True,
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="湖北省空气质量预测热力地图（中国地图视图）"),
                    visualmap_opts=opts.VisualMapOpts(
                        min_=0,
                        max_=100,
                        range_text=["高", "低"],
                        is_calculable=True,
                        range_color=["#50a3ba", "#eac736", "#d94e5d"],
                    ),
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


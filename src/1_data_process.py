"""
步骤 1：数据整合
读取 data/ 目录下所有城市的 Excel 文件，合并为一个总的 CSV 文件 AirCondition.csv
"""

import pandas as pd
import os
import sys
from pathlib import Path

# 设置输出编码（Windows 兼容）
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

# 城市列表
cities = [
    "武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", 
    "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市", 
    "恩施土家族苗族自治州", "仙桃市", "潜江市", "天门市", "神农架林区"
]

# 需要提取的列（支持多种可能的列名）
column_mapping = {
    "city": ["city", "城市", "城市名称"],
    "date": ["date", "日期", "时间", "日期时间"],
    "PM2.5": ["PM2.5", "PM2_5", "pm2.5"],
    "PM10": ["PM10", "pm10"],
    "O3": ["O3", "o3", "臭氧"],
    "SO2": ["SO2", "so2", "二氧化硫"],
    "NO2": ["NO2", "no2", "二氧化氮"],
    "CO": ["CO", "co", "一氧化碳"],
    "AQI": ["AQI", "aqi", "空气质量指数"]
}

required_columns = ["city", "date", "PM2.5", "PM10", "O3", "SO2", "NO2", "CO", "AQI"]

def merge_city_data():
    """
    合并所有城市的数据文件
    """
    data_dir = Path("data")
    all_data = []
    
    print("开始读取城市数据文件...")
    
    for city in cities:
        # 构建文件路径
        filename = f"历史日数据_{city}.xlsx"
        filepath = data_dir / filename
        
        if not filepath.exists():
            print(f"警告: 未找到文件 {filename}，跳过该城市")
            continue
        
        try:
            # 读取 Excel 文件
            df = pd.read_excel(filepath)
            
            # 反转索引以按时间正序排列
            df = df.iloc[::-1].reset_index(drop=True)
            
            # 映射列名到标准列名
            column_map = {}
            for standard_col, possible_names in column_mapping.items():
                for possible_name in possible_names:
                    if possible_name in df.columns:
                        column_map[possible_name] = standard_col
                        break
            
            # 重命名列
            df = df.rename(columns=column_map)
            
            # 添加 city 列（如果不存在）
            if "city" not in df.columns:
                df["city"] = city
            else:
                df["city"] = city  # 确保使用正确的城市名
            
            # 检查必需的列
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"警告: {city} 的数据文件缺少以下列: {missing_columns}")
                print(f"      可用列: {list(df.columns)}")
            
            # 只保留需要的列（如果存在）
            available_required = [col for col in required_columns if col in df.columns]
            if not available_required:
                print(f"错误: {city} 的数据文件没有可用的必需列，跳过")
                continue
            
            df = df[available_required]
            
            all_data.append(df)
            print(f"✓ 成功读取 {city} 的数据，共 {len(df)} 条记录")
            
        except Exception as e:
            print(f"错误: 读取 {city} 的数据时出错: {str(e)}")
            continue
    
    if not all_data:
        print("错误: 没有成功读取任何城市的数据文件")
        return
    
    # 合并所有数据
    print("\n正在合并数据...")
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 确保列的顺序正确（只保留存在的列）
    available_columns = [col for col in required_columns if col in merged_df.columns]
    merged_df = merged_df[available_columns]
    
    # 保存为 CSV
    output_file = data_dir / "AirCondition.csv"
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✓ 数据合并完成！")
    print(f"  - 总记录数: {len(merged_df)}")
    print(f"  - 城市数量: {merged_df['city'].nunique()}")
    print(f"  - 日期范围: {merged_df['date'].min()} 至 {merged_df['date'].max()}")
    print(f"  - 输出文件: {output_file}")
    
    # 显示每个城市的数据统计
    print("\n各城市数据统计:")
    city_stats = merged_df.groupby('city').size()
    for city, count in city_stats.items():
        print(f"  - {city}: {count} 条记录")
    
    return merged_df

if __name__ == "__main__":
    # 检查 data 目录是否存在
    if not os.path.exists("data"):
        print("错误: data 目录不存在，请先创建并放入数据文件")
    else:
        merged_data = merge_city_data()


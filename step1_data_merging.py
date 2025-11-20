"""
步骤 1：数据整合
读取 data/ 目录下所有城市的 Excel 文件，合并为一个总的 CSV 文件 AirCondition.csv
"""

import pandas as pd
import os
from pathlib import Path

# 城市列表
cities = [
    "武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", 
    "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市", 
    "恩施土家族苗族自治州", "仙桃市", "潜江市", "天门市", "神农架林区"
]

# 需要提取的列
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
            
            # 检查必需的列是否存在
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"警告: {city} 的数据文件缺少以下列: {missing_columns}")
                # 尝试使用部分列
                available_columns = [col for col in required_columns if col in df.columns]
                df = df[available_columns]
            else:
                # 提取需要的列
                df = df[required_columns]
            
            # 确保 city 列存在（如果原数据没有，则添加）
            if "city" not in df.columns:
                df["city"] = city
            
            # 确保 city 列的值正确
            df["city"] = city
            
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
    
    # 确保列的顺序正确
    merged_df = merged_df[required_columns]
    
    # 保存为 CSV
    output_file = "AirCondition.csv"
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


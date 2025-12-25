"""
安装 PyEcharts 地图包的辅助脚本
解决 echarts-china-provinces-pypkg 安装问题

该程序代码完成人：张思浩
"""

import subprocess
import sys

def install_echarts_maps():
    """安装 PyEcharts 地图包"""
    print("=" * 60)
    print("PyEcharts 地图包安装工具")
    print("=" * 60)
    print()
    
    # 步骤 1: 确保 pip 可用
    print("步骤 1: 检查 pip...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True, capture_output=True)
        print("✓ pip 可用")
    except:
        print("✗ pip 不可用，尝试修复...")
        try:
            subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], check=True)
            print("✓ pip 已修复")
        except Exception as e:
            print(f"✗ 无法修复 pip: {e}")
            print("请手动运行: python -m ensurepip --upgrade")
            return False
    
    print()
    
    # 步骤 2: 安装 pyecharts-jupyter-installer（如果需要）
    print("步骤 2: 安装构建依赖...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyecharts-jupyter-installer'], 
                      check=True)
        print("✓ pyecharts-jupyter-installer 安装成功")
    except Exception as e:
        print(f"⚠ 警告: pyecharts-jupyter-installer 安装失败: {e}")
        print("  继续尝试安装地图包...")
    
    print()
    
    # 步骤 3: 尝试安装地图包
    print("步骤 3: 安装地图包...")
    packages = [
        'echarts-china-provinces-pypkg',
        'echarts-china-cities-pypkg'
    ]
    
    success_count = 0
    for package in packages:
        try:
            print(f"  正在安装 {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                          check=True, capture_output=True)
            print(f"  ✓ {package} 安装成功")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {package} 安装失败")
            print(f"    错误信息: {e}")
    
    print()
    print("=" * 60)
    if success_count == len(packages):
        print("✓ 所有地图包安装成功！")
        return True
    elif success_count > 0:
        print(f"⚠ 部分地图包安装成功 ({success_count}/{len(packages)})")
        print("  项目仍可运行，但某些地图功能可能受限")
        return True
    else:
        print("✗ 地图包安装失败")
        print()
        print("替代方案:")
        print("  1. 新版本的 pyecharts 可能不需要这些包")
        print("  2. 可以在代码中手动加载地图数据")
        print("  3. 使用 pyecharts 的内置地图功能")
        return False

if __name__ == "__main__":
    install_echarts_maps()


"""
检查并安装缺失的依赖包
适用于已存在的 conda 虚拟环境
"""

import subprocess
import sys
import pkg_resources

# 可选包列表（安装失败不影响项目运行）
OPTIONAL_PACKAGES = [
    'echarts-china-provinces-pypkg',
    'echarts-china-cities-pypkg'
]

# 从 requirements.txt 读取需要的包
def read_requirements():
    """读取 requirements.txt 文件"""
    requirements = []
    optional_requirements = []
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 处理版本号，例如 "pandas>=1.5.0" -> "pandas"
                    package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('>')[0].split('<')[0].strip()
                    if package_name in OPTIONAL_PACKAGES:
                        optional_requirements.append((package_name, line))
                    else:
                        requirements.append((package_name, line))
    except FileNotFoundError:
        print("错误: 未找到 requirements.txt 文件")
        return [], []
    return requirements, optional_requirements

def check_package_installed(package_name):
    """检查包是否已安装"""
    try:
        # 尝试导入包（使用标准名称）
        # 有些包的导入名和安装名不同
        import_map = {
            'scikit-learn': 'sklearn',
            'pyecharts': 'pyecharts',
            'torch': 'torch',
        }
        
        import_name = import_map.get(package_name, package_name)
        __import__(import_name)
        return True
    except ImportError:
        # 也尝试通过 pkg_resources 检查
        try:
            pkg_resources.get_distribution(package_name)
            return True
        except pkg_resources.DistributionNotFound:
            return False

def get_installed_version(package_name):
    """获取已安装包的版本"""
    try:
        import_map = {
            'scikit-learn': 'sklearn',
        }
        import_name = import_map.get(package_name, package_name)
        module = __import__(import_name)
        if hasattr(module, '__version__'):
            return module.__version__
    except:
        pass
    
    try:
        return pkg_resources.get_distribution(package_name).version
    except:
        return "未知"

def main():
    print("=" * 60)
    print("依赖包检查工具")
    print("=" * 60)
    print()
    
    requirements, optional_requirements = read_requirements()
    all_requirements = requirements + optional_requirements
    
    if not all_requirements:
        return
    
    installed_packages = []
    missing_packages = []
    missing_optional = []
    
    print("正在检查必需包...")
    print("-" * 60)
    
    for package_name, requirement_line in requirements:
        if check_package_installed(package_name):
            version = get_installed_version(package_name)
            installed_packages.append((package_name, requirement_line, version))
            print(f"✓ {package_name:20s} 已安装 (版本: {version})")
        else:
            missing_packages.append((package_name, requirement_line))
            print(f"✗ {package_name:20s} 未安装 [必需]")
    
    if optional_requirements:
        print()
        print("正在检查可选包（地图包）...")
        print("-" * 60)
        for package_name, requirement_line in optional_requirements:
            if check_package_installed(package_name):
                version = get_installed_version(package_name)
                installed_packages.append((package_name, requirement_line, version))
                print(f"✓ {package_name:20s} 已安装 (版本: {version})")
            else:
                missing_optional.append((package_name, requirement_line))
                print(f"⚠ {package_name:20s} 未安装 [可选，不影响运行]")
    
    print("-" * 60)
    print()
    
    # 统计结果
    print(f"必需包: {len(requirements)} 个，已安装 {len([p for p, _, _ in installed_packages if p not in OPTIONAL_PACKAGES])} 个")
    if optional_requirements:
        print(f"可选包: {len(optional_requirements)} 个，已安装 {len([p for p, _, _ in installed_packages if p in OPTIONAL_PACKAGES])} 个")
    print()
    
    if missing_packages:
        print("=" * 60)
        print("缺失的必需包（需要安装）:")
        print("=" * 60)
        for package_name, requirement_line in missing_packages:
            print(f"  - {requirement_line}")
        print()
    
    if missing_optional:
        print("=" * 60)
        print("缺失的可选包（地图包，不影响项目运行）:")
        print("=" * 60)
        for package_name, requirement_line in missing_optional:
            print(f"  - {requirement_line}")
        print()
        print("提示: 地图包安装失败不影响项目运行，已提供替代可视化方案")
        print("      详见 map_visualization_helper.py 和 install_maps_alternative.md")
        print()
    
    if missing_packages:
        
        # 询问是否安装
        print("=" * 60)
        print("安装选项:")
        print("=" * 60)
        print()
        print("方式 1: 使用 pip 安装所有缺失的包（推荐）")
        print("  命令: pip install " + " ".join([req for _, req in missing_packages]))
        print()
        print("方式 2: 使用 conda 安装（如果可用）")
        conda_packages = []
        pip_only_packages = []
        
        # 分类：哪些可以用 conda，哪些只能用 pip
        conda_available = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'scikit-learn', 'pytorch', 'torch', 'openpyxl']
        for package_name, requirement_line in missing_packages:
            if package_name in conda_available:
                conda_packages.append(package_name)
            else:
                pip_only_packages.append(requirement_line)
        
        if conda_packages:
            print(f"  conda install {' '.join(conda_packages)} -c conda-forge -c pytorch")
        if pip_only_packages:
            print(f"  pip install {' '.join(pip_only_packages)}")
        print()
        
        # 自动安装选项
        response = input("是否现在自动安装缺失的包？(y/n): ").strip().lower()
        if response == 'y' or response == 'yes':
            print()
            print("开始安装缺失的包...")
            print("-" * 60)
            
            # 先尝试用 conda 安装可用的包
            if conda_packages:
                print(f"\n使用 conda 安装: {', '.join(conda_packages)}")
                try:
                    conda_cmd = ['conda', 'install', '-y'] + conda_packages + ['-c', 'conda-forge', '-c', 'pytorch']
                    subprocess.run(conda_cmd, check=True)
                    print("✓ Conda 安装完成")
                except subprocess.CalledProcessError:
                    print("✗ Conda 安装失败，将使用 pip 安装")
                    pip_only_packages.extend([req for pkg, req in missing_packages if pkg in conda_packages])
                except FileNotFoundError:
                    print("✗ 未找到 conda 命令，将使用 pip 安装")
                    pip_only_packages.extend([req for pkg, req in missing_packages if pkg in conda_packages])
            
            # 使用 pip 安装所有包（包括 conda 安装失败的）
            if pip_only_packages or not conda_packages:
                print(f"\n使用 pip 安装剩余包...")
                pip_cmd = [sys.executable, '-m', 'pip', 'install'] + [req for _, req in missing_packages]
                try:
                    subprocess.run(pip_cmd, check=True)
                    print("✓ Pip 安装完成")
                except subprocess.CalledProcessError as e:
                    print(f"✗ 安装过程中出现错误: {e}")
                    print("请手动运行安装命令")
            
            print()
            print("安装完成！建议重新运行此脚本验证安装结果。")
        else:
            print("已跳过自动安装。请手动运行上述命令安装缺失的包。")
    else:
        print("=" * 60)
        print("✓ 所有依赖包已安装！")
        print("=" * 60)

if __name__ == "__main__":
    main()


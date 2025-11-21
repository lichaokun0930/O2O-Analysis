# ============================================================================
# 测算模型目录 - 冗余文件清理分析
# ============================================================================

import os
from pathlib import Path
from collections import defaultdict
import re

# 当前目录
BASE_DIR = Path(__file__).parent

# 定义文件类别
CATEGORIES = {
    '🧪 测试文件': [],
    '🔍 检查文件': [],
    '✅ 验证文件': [],
    '🩺 诊断文件': [],
    '📊 对比文件': [],
    '🧹 清理脚本': [],
    '📝 演示/Demo': [],
    '🔧 配置脚本': [],
    '📚 文档指南': [],
    '🗂️ 归档/备份': [],
    '⚙️ 核心功能': [],
    '🚀 启动脚本': [],
    '🔄 临时文件': [],
}

# 关键词映射
KEYWORDS = {
    '测试': '🧪 测试文件',
    '检查': '🔍 检查文件',
    '验证': '✅ 验证文件',
    '诊断': '🩺 诊断文件',
    '对比': '📊 对比文件',
    '清理': '🧹 清理脚本',
    '演示': '📝 演示/Demo',
    'demo': '📝 演示/Demo',
    'Demo': '📝 演示/Demo',
    'DEMO': '📝 演示/Demo',
    '配置': '🔧 配置脚本',
    'setup': '🔧 配置脚本',
    'config': '🔧 配置脚本',
    '指南': '📚 文档指南',
    '说明': '📚 文档指南',
    '使用': '📚 文档指南',
    'README': '📚 文档指南',
    'Archived': '🗂️ 归档/备份',
    'backup': '🗂️ 归档/备份',
    '备份': '🗂️ 归档/备份',
    '归档': '🗂️ 归档/备份',
    '已删除': '🗂️ 归档/备份',
    'temp': '🔄 临时文件',
    '临时': '🔄 临时文件',
    '启动': '🚀 启动脚本',
    'start': '🚀 启动脚本',
}

# 核心功能文件（不应删除）
CORE_FILES = {
    '智能门店看板_Dash版.py',
    '真实数据处理器.py',
    '订单数据处理器.py',
    '场景营销智能决策引擎.py',
    '商品场景智能打标引擎.py',
    'requirements.txt',
    '.env',
    '.gitignore',
    'README.md',
}

# 扫描文件
def scan_files():
    files = []
    for file in BASE_DIR.iterdir():
        if file.is_file():
            files.append(file.name)
    return sorted(files)

# 分类文件
def categorize_file(filename):
    # 先检查是否是核心文件
    if filename in CORE_FILES:
        return '⚙️ 核心功能'
    
    # 根据关键词分类
    for keyword, category in KEYWORDS.items():
        if keyword in filename:
            return category
    
    # 默认为其他
    return None

# 主分析
def analyze():
    print("=" * 80)
    print("               测算模型目录 - 文件清理分析报告")
    print("=" * 80)
    print()
    
    files = scan_files()
    categorized = defaultdict(list)
    
    # 分类统计
    for filename in files:
        category = categorize_file(filename)
        if category:
            categorized[category].append(filename)
    
    total_files = len(files)
    
    # 显示分类结果
    print(f"📊 总文件数: {total_files}")
    print()
    
    # 核心功能文件（必须保留）
    print("=" * 80)
    print("⚙️  核心功能文件 (必须保留)")
    print("=" * 80)
    if categorized['⚙️ 核心功能']:
        for f in sorted(categorized['⚙️ 核心功能']):
            print(f"  ✅ {f}")
    print(f"\n  小计: {len(categorized['⚙️ 核心功能'])} 个文件\n")
    
    # 可以删除的文件类别
    deletable_categories = [
        '🧪 测试文件',
        '🔍 检查文件', 
        '✅ 验证文件',
        '🩺 诊断文件',
        '📊 对比文件',
        '📝 演示/Demo',
        '🔄 临时文件',
        '🗂️ 归档/备份',
    ]
    
    deletable_count = 0
    
    for category in deletable_categories:
        if categorized[category]:
            print("=" * 80)
            print(f"{category} (建议删除)")
            print("=" * 80)
            for f in sorted(categorized[category]):
                print(f"  ❌ {f}")
                deletable_count += 1
            print(f"\n  小计: {len(categorized[category])} 个文件\n")
    
    # 需要保留的其他类别
    keep_categories = [
        '🚀 启动脚本',
        '🔧 配置脚本',
        '📚 文档指南',
        '🧹 清理脚本',
    ]
    
    for category in keep_categories:
        if categorized[category]:
            print("=" * 80)
            print(f"{category} (建议保留)")
            print("=" * 80)
            for f in sorted(categorized[category]):
                print(f"  ⚠️  {f}")
            print(f"\n  小计: {len(categorized[category])} 个文件\n")
    
    # 汇总
    print("=" * 80)
    print("📊 清理建议汇总")
    print("=" * 80)
    print(f"  总文件数: {total_files}")
    print(f"  可删除文件: {deletable_count} 个")
    print(f"  可释放空间: 预计可减少 {deletable_count} 个文件")
    print()
    
    # 生成清理脚本建议
    print("=" * 80)
    print("🔧 自动清理建议")
    print("=" * 80)
    print()
    print("方式1: 使用PowerShell批量删除")
    print("-" * 80)
    print("# 复制以下命令到PowerShell运行:")
    print()
    
    for category in deletable_categories:
        if categorized[category]:
            for f in sorted(categorized[category]):
                print(f'Remove-Item "{f}" -Force')
    
    print()
    print("=" * 80)
    print()
    print("⚠️  重要提示:")
    print("  1. 建议先备份整个目录")
    print("  2. 确认当前项目没有在运行")
    print("  3. 删除前仔细检查文件列表")
    print("  4. 可以先将文件移动到临时文件夹,测试无问题后再删除")
    print()
    print("=" * 80)

if __name__ == '__main__':
    analyze()

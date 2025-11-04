# -*- coding: utf-8 -*-
"""
快速集成脚本 - 订单分析增强模块
自动将增强功能集成到主看板文件中
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
MAIN_DASHBOARD_FILE = SCRIPT_DIR / "智能门店经营看板_可视化.py"
ENHANCEMENT_MODULE = SCRIPT_DIR / "订单分析增强模块.py"
BACKUP_DIR = SCRIPT_DIR / "backups"

def create_backup():
    """创建主文件备份"""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"智能门店经营看板_可视化_backup_{timestamp}.py"
    
    shutil.copy2(MAIN_DASHBOARD_FILE, backup_file)
    print(f"✅ 备份已创建: {backup_file}")
    return backup_file

def check_files_exist():
    """检查必要文件是否存在"""
    if not MAIN_DASHBOARD_FILE.exists():
        print(f"❌ 主文件不存在: {MAIN_DASHBOARD_FILE}")
        return False
    
    if not ENHANCEMENT_MODULE.exists():
        print(f"❌ 增强模块不存在: {ENHANCEMENT_MODULE}")
        return False
    
    print("✅ 所有必要文件都存在")
    return True

def add_import_statement():
    """在主文件中添加导入语句"""
    with open(MAIN_DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经导入
    if 'from 订单分析增强模块 import' in content:
        print("⚠️ 导入语句已存在，跳过")
        return True
    
    # 查找合适的插入位置（在其他导入之后）
    import_section_end = content.find('from price_comparison_dashboard import')
    if import_section_end == -1:
        import_section_end = content.find('PRICE_PANEL_INTERMEDIATE_DIR')
    
    if import_section_end == -1:
        print("❌ 无法找到合适的插入位置")
        return False
    
    # 找到该行的结束位置
    next_newline = content.find('\n', import_section_end)
    
    import_code = """
# 导入订单分析增强模块
try:
    from 订单分析增强模块 import (
        render_enhanced_order_overview,
        render_enhanced_profit_analysis
    )
    ORDER_ENHANCEMENT_AVAILABLE = True
    print("✅ 订单分析增强模块已加载")
except ImportError as e:
    print(f"⚠️ 订单分析增强模块未加载: {e}")
    ORDER_ENHANCEMENT_AVAILABLE = False
"""
    
    # 插入导入代码
    new_content = content[:next_newline+1] + import_code + content[next_newline+1:]
    
    # 写回文件
    with open(MAIN_DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 导入语句已添加")
    return True

def update_render_functions():
    """更新渲染函数调用"""
    with open(MAIN_DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换订单概览调用
    old_overview_call = "render_order_overview(processed_order_data, order_summary)"
    new_overview_call = """if ORDER_ENHANCEMENT_AVAILABLE:
            render_enhanced_order_overview(processed_order_data, order_summary)
        else:
            render_order_overview(processed_order_data, order_summary)"""
    
    if old_overview_call in content:
        content = content.replace(old_overview_call, new_overview_call)
        print("✅ 订单概览调用已更新")
    else:
        print("⚠️ 未找到订单概览调用，可能已更新或位置不同")
    
    # 替换利润分析调用
    old_profit_call = "render_profit_analysis(processed_order_data, order_summary)"
    new_profit_call = """if ORDER_ENHANCEMENT_AVAILABLE:
            render_enhanced_profit_analysis(processed_order_data, order_summary)
        else:
            render_profit_analysis(processed_order_data, order_summary)"""
    
    if old_profit_call in content:
        content = content.replace(old_profit_call, new_profit_call)
        print("✅ 利润分析调用已更新")
    else:
        print("⚠️ 未找到利润分析调用，可能已更新或位置不同")
    
    # 写回文件
    with open(MAIN_DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def verify_integration():
    """验证集成是否成功"""
    with open(MAIN_DASHBOARD_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "导入语句": "from 订单分析增强模块 import" in content,
        "增强标志": "ORDER_ENHANCEMENT_AVAILABLE" in content,
        "概览函数调用": "render_enhanced_order_overview" in content,
        "利润函数调用": "render_enhanced_profit_analysis" in content
    }
    
    print("\n📋 集成验证结果:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}: {'通过' if result else '失败'}")
        if not result:
            all_passed = False
    
    return all_passed

def main():
    """主函数"""
    print("=" * 60)
    print("  订单分析增强模块 - 快速集成工具")
    print("=" * 60)
    print()
    
    # 1. 检查文件存在性
    print("步骤 1: 检查文件...")
    if not check_files_exist():
        print("\n❌ 集成失败：缺少必要文件")
        return False
    print()
    
    # 2. 创建备份
    print("步骤 2: 创建备份...")
    backup_file = create_backup()
    print()
    
    # 3. 添加导入语句
    print("步骤 3: 添加导入语句...")
    if not add_import_statement():
        print("\n❌ 集成失败：无法添加导入语句")
        print(f"💡 提示: 可以手动添加，参考《订单分析模块集成指南.md》")
        return False
    print()
    
    # 4. 更新函数调用
    print("步骤 4: 更新函数调用...")
    if not update_render_functions():
        print("\n❌ 集成失败：无法更新函数调用")
        return False
    print()
    
    # 5. 验证集成
    print("步骤 5: 验证集成...")
    success = verify_integration()
    print()
    
    if success:
        print("=" * 60)
        print("  🎉 集成成功！")
        print("=" * 60)
        print()
        print("📌 下一步操作:")
        print("  1. 运行 Streamlit 应用:")
        print("     cd \"d:\\Python1\\O2O_Analysis\\O2O数据分析\\测算模型\"")
        print("     & \"..\\\.venv\\Scripts\\streamlit.exe\" run 智能门店经营看板_可视化.py --server.port 8505")
        print()
        print("  2. 加载订单数据并测试功能")
        print("  3. 检查'订单概览'和'利润分析'标签页")
        print()
        print(f"💾 备份文件: {backup_file}")
        print("   如需恢复，复制备份文件到主文件位置")
    else:
        print("=" * 60)
        print("  ⚠️ 集成部分完成，请手动检查")
        print("=" * 60)
        print()
        print("📖 请参考《订单分析模块集成指南.md》手动完成集成")
    
    return success

if __name__ == "__main__":
    try:
        main()
        input("\n按 Enter 键退出...")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")

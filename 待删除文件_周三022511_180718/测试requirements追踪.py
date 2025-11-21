#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements追踪系统功能测试脚本
演示新增/删除/更新依赖包的追踪功能

作者: AI助手
创建日期: 2025-11-19
"""

import sys
import shutil
from pathlib import Path
import time

# 添加tools目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.track_requirements_changes import RequirementsTracker

def print_section(title):
    """打印章节标题"""
    print("\n" + "="*80)
    print(f"🧪 {title}")
    print("="*80)

def backup_requirements():
    """备份原始requirements.txt"""
    req_path = Path("requirements.txt")
    backup_path = Path("requirements.txt.backup")
    
    if req_path.exists():
        shutil.copy(req_path, backup_path)
        print(f"✅ 已备份原始requirements.txt → {backup_path}")
        return True
    else:
        print(f"❌ 找不到requirements.txt")
        return False

def restore_requirements():
    """恢复原始requirements.txt"""
    backup_path = Path("requirements.txt.backup")
    req_path = Path("requirements.txt")
    
    if backup_path.exists():
        shutil.copy(backup_path, req_path)
        backup_path.unlink()
        print(f"✅ 已恢复原始requirements.txt")
        return True
    else:
        print(f"⚠️  未找到备份文件")
        return False

def test_initial_snapshot():
    """测试1: 创建初始快照"""
    print_section("测试1: 创建初始快照")
    
    tracker = RequirementsTracker()
    
    # 读取当前requirements
    if not tracker.read_current_requirements():
        return False
    
    print(f"\n📊 当前依赖包数量: {len(tracker.current_requirements)}")
    
    # 显示前10个包
    print("\n📦 示例包列表 (前10个):")
    for i, (package, version) in enumerate(list(tracker.current_requirements.items())[:10]):
        print(f"   {i+1}. {package:<30} {version}")
    
    print("\n💡 首次运行将创建初始快照...")
    time.sleep(1)
    
    return True

def test_add_package():
    """测试2: 新增依赖包"""
    print_section("测试2: 新增依赖包")
    
    req_path = Path("requirements.txt")
    
    # 读取当前内容
    with open(req_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # 添加新包
    print("\n📝 添加新依赖包...")
    new_packages = [
        "\n# 测试新增依赖 (测试用)",
        "requests==2.31.0  # HTTP客户端库",
        "beautifulsoup4==4.12.0  # HTML解析库"
    ]
    
    with open(req_path, 'a', encoding='utf-8') as f:
        f.write('\n'.join(new_packages))
    
    print("✅ 已添加:")
    for pkg in new_packages[1:]:  # 跳过注释行
        print(f"   + {pkg}")
    
    # 运行追踪
    print("\n🔍 运行追踪检测变更...")
    tracker = RequirementsTracker()
    result = tracker.track_changes(reason="【测试】添加HTTP和HTML解析库")
    
    # 恢复原始内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    print("\n✅ 已恢复原始requirements.txt")
    
    return result

def test_remove_package():
    """测试3: 删除依赖包"""
    print_section("测试3: 删除依赖包")
    
    req_path = Path("requirements.txt")
    
    # 读取当前内容
    with open(req_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到要删除的包
    target_packages = ['seaborn', 'matplotlib']
    removed_lines = []
    new_lines = []
    
    for line in lines:
        if any(pkg in line.lower() for pkg in target_packages) and not line.strip().startswith('#'):
            removed_lines.append(line.strip())
        else:
            new_lines.append(line)
    
    if not removed_lines:
        print("⚠️  未找到可删除的测试包")
        return False
    
    # 写入修改后的内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("\n📝 删除依赖包:")
    for line in removed_lines:
        print(f"   - {line}")
    
    # 运行追踪
    print("\n🔍 运行追踪检测变更...")
    tracker = RequirementsTracker()
    result = tracker.track_changes(reason="【测试】移除未使用的可视化库")
    
    # 恢复原始内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✅ 已恢复原始requirements.txt")
    
    return result

def test_update_version():
    """测试4: 更新版本号"""
    print_section("测试4: 更新版本号")
    
    req_path = Path("requirements.txt")
    
    # 读取当前内容
    with open(req_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新版本号
    print("\n📝 更新依赖包版本:")
    
    updates = [
        ('pandas>=2.0.0', 'pandas>=2.1.0'),
        ('numpy>=1.24.0', 'numpy>=1.25.0'),
    ]
    
    modified_content = content
    for old_spec, new_spec in updates:
        if old_spec in modified_content:
            modified_content = modified_content.replace(old_spec, new_spec)
            print(f"   🔄 {old_spec} → {new_spec}")
    
    # 写入修改后的内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    # 运行追踪
    print("\n🔍 运行追踪检测变更...")
    tracker = RequirementsTracker()
    result = tracker.track_changes(reason="【测试】升级pandas和numpy版本")
    
    # 恢复原始内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ 已恢复原始requirements.txt")
    
    return result

def test_mixed_changes():
    """测试5: 混合变更"""
    print_section("测试5: 混合变更(新增+删除+更新)")
    
    req_path = Path("requirements.txt")
    
    # 读取当前内容
    with open(req_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print("\n📝 执行混合变更:")
    
    # 1. 删除包
    new_lines = [line for line in lines if 'seaborn' not in line.lower()]
    print("   ❌ 删除: seaborn")
    
    # 2. 更新版本
    modified_lines = []
    for line in new_lines:
        if 'pandas>=2.0.0' in line:
            modified_lines.append(line.replace('pandas>=2.0.0', 'pandas>=2.1.0'))
            print("   🔄 更新: pandas>=2.0.0 → pandas>=2.1.0")
        else:
            modified_lines.append(line)
    
    # 3. 新增包
    modified_lines.append('\n# 测试新增\n')
    modified_lines.append('pytest==7.4.0  # 测试框架\n')
    print("   ✅ 新增: pytest==7.4.0")
    
    # 写入修改后的内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    # 运行追踪
    print("\n🔍 运行追踪检测变更...")
    tracker = RequirementsTracker()
    result = tracker.track_changes(reason="【测试】混合变更:删除seaborn,升级pandas,添加pytest")
    
    # 恢复原始内容
    with open(req_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("\n✅ 已恢复原始requirements.txt")
    
    return result

def test_show_packages():
    """测试6: 显示当前包列表"""
    print_section("测试6: 显示当前包列表")
    
    tracker = RequirementsTracker()
    
    if not tracker.read_current_requirements():
        return False
    
    tracker.show_current_packages()
    
    return True

def test_cleanup_snapshots():
    """测试7: 清理旧快照"""
    print_section("测试7: 清理旧快照")
    
    tracker = RequirementsTracker()
    
    snapshots = sorted(tracker.snapshots_dir.glob("requirements_*.json"))
    
    print(f"\n📁 当前快照数量: {len(snapshots)}")
    
    if len(snapshots) > 3:
        print(f"\n🗑️  清理旧快照 (保留最新3个)...")
        tracker.cleanup_old_snapshots(keep_count=3)
    else:
        print(f"\n💡 快照数量较少,无需清理")
    
    return True

def main():
    """主函数"""
    
    print("="*80)
    print("🧪 Requirements追踪系统功能测试")
    print("="*80)
    print("本测试将演示所有主要功能")
    print("测试过程会临时修改requirements.txt,完成后会自动恢复")
    print("="*80)
    
    input("\n按Enter键开始测试...")
    
    # 备份原始文件
    if not backup_requirements():
        print("❌ 备份失败,测试终止")
        return False
    
    try:
        # 测试序列
        tests = [
            ("初始快照", test_initial_snapshot),
            ("新增依赖包", test_add_package),
            ("删除依赖包", test_remove_package),
            ("更新版本号", test_update_version),
            ("混合变更", test_mixed_changes),
            ("显示包列表", test_show_packages),
            ("清理快照", test_cleanup_snapshots),
        ]
        
        results = []
        
        for i, (name, test_func) in enumerate(tests, 1):
            try:
                print(f"\n\n{'='*80}")
                print(f"🔹 执行测试 {i}/{len(tests)}: {name}")
                print(f"{'='*80}")
                
                result = test_func()
                results.append((name, result))
                
                if result:
                    print(f"\n✅ 测试通过: {name}")
                else:
                    print(f"\n⚠️  测试未完成: {name}")
                
                # 等待用户确认
                if i < len(tests):
                    input(f"\n按Enter继续下一个测试...")
                
            except Exception as e:
                print(f"\n❌ 测试失败: {name}")
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        # 测试总结
        print("\n\n" + "="*80)
        print("📋 测试总结")
        print("="*80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status} - {name}")
        
        print(f"\n🎯 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("✅ 所有测试通过!")
        else:
            print(f"⚠️  {total - passed} 项测试失败")
        
    finally:
        # 恢复原始文件
        print("\n" + "="*80)
        print("🔄 恢复原始文件...")
        restore_requirements()
        
        print("\n📄 查看生成的文件:")
        print("   - requirements_changelog.md (变更日志)")
        print("   - .requirements_snapshots/ (历史快照)")
        
        print("\n💡 提示:")
        print("   如需真实使用,请运行: python tools\\track_requirements_changes.py")
        print("="*80)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已取消")
        restore_requirements()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        restore_requirements()
        sys.exit(1)

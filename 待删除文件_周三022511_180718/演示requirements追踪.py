#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements追踪系统 - 简单演示
"""

import sys
from pathlib import Path

# 添加tools目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from tools.track_requirements_changes import RequirementsTracker

def main():
    print("="*80)
    print("📦 Requirements追踪系统演示")
    print("="*80)
    
    # 初始化追踪器
    tracker = RequirementsTracker()
    
    print("\n1️⃣ 读取当前requirements.txt...")
    if not tracker.read_current_requirements():
        print("❌ 读取失败")
        return False
    
    print(f"\n✅ 成功读取 {len(tracker.current_requirements)} 个依赖包")
    
    print("\n2️⃣ 前10个依赖包:")
    for i, (package, version) in enumerate(list(tracker.current_requirements.items())[:10], 1):
        print(f"   {i:2d}. {package:<35} {version}")
    
    print("\n3️⃣ 读取历史快照...")
    has_snapshot = tracker.read_last_snapshot()
    
    if has_snapshot:
        print(f"\n✅ 找到历史快照: {len(tracker.last_snapshot)} 个包")
        
        print("\n4️⃣ 检测变更...")
        changes = tracker.detect_changes()
        
        total_changes = len(changes['added']) + len(changes['removed']) + len(changes['updated'])
        
        print(f"\n📊 变更统计:")
        print(f"   ✅ 新增: {len(changes['added'])} 个")
        print(f"   ❌ 删除: {len(changes['removed'])} 个")
        print(f"   🔄 更新: {len(changes['updated'])} 个")
        print(f"   ⚪ 未变更: {changes['unchanged']} 个")
        
        if total_changes > 0:
            if changes['added']:
                print("\n✅ 新增的包:")
                for package, version in changes['added']:
                    print(f"   + {package} {version}")
            
            if changes['removed']:
                print("\n❌ 删除的包:")
                for package, version in changes['removed']:
                    print(f"   - {package} {version}")
            
            if changes['updated']:
                print("\n🔄 更新的包:")
                for package, old_ver, new_ver in changes['updated']:
                    print(f"   {package}: {old_ver} → {new_ver}")
        else:
            print("\n✅ requirements.txt 与上次快照完全一致,无变更")
    else:
        print("\nℹ️  这是首次追踪,已创建初始快照")
    
    print("\n5️⃣ 快照文件列表:")
    snapshots = sorted(tracker.snapshots_dir.glob("requirements_*.json"))
    for snapshot in snapshots:
        print(f"   📄 {snapshot.name}")
    
    print("\n" + "="*80)
    print("✅ 演示完成!")
    print("="*80)
    
    print("\n💡 使用提示:")
    print("1. 修改requirements.txt后运行: python tools\\track_requirements_changes.py")
    print("2. 查看变更日志: requirements_changelog.md")
    print("3. 查看历史快照: .requirements_snapshots/")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

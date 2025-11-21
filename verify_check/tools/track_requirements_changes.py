#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Requirements.txt 变更追踪工具
自动检测requirements.txt的变更并生成结构化的变更日志

功能:
1. 自动对比当前版本与上一次快照
2. 识别新增/删除/版本更新的包
3. 生成结构化的Markdown变更日志
4. 保存历史版本快照
5. 可选: 安全漏洞扫描

作者: AI助手
创建日期: 2025-11-19
"""

import os
import sys
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
import re

class RequirementsTracker:
    """Requirements.txt变更追踪器"""
    
    def __init__(self, 
                 requirements_path: str = "requirements.txt",
                 snapshots_dir: str = ".requirements_snapshots",
                 changelog_path: str = "requirements_changelog.md"):
        """
        初始化追踪器
        
        Args:
            requirements_path: requirements.txt文件路径
            snapshots_dir: 快照存储目录
            changelog_path: 变更日志路径
        """
        self.requirements_path = Path(requirements_path)
        self.snapshots_dir = Path(snapshots_dir)
        self.changelog_path = Path(changelog_path)
        
        # 确保目录存在
        self.snapshots_dir.mkdir(exist_ok=True)
        
        # 当前requirements内容
        self.current_requirements = {}
        self.current_raw_content = ""
        
        # 上一次快照
        self.last_snapshot = {}
        
        print(f"📦 Requirements追踪器初始化完成")
        print(f"   📄 监控文件: {self.requirements_path}")
        print(f"   📁 快照目录: {self.snapshots_dir}")
        print(f"   📋 变更日志: {self.changelog_path}")
    
    def parse_requirements(self, content: str) -> Dict[str, str]:
        """
        解析requirements.txt内容
        
        Args:
            content: requirements.txt文件内容
            
        Returns:
            {package_name: version_spec} 字典
        """
        packages = {}
        
        for line in content.split('\n'):
            # 去除注释和空白
            line = line.split('#')[0].strip()
            
            if not line:
                continue
            
            # 匹配包名和版本
            # 支持: package==1.0.0, package>=1.0.0, package~=1.0.0, package
            match = re.match(r'^([a-zA-Z0-9\-_\[\]]+)(.*?)$', line)
            
            if match:
                package_name = match.group(1).lower()
                version_spec = match.group(2).strip()
                
                # 清理包名中的extras (如 uvicorn[standard])
                package_name_clean = re.sub(r'\[.*?\]', '', package_name)
                
                packages[package_name_clean] = version_spec if version_spec else 'any'
        
        return packages
    
    def read_current_requirements(self) -> bool:
        """读取当前requirements.txt"""
        
        if not self.requirements_path.exists():
            print(f"❌ 找不到文件: {self.requirements_path}")
            return False
        
        try:
            with open(self.requirements_path, 'r', encoding='utf-8') as f:
                self.current_raw_content = f.read()
            
            self.current_requirements = self.parse_requirements(self.current_raw_content)
            
            print(f"✅ 已读取当前requirements.txt")
            print(f"   📦 包数量: {len(self.current_requirements)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 读取requirements.txt失败: {e}")
            return False
    
    def get_latest_snapshot_path(self) -> Optional[Path]:
        """获取最新的快照文件路径"""
        
        snapshot_files = sorted(self.snapshots_dir.glob("requirements_*.json"))
        
        if snapshot_files:
            return snapshot_files[-1]
        return None
    
    def read_last_snapshot(self) -> bool:
        """读取上一次快照"""
        
        latest_snapshot = self.get_latest_snapshot_path()
        
        if not latest_snapshot:
            print("ℹ️  未找到历史快照,这是首次追踪")
            return False
        
        try:
            with open(latest_snapshot, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            
            self.last_snapshot = snapshot_data.get('packages', {})
            
            print(f"✅ 已读取上次快照: {latest_snapshot.name}")
            print(f"   📦 包数量: {len(self.last_snapshot)}")
            print(f"   📅 快照时间: {snapshot_data.get('timestamp', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"⚠️  读取快照失败: {e}")
            return False
    
    def detect_changes(self) -> Dict[str, any]:
        """
        检测变更
        
        Returns:
            {
                'added': [(package, version)],
                'removed': [(package, version)],
                'updated': [(package, old_version, new_version)],
                'unchanged': int
            }
        """
        added = []
        removed = []
        updated = []
        
        current_packages = set(self.current_requirements.keys())
        last_packages = set(self.last_snapshot.keys())
        
        # 新增的包
        for package in current_packages - last_packages:
            version = self.current_requirements[package]
            added.append((package, version))
        
        # 删除的包
        for package in last_packages - current_packages:
            version = self.last_snapshot[package]
            removed.append((package, version))
        
        # 版本更新的包
        for package in current_packages & last_packages:
            old_version = self.last_snapshot[package]
            new_version = self.current_requirements[package]
            
            if old_version != new_version:
                updated.append((package, old_version, new_version))
        
        unchanged = len(current_packages & last_packages) - len(updated)
        
        return {
            'added': sorted(added),
            'removed': sorted(removed),
            'updated': sorted(updated),
            'unchanged': unchanged
        }
    
    def save_snapshot(self) -> bool:
        """保存当前快照"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_file = self.snapshots_dir / f"requirements_{timestamp}.json"
        
        # 计算内容哈希
        content_hash = hashlib.md5(self.current_raw_content.encode()).hexdigest()
        
        snapshot_data = {
            'timestamp': datetime.now().isoformat(),
            'hash': content_hash,
            'packages': self.current_requirements,
            'total_packages': len(self.current_requirements)
        }
        
        try:
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 快照已保存: {snapshot_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ 保存快照失败: {e}")
            return False
    
    def generate_changelog_entry(self, changes: Dict, reason: str = "") -> str:
        """
        生成变更日志条目
        
        Args:
            changes: 变更数据
            reason: 变更原因说明
            
        Returns:
            Markdown格式的变更日志
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        entry = f"\n## 📅 {timestamp}\n\n"
        
        if reason:
            entry += f"**变更原因:** {reason}\n\n"
        
        # 统计信息
        total_changes = len(changes['added']) + len(changes['removed']) + len(changes['updated'])
        
        if total_changes == 0:
            entry += "### ℹ️ 无变更\n\n"
            entry += f"- 依赖包总数: {len(self.current_requirements)}\n"
            entry += f"- 未发现任何变更\n"
            return entry
        
        entry += "### 📊 变更统计\n\n"
        entry += f"| 类型 | 数量 |\n"
        entry += f"|------|------|\n"
        entry += f"| ✅ 新增 | {len(changes['added'])} |\n"
        entry += f"| ❌ 删除 | {len(changes['removed'])} |\n"
        entry += f"| 🔄 更新 | {len(changes['updated'])} |\n"
        entry += f"| ⚪ 未变更 | {changes['unchanged']} |\n"
        entry += f"| **总计** | **{len(self.current_requirements)}** |\n\n"
        
        # 新增的包
        if changes['added']:
            entry += "### ✅ 新增依赖\n\n"
            for package, version in changes['added']:
                entry += f"- **{package}** `{version}`\n"
            entry += "\n"
        
        # 删除的包
        if changes['removed']:
            entry += "### ❌ 删除依赖\n\n"
            for package, version in changes['removed']:
                entry += f"- ~~**{package}**~~ `{version}`\n"
            entry += "\n"
        
        # 更新的包
        if changes['updated']:
            entry += "### 🔄 版本更新\n\n"
            for package, old_version, new_version in changes['updated']:
                entry += f"- **{package}**: `{old_version}` → `{new_version}`\n"
            entry += "\n"
        
        entry += "---\n"
        
        return entry
    
    def append_to_changelog(self, entry: str) -> bool:
        """追加变更日志"""
        
        try:
            # 如果文件不存在,创建文件头
            if not self.changelog_path.exists():
                header = "# Requirements.txt 变更日志\n\n"
                header += "> 自动生成的依赖包变更追踪日志\n\n"
                header += "---\n"
                
                with open(self.changelog_path, 'w', encoding='utf-8') as f:
                    f.write(header)
            
            # 追加新条目
            with open(self.changelog_path, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            print(f"✅ 变更日志已更新: {self.changelog_path}")
            return True
            
        except Exception as e:
            print(f"❌ 更新变更日志失败: {e}")
            return False
    
    def track_changes(self, reason: str = "") -> bool:
        """
        执行完整的变更追踪流程
        
        Args:
            reason: 变更原因说明
            
        Returns:
            是否成功
        """
        print("\n" + "="*80)
        print("🔍 开始追踪 requirements.txt 变更")
        print("="*80)
        
        # Step 1: 读取当前requirements
        if not self.read_current_requirements():
            return False
        
        # Step 2: 读取上次快照
        has_snapshot = self.read_last_snapshot()
        
        if not has_snapshot:
            # 首次追踪,只保存快照
            print("\n📋 首次追踪,创建初始快照...")
            
            if self.save_snapshot():
                print("\n✅ 初始快照已创建")
                print(f"   📦 记录了 {len(self.current_requirements)} 个依赖包")
                print(f"   💡 下次运行将开始追踪变更")
                return True
            else:
                return False
        
        # Step 3: 检测变更
        print("\n🔍 检测变更...")
        changes = self.detect_changes()
        
        total_changes = len(changes['added']) + len(changes['removed']) + len(changes['updated'])
        
        if total_changes == 0:
            print("\n✅ 无变更检测")
            print(f"   📦 依赖包总数: {len(self.current_requirements)}")
            print(f"   💡 requirements.txt 与上次快照完全一致")
            
            # 仍然记录"无变更"条目(可选)
            # entry = self.generate_changelog_entry(changes, reason)
            # self.append_to_changelog(entry)
            
            return True
        
        # Step 4: 显示变更摘要
        print(f"\n📊 检测到 {total_changes} 项变更:")
        if changes['added']:
            print(f"   ✅ 新增: {len(changes['added'])} 个")
        if changes['removed']:
            print(f"   ❌ 删除: {len(changes['removed'])} 个")
        if changes['updated']:
            print(f"   🔄 更新: {len(changes['updated'])} 个")
        
        # Step 5: 生成变更日志
        print("\n📝 生成变更日志...")
        entry = self.generate_changelog_entry(changes, reason)
        
        if not self.append_to_changelog(entry):
            return False
        
        # Step 6: 保存新快照
        print("\n💾 保存新快照...")
        if not self.save_snapshot():
            return False
        
        print("\n" + "="*80)
        print("✅ 变更追踪完成!")
        print("="*80)
        print(f"\n📄 查看变更日志: {self.changelog_path}")
        
        return True
    
    def show_current_packages(self):
        """显示当前所有包"""
        
        print("\n" + "="*80)
        print(f"📦 当前依赖包列表 (共 {len(self.current_requirements)} 个)")
        print("="*80)
        
        for package, version in sorted(self.current_requirements.items()):
            print(f"  {package:<40} {version}")
        
        print("="*80)
    
    def cleanup_old_snapshots(self, keep_count: int = 10):
        """清理旧快照,保留最新的N个"""
        
        snapshot_files = sorted(self.snapshots_dir.glob("requirements_*.json"))
        
        if len(snapshot_files) <= keep_count:
            print(f"ℹ️  当前快照数量: {len(snapshot_files)}, 无需清理")
            return
        
        to_delete = snapshot_files[:-keep_count]
        
        print(f"\n🗑️  清理旧快照 (保留最新 {keep_count} 个)...")
        
        for snapshot_file in to_delete:
            try:
                snapshot_file.unlink()
                print(f"   ✅ 已删除: {snapshot_file.name}")
            except Exception as e:
                print(f"   ⚠️  删除失败 {snapshot_file.name}: {e}")
        
        print(f"✅ 清理完成,剩余 {keep_count} 个快照")


def main():
    """主函数"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Requirements.txt 变更追踪工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本追踪
  python track_requirements_changes.py
  
  # 添加变更说明
  python track_requirements_changes.py -r "升级Django到最新版本"
  
  # 显示当前包列表
  python track_requirements_changes.py --show
  
  # 清理旧快照
  python track_requirements_changes.py --cleanup
        """
    )
    
    parser.add_argument(
        '-r', '--reason',
        type=str,
        default="",
        help='变更原因说明'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='显示当前所有依赖包'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='清理旧快照(保留最新10个)'
    )
    
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='清理时保留的快照数量(默认10)'
    )
    
    args = parser.parse_args()
    
    # 初始化追踪器
    tracker = RequirementsTracker()
    
    # 读取当前requirements
    if not tracker.read_current_requirements():
        sys.exit(1)
    
    # 显示包列表
    if args.show:
        tracker.show_current_packages()
        return
    
    # 清理快照
    if args.cleanup:
        tracker.cleanup_old_snapshots(keep_count=args.keep)
        return
    
    # 执行追踪
    success = tracker.track_changes(reason=args.reason)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

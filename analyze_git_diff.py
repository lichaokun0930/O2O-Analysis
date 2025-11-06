# -*- coding: utf-8 -*-
"""分析Git仓库和工作目录的差异"""

import os
import subprocess

print("=" * 60)
print("Git仓库文件对比分析")
print("=" * 60)

# 获取Git里的所有Python文件
result = subprocess.run(
    ["git", "ls-tree", "-r", "HEAD", "--name-only"],
    capture_output=True,
    text=True
)

git_files = set()
for line in result.stdout.strip().split('\n'):
    if line.endswith('.py'):
        git_files.add(line)

print(f"\n📦 Git仓库中的Python文件: {len(git_files)} 个")

# 获取工作目录的所有Python文件
work_files = set()
for root, dirs, files in os.walk('.'):
    # 跳过特殊目录
    if any(skip in root for skip in ['.git', '__pycache__', '.venv', 'venv', 'node_modules']):
        continue
    
    for file in files:
        if file.endswith('.py'):
            rel_path = os.path.relpath(os.path.join(root, file), '.').replace('\\', '/')
            work_files.add(rel_path)

print(f"💾 工作目录中的Python文件: {len(work_files)} 个")

# 找出差异
only_in_git = git_files - work_files
only_in_work = work_files - git_files

print(f"\n" + "=" * 60)
print(f"📊 差异分析")
print("=" * 60)

if only_in_git:
    print(f"\n❌ 仅在Git中（工作目录缺失）: {len(only_in_git)} 个")
    for f in sorted(only_in_git):
        print(f"  - {f}")
else:
    print(f"\n✅ Git中的文件都存在于工作目录")

if only_in_work:
    print(f"\n⚠️  仅在工作目录（未提交）: {len(only_in_work)} 个")
    
    # 按类别分组
    categories = {
        '智能门店相关': [],
        '测试脚本': [],
        '数据处理': [],
        '配置和文档': [],
        '其他': []
    }
    
    for f in sorted(only_in_work):
        fname = os.path.basename(f)
        if '智能' in fname or '看板' in fname:
            categories['智能门店相关'].append(f)
        elif fname.startswith('test_') or '测试' in fname or '验证' in fname:
            categories['测试脚本'].append(f)
        elif '数据' in fname or '导入' in fname or '处理' in fname:
            categories['数据处理'].append(f)
        elif fname.endswith('.md') or '配置' in fname or '指南' in fname:
            categories['配置和文档'].append(f)
        else:
            categories['其他'].append(f)
    
    for category, files in categories.items():
        if files:
            print(f"\n  【{category}】({len(files)} 个):")
            for f in files[:10]:  # 只显示前10个
                print(f"    - {f}")
            if len(files) > 10:
                print(f"    ... 还有 {len(files)-10} 个文件")
else:
    print(f"\n✅ 工作目录没有未提交的文件")

print("\n" + "=" * 60)
print("💡 建议")
print("=" * 60)

if only_in_work:
    print("\n这些未提交的文件不会在Git回滚时丢失。")
    print("如果需要保存这些文件，建议:")
    print("  1. git add <文件名>")
    print("  2. git commit -m '保存工作进度'")
    print("  3. 或者创建一个新分支保存当前状态")

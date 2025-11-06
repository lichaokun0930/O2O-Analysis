#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量替换文件写入日志为标准logging调用
"""

import re

file_path = '智能门店看板_Dash版.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next = 0

for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    
    # 检测文件日志模式
    if 'with open("callback_debug.txt", "a", encoding="utf-8") as f:' in line:
        # 跳过整个with块（通常3-4行）
        indent = len(line) - len(line.lstrip())
        j = i + 1
        while j < len(lines) and (lines[j].strip() == '' or len(lines[j]) - len(lines[j].lstrip()) > indent):
            j += 1
        skip_next = j - i - 1
        
        # 提取函数名（向上查找最近的def）
        func_name = "unknown"
        for k in range(i-1, max(0, i-50), -1):
            if lines[k].strip().startswith('def '):
                match = re.search(r'def (\w+)', lines[k])
                if match:
                    func_name = match.group(1)
                    break
        
        # 添加logging调用（注释掉原文件日志）
        new_lines.append(f"{' ' * indent}# [DEBUG模式已禁用] 原文件日志已替换为标准logging\n")
        new_lines.append(f"{' ' * indent}# log_callback('{func_name}', ...)\n")
        continue
    
    new_lines.append(line)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ 已移除所有callback_debug.txt文件写入")
print("   改为使用标准logging模块")
print("   日志输出到: callback_debug.log")

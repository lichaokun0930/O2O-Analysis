#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复 return fig 为 wrap_chart_component(fig)
"""

import re

file_path = '智能门店看板_Dash版.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 正则模式：匹配 return fig，但保留缩进
pattern = r'^(\s+)return fig$'

def replace_return_fig(match):
    indent = match.group(1)
    # 提取前面的height信息（如果有）
    before_text = content[:match.start()]
    height_match = re.search(r"height\s*=\s*(\d+)", before_text[-500:])
    
    if height_match:
        height = height_match.group(1)
        return f"{indent}# ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure\n{indent}return wrap_chart_component(fig, height='{height}px')"
    else:
        return f"{indent}# ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure\n{indent}return wrap_chart_component(fig, height='450px')"

# 替换所有匹配
new_content = re.sub(pattern, replace_return_fig, content, flags=re.MULTILINE)

# 计数修改
original_count = len(re.findall(pattern, content, re.MULTILINE))
new_count = len(re.findall(pattern, new_content, re.MULTILINE))

print(f"原始文件中的 'return fig': {original_count} 处")
print(f"修复后剩余的 'return fig': {new_count} 处")
print(f"成功修复: {original_count - new_count} 处")

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n✅ 文件已更新！")

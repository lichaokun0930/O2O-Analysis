#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
针对性修复Streamlit兼容性问题
"""

def fix_specific_issue():
    """修复特定的use_container_width问题"""
    
    file_path = "智能门店经营看板_可视化.py"
    
    print(f"正在修复文件: {file_path}")
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 查找并修复所有use_container_width的使用
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if 'st.plotly_chart(' in line and 'use_container_width=True' in line:
            print(f"发现第{i+1}行有use_container_width问题: {line.strip()}")
            # 替换use_container_width=True为width='stretch'
            fixed_line = line.replace('use_container_width=True', "width='stretch'")
            # 添加唯一的key参数
            if ', key=' not in fixed_line:
                # 在)前添加key参数
                if fixed_line.rstrip().endswith(')'):
                    fixed_line = fixed_line.rstrip()[:-1] + f", key='hypothesis_chart_{i}')"
                else:
                    fixed_line = fixed_line + f", key='hypothesis_chart_{i}'"
            
            print(f"修复为: {fixed_line.strip()}")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # 额外处理一些可能遗漏的情况
    import re
    
    # 处理跨行的plotly_chart调用
    content = re.sub(
        r'(st\.plotly_chart\([^)]*),\s*use_container_width=True\)',
        r"\1, width='stretch')",
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # 保存修复后的文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ use_container_width问题修复完成")
        return True
    else:
        print("❌ 没有发现需要修复的内容")
        return False

if __name__ == "__main__":
    success = fix_specific_issue()
    if success:
        print("\n🚀 修复完成，现在重新启动Streamlit应用")
    else:
        print("\n⚠️  没有发现需要修复的问题")
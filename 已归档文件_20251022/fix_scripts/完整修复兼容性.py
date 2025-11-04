#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整修复Streamlit兼容性问题
- 修复use_container_width参数
- 修复plotly_chart重复ID问题
"""

import re

def fix_compatibility():
    """修复智能门店经营看板_可视化.py的兼容性问题"""
    
    file_path = r'智能门店经营看板_可视化.py'
    
    print(f"正在修复文件: {file_path}")
    
    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 修复use_container_width参数
    print("修复use_container_width参数...")
    
    # 替换所有的use_container_width=True为width='stretch'
    content = re.sub(
        r'use_container_width=True',
        "width='stretch'",
        content
    )
    
    # 替换所有的use_container_width=False为width='content'
    content = re.sub(
        r'use_container_width=False',  
        "width='content'",
        content
    )
    
    # 2. 为plotly_chart添加唯一key参数
    print("为plotly_chart添加唯一key...")
    
    # 查找所有plotly_chart调用并添加唯一key
    plotly_calls = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'st.plotly_chart(' in line:
            # 检查是否已经有key参数
            if ', key=' not in line and 'key=' not in line.split('st.plotly_chart(')[1]:
                plotly_calls.append((i, line))
    
    # 为每个plotly_chart调用添加唯一key
    key_counter = 1
    for line_idx, line in reversed(plotly_calls):  # 从后向前处理避免行号变化
        # 提取函数名或上下文作为key前缀
        context_lines = lines[max(0, line_idx-10):line_idx]
        key_prefix = "chart"
        
        # 尝试从上下文中提取更有意义的key前缀
        for ctx_line in reversed(context_lines):
            if 'def ' in ctx_line:
                func_match = re.search(r'def (\w+)', ctx_line)
                if func_match:
                    key_prefix = func_match.group(1)
                    break
            elif '###' in ctx_line or '##' in ctx_line:
                # 从注释中提取key
                comment_match = re.search(r'#+\s*(.+)', ctx_line)
                if comment_match:
                    key_prefix = re.sub(r'[^\w]', '_', comment_match.group(1).strip())[:20]
                    break
        
        # 构造新的plotly_chart调用
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        if line.rstrip().endswith(')'):
            # 在最后的)前添加key参数
            new_line = line.rstrip()[:-1] + f", key='{key_prefix}_{key_counter}')"
        else:
            # 多行调用，需要特殊处理
            new_line = line.rstrip() + f", key='{key_prefix}_{key_counter}'"
        
        lines[line_idx] = new_line
        key_counter += 1
    
    content = '\n'.join(lines)
    
    # 3. 检查并修复其他可能的兼容性问题
    print("检查其他兼容性问题...")
    
    # 修复st.beta_columns等过时API
    content = re.sub(r'st\.beta_columns', 'st.columns', content)
    content = re.sub(r'st\.beta_container', 'st.container', content)
    content = re.sub(r'st\.beta_expander', 'st.expander', content)
    
    # 保存修复后的文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ 兼容性问题修复完成")
        
        # 统计修复内容
        use_container_fixes = len(re.findall(r"width='stretch'", content)) + len(re.findall(r"width='content'", content))
        key_fixes = len([line for line in lines if ', key=' in line and 'st.plotly_chart(' in line])
        
        print(f"  - 修复use_container_width参数: {use_container_fixes}处")
        print(f"  - 添加plotly_chart唯一key: {key_fixes}处")
        
        return True
    else:
        print("❌ 没有发现需要修复的内容")
        return False

if __name__ == "__main__":
    success = fix_compatibility()
    if success:
        print("\n🚀 请重新启动Streamlit应用程序以验证修复效果")
        print("运行命令: streamlit run 智能门店经营看板_可视化.py")
    else:
        print("\n⚠️  修复未成功，请检查文件内容")
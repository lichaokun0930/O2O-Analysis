#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证代码质量修复成果
"""

import re
import sys

def check_fix_quality():
    """检查修复质量"""
    
    file_path = '智能门店看板_Dash版.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 60)
    print("🔍 代码质量修复验证报告")
    print("=" * 60)
    print()
    
    # 1. 检查裸 return fig
    pattern_naked_return_fig = r'^\s+return fig$'
    naked_returns = re.findall(pattern_naked_return_fig, content, re.MULTILINE)
    
    print("1️⃣ Plotly 返回值修复检查")
    if len(naked_returns) == 0:
        print("   ✅ 通过：所有 'return fig' 已修复为 'wrap_chart_component(fig)'")
    else:
        print(f"   ❌ 失败：仍有 {len(naked_returns)} 处裸返回 Figure 对象")
    print()
    
    # 2. 检查 wrap_chart_component 函数
    has_wrap_function = 'def wrap_chart_component' in content
    
    print("2️⃣ 统一包装函数检查")
    if has_wrap_function:
        print("   ✅ 通过：wrap_chart_component() 函数已创建")
        # 检查函数是否正确处理 go.Figure
        if 'isinstance(component, go.Figure)' in content:
            print("   ✅ 通过：正确检测并转换 Plotly Figure")
        else:
            print("   ⚠️ 警告：未检测到 Figure 类型转换逻辑")
    else:
        print("   ❌ 失败：缺少 wrap_chart_component() 函数")
    print()
    
    # 3. 检查乱码 emoji
    pattern_garbled = r'�'
    garbled_count = len(re.findall(pattern_garbled, content))
    
    print("3️⃣ 乱码占位符检查")
    if garbled_count == 0:
        print("   ✅ 通过：无乱码占位符 '�'")
    else:
        print(f"   ❌ 失败：仍有 {garbled_count} 处乱码")
        # 显示位置
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '�' in line:
                print(f"      行 {i}: {line.strip()[:60]}...")
    print()
    
    # 4. 检查文件日志写入
    pattern_file_log = r'with open\("callback_debug\.txt", "a"'
    file_log_count = len(re.findall(pattern_file_log, content))
    
    print("4️⃣ 文件日志写入检查")
    if file_log_count == 0:
        print("   ✅ 通过：已移除所有 callback_debug.txt 文件写入")
    else:
        print(f"   ⚠️ 警告：仍有 {file_log_count} 处文件写入")
    print()
    
    # 5. 检查标准logging配置
    has_logging = 'import logging' in content
    has_log_callback = 'def log_callback' in content
    
    print("5️⃣ 标准日志系统检查")
    if has_logging:
        print("   ✅ 通过：已导入 logging 模块")
    else:
        print("   ❌ 失败：缺少 logging 模块导入")
    
    if has_log_callback:
        print("   ✅ 通过：log_callback() 辅助函数已创建")
    else:
        print("   ⚠️ 警告：建议添加 log_callback() 辅助函数")
    print()
    
    # 6. 统计修复情况
    wrap_usage = len(re.findall(r'wrap_chart_component\(', content))
    
    print("6️⃣ 修复使用统计")
    print(f"   📊 wrap_chart_component 调用次数: {wrap_usage}")
    print(f"   📊 剩余裸返回: {len(naked_returns)}")
    print(f"   📊 文件日志剩余: {file_log_count}")
    print()
    
    # 总评
    print("=" * 60)
    all_pass = (
        len(naked_returns) == 0 and
        has_wrap_function and
        garbled_count == 0 and
        file_log_count == 0 and
        has_logging
    )
    
    if all_pass:
        print("🎉 总评：所有核心问题已修复，代码质量达标！")
    else:
        print("⚠️ 总评：部分问题仍需修复，请查看上述详情")
    print("=" * 60)
    
    return all_pass

if __name__ == "__main__":
    success = check_fix_quality()
    sys.exit(0 if success else 1)

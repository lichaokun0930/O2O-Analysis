#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 html.Style() 修复
验证 Dash 3.x 兼容性
"""
import sys
import io

# ⚡ 解决 Windows PowerShell 下 emoji 输出乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("🔍 测试 html.Style() 修复")
print("=" * 60)

# 测试1: 检查 Dash 版本
print("\n1️⃣ 检查 Dash 版本...")
try:
    import dash
    print(f"   ✅ Dash 版本: {dash.__version__}")
    
    # 检查 html.Style 是否存在
    from dash import html
    if hasattr(html, 'Style'):
        print(f"   ⚠️  html.Style 存在（旧版本）")
    else:
        print(f"   ✅ html.Style 不存在（Dash 3.x）")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试2: 验证 html.Style 不存在
print("\n2️⃣ 验证 html.Style 已移除...")
try:
    from dash import html
    
    # 旧用法（Dash 2.x，会报错）
    # style_old = html.Style("body { color: red; }")
    
    # Dash 3.x: html.Style 不存在，样式应通过以下方式应用：
    # 1. DataTable 的 style_cell、style_header、style_data_conditional 属性
    # 2. assets/custom.css 文件
    # 3. app.index_string 注入
    
    # 验证 html.Style 确实不存在
    if not hasattr(html, 'Style'):
        print(f"   ✅ 确认 html.Style 已移除")
        print(f"   📝 样式应通过组件属性或 assets 文件应用")
    else:
        print(f"   ⚠️  html.Style 仍然存在（不应该）")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试3: 导入修复后的模块
print("\n3️⃣ 测试修复后的模块...")
try:
    from components.today_must_do.skeleton_screens import inject_skeleton_css
    print(f"   ✅ skeleton_screens 导入成功")
    
    # 测试函数调用
    result = inject_skeleton_css(None)
    print(f"   ✅ inject_skeleton_css() 调用成功")
    print(f"   📝 返回类型: {type(result)}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试4: 检查 callbacks.py 语法
print("\n4️⃣ 检查 callbacks.py 语法...")
try:
    import ast
    with open('components/today_must_do/callbacks.py', 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print(f"   ✅ callbacks.py 语法正确")
except SyntaxError as e:
    print(f"   ❌ 语法错误: {e}")
    print(f"      行号: {e.lineno}")
    print(f"      位置: {e.offset}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
print("\n💡 修复说明:")
print("   • html.Style() 在 Dash 3.x 中已完全移除")
print("   • 样式应通过以下方式应用:")
print("     1. DataTable 的 style_* 属性（推荐）")
print("     2. assets/custom.css 文件")
print("     3. app.index_string 注入")
print("   • 已修复文件:")
print("     - components/today_must_do/skeleton_screens.py")
print("     - components/today_must_do/callbacks.py")

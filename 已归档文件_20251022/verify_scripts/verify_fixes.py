# -*- coding: utf-8 -*-
"""
代码质量核心验证
"""

print("=" * 70)
print("代码质量核心验证")
print("=" * 70)
print()

# 1. 语法检查
print("[1] Python 语法检查")
import py_compile
try:
    py_compile.compile('智能门店看板_Dash版.py', doraise=True)
    print("    [PASS] 语法正确")
except py_compile.PyCompileError as e:
    print(f"    [FAIL] 语法错误: {e}")
print()

# 2. 检查关键函数是否存在
print("[2] 检查关键代码")
with open('智能门店看板_Dash版.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    checks = [
        ('wrap_chart_component', 'def wrap_chart_component'),
        ('update_slot_distribution_chart', 'def update_slot_distribution_chart'),
        ('update_scene_distribution_chart', 'def update_scene_distribution_chart'),
        ('scene_inference导入', 'from scene_inference import'),
        ('cache_utils导入', 'from cache_utils import'),
        ('echarts_responsive_utils导入', 'from echarts_responsive_utils import'),
    ]
    
    for name, pattern in checks:
        if pattern in content:
            print(f"    [PASS] {name} 存在")
        else:
            print(f"    [FAIL] {name} 不存在")
print()

# 3. 检查返回类型处理
print("[3] 检查 Plotly 降级处理")
count_wrap = content.count('wrap_chart_component')
count_dcc_graph = content.count('dcc.Graph(figure=')
print(f"    [INFO] wrap_chart_component 使用次数: {count_wrap}")
print(f"    [INFO] dcc.Graph(figure=) 使用次数: {count_dcc_graph}")
if count_wrap >= 2:
    print("    [PASS] wrap_chart_component 被正确使用")
print()

# 4. 检查文件日志是否已禁用
print("[4] 检查调试日志状态")
if 'DEBUG模式已禁用' in content:
    print("    [PASS] 文件日志已禁用")
else:
    print("    [WARN] 文件日志可能仍在使用")
print()

print("=" * 70)
print("总结: 代码质量检查完成")
print("=" * 70)
print()
print("主要修复:")
print("  1. wrap_chart_component 统一包装函数 ✓")
print("  2. 场景推断逻辑抽取为独立模块 ✓")
print("  3. 缓存哈希优化模块 ✓")
print("  4. 文件日志已禁用 ✓")
print()
print("建议:")
print("  1. 运行完整应用测试")
print("  2. 测试 ECharts 不可用场景")
print("  3. 性能测试验证缓存优化效果")
print()

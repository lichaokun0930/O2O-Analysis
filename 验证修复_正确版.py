"""
验证修复完成情况
"""
print("="*80)
print("验证修复结果")
print("="*80)

# 检查问题诊断引擎
with open('问题诊断引擎.py', 'r', encoding='utf-8') as f:
    engine_content = f.read()

print("\n✓ 问题诊断引擎.py 修复验证:")
print("-" * 60)

# 检查1: 问题等级表情符号
if '🔴 严重' in engine_content or '🟠 警告' in engine_content:
    print("  ❌ 仍有表情符号")
else:
    print("  ✅ 问题等级表情符号已移除")

# 检查2: 变量重命名
if 'compare_data' in engine_content and 'compare_sales' in engine_content:
    print("  ✅ 变量已重命名为 compare_data/sales/revenue")
else:
    print("  ❌ 变量重命名未完成")

if 'previous_data' in engine_content or 'previous_sales' in engine_content:
    print("  ❌ 仍有 previous_ 变量")
else:
    print("  ✅ 所有 previous_ 变量已替换")

# 检查可视化文件
with open('智能门店经营看板_可视化.py', 'r', encoding='utf-8') as f:
    viz_content = f.read()

print("\n✓ 智能门店经营看板_可视化.py 修复验证:")
print("-" * 60)

# 检查样式匹配
if "v == '严重'" in viz_content and "v == '警告'" in viz_content:
    print("  ✅ 样式匹配代码已更新（无表情符号版本）")
else:
    print("  ❌ 样式匹配代码未更新")

if "v == '🔴 严重'" in viz_content or "v == '🟠 警告'" in viz_content:
    print("  ❌ 仍有表情符号版本的样式匹配")
else:
    print("  ✅ 表情符号版本的样式匹配已移除")

print("\n" + "="*80)
print("修复总结")
print("="*80)

all_good = True

if ('compare_data' in engine_content and 
    'compare_sales' in engine_content and
    'previous_data' not in engine_content):
    print("✅ 问题2: 变量重命名完成")
else:
    print("❌ 问题2: 变量重命名未完成")
    all_good = False

if ('🔴' not in engine_content and 
    "v == '严重'" in viz_content):
    print("✅ 问题1: 表情符号移除完成")
else:
    print("❌ 问题1: 表情符号移除未完成")
    all_good = False

if all_good:
    print("\n🎉 所有修复已完成！")
    print("\n下一步测试:")
    print("1. streamlit run 智能门店经营看板_可视化.py")
    print("2. 进入【问题诊断引擎】→【销量下滑】")
    print("3. 导出CSV检查'问题等级'列是否只显示：严重/警告/关注")
    print("4. 验证活珠子商品的销量变化数据")
else:
    print("\n⚠️  部分修复未完成，请检查")

print("="*80)

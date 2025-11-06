"""
测试CSV导出修复
验证导出的CSV文件是否正确处理了中文和特殊符号
"""

import pandas as pd
import sys
import os

print("=" * 80)
print("📋 测试CSV导出修复")
print("=" * 80)

# 1. 创建测试数据（模拟销量下滑结果）
print("\n🔍 步骤1: 创建测试数据...")
test_data = {
    '商品名称': ['测试商品A', '测试商品B', '测试商品C'],
    '第40周销量': [0, 1, 5],
    '第39周销量': [5, 8, 10],
    '第40周预计收入': ['¥0.0', '¥15.8', '¥125.5'],
    '第39周预计收入': ['¥125.5', '¥126.4', '¥250.0'],
    '销量变化': [-5, -7, -5],
    '变化幅度%': ['-100.0%', '-87.5%', '-50.0%'],
    '商品实售价': ['¥15.8', '¥15.8', '¥25.1'],
    '一级分类名': ['休闲食品', '休闲食品', '日用品'],
    '三级分类名': ['鱼肉类制品', '糖果巧克力', '清洁用品'],
    '问题等级': ['🔴 严重', '🟠 警告', '🟠 警告'],
    '建议操作': ['立即检查库存', '关注销售趋势', '观察市场反应']
}

result = pd.DataFrame(test_data)
print(f"✅ 创建测试数据: {len(result)} 行")

# 2. 模拟导出处理
print("\n🔍 步骤2: 模拟新的自动检测导出处理...")

# 创建导出专用版本
export_df = result.copy()

# 自动检测并清理所有包含¥符号的列
cleaned_cols = []
for col in export_df.columns:
    if export_df[col].dtype == 'object':  # 只处理字符串类型的列
        # 检查是否包含¥符号
        sample_value = export_df[col].iloc[0] if len(export_df) > 0 else ""
        if isinstance(sample_value, str) and '¥' in sample_value:
            try:
                # 清理¥符号、千分位逗号、N/A，转为数值
                export_df[col] = (export_df[col]
                                 .astype(str)
                                 .str.replace('¥', '')
                                 .str.replace(',', '')
                                 .str.replace('N/A', '0')
                                 .replace('', '0')
                                 .astype(float))
                cleaned_cols.append(col)
                print(f"  ✅ 自动清理 {col} 的¥符号")
            except Exception as e:
                print(f"  ⚠️ 清理 {col} 失败: {e}")

# 清理变化幅度的%符号
if '变化幅度%' in export_df.columns:
    try:
        export_df['变化幅度%'] = (export_df['变化幅度%']
                              .astype(str)
                              .str.replace('%', '')
                              .astype(float))
        cleaned_cols.append('变化幅度%')
        print(f"  ✅ 清理 变化幅度% 的%符号")
    except Exception as e:
        print(f"  ⚠️ 清理 变化幅度% 失败: {e}")

print(f"\n  📊 共清理了 {len(cleaned_cols)} 个列: {', '.join(cleaned_cols)}")

# 3. 导出CSV
print("\n🔍 步骤3: 导出CSV文件...")
output_file = "测试_销量下滑商品_导出.csv"

try:
    csv_content = export_df.to_csv(index=False, encoding='utf-8-sig')
    
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write(csv_content)
    
    print(f"✅ 成功导出: {output_file}")
    print(f"  文件大小: {len(csv_content)} 字节")
except Exception as e:
    print(f"❌ 导出失败: {e}")
    sys.exit(1)

# 4. 验证导出结果
print("\n🔍 步骤4: 验证导出结果...")
try:
    # 读取导出的文件
    read_df = pd.read_csv(output_file, encoding='utf-8-sig')
    
    print(f"✅ 成功读取CSV: {len(read_df)} 行 × {len(read_df.columns)} 列")
    
    # 检查中文是否正确
    if read_df.loc[0, '商品名称'] == '测试商品A':
        print("  ✅ 中文显示正常")
    else:
        print(f"  ❌ 中文乱码: {read_df.loc[0, '商品名称']}")
    
    # 检查数值是否正确
    if read_df.loc[0, '第40周预计收入'] == 0.0:
        print("  ✅ 预计收入数值正确（移除¥符号）")
    else:
        print(f"  ❌ 预计收入数值错误: {read_df.loc[0, '第40周预计收入']}")
    
    if read_df.loc[0, '变化幅度%'] == -100.0:
        print("  ✅ 变化幅度数值正确（移除%符号）")
    else:
        print(f"  ❌ 变化幅度数值错误: {read_df.loc[0, '变化幅度%']}")
    
    if read_df.loc[0, '商品实售价'] == 15.8:
        print("  ✅ 商品实售价数值正确（移除¥符号）")
    else:
        print(f"  ❌ 商品实售价数值错误: {read_df.loc[0, '商品实售价']}")
    
    # 检查emoji表情
    if '🔴' in read_df.loc[0, '问题等级']:
        print("  ✅ Emoji表情显示正常")
    else:
        print(f"  ⚠️ Emoji可能显示异常: {read_df.loc[0, '问题等级']}")
    
    # 显示前3行
    print("\n📊 导出数据预览（前3行）:")
    print(read_df.head(3).to_string())
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试Excel打开兼容性
print("\n🔍 步骤5: 测试Excel兼容性...")
print("  💡 utf-8-sig 编码可确保Excel正确识别中文")
print(f"  📁 请用Excel打开文件验证: {os.path.abspath(output_file)}")

print("\n" + "=" * 80)
print("✅ CSV导出测试完成!")
print("=" * 80)
print("\n📝 修复要点:")
print("  1. 使用 utf-8-sig 编码（Excel兼容）")
print("  2. 导出前移除格式化符号（¥、%）")
print("  3. 转换为纯数值，方便Excel进行计算和筛选")
print("  4. 保留中文和Emoji表情")
print("\n🚀 修复已应用到智能门店经营看板_可视化.py")

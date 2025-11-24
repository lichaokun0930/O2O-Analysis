"""
库存数据诊断脚本
快速检查库存数据是否正确读取到看板
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.data_source_manager import DataSourceManager

print("="*80)
print("库存数据诊断")
print("="*80)

# 初始化数据源管理器
manager = DataSourceManager()

# 加载数据(最近7天)
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\n加载数据: {start_date.date()} 至 {end_date.date()}")

result = manager.load_from_database(
    store_name="惠宜选超市（徐州祥和路店）",
    start_date=start_date,
    end_date=end_date
)

df = result['display']

print(f"\n数据形状: {df.shape}")
print(f"总记录数: {len(df)}")

# 检查库存字段
print("\n" + "-"*80)
print("库存字段检查")
print("-"*80)

stock_cols = [col for col in df.columns if '库存' in col or 'stock' in col.lower()]
print(f"\n库存相关列: {stock_cols}")

if stock_cols:
    for col in stock_cols:
        print(f"\n【{col}】")
        print(f"  非空记录: {df[col].notna().sum()}")
        print(f"  大于0记录: {(df[col] > 0).sum()}")
        print(f"  平均值: {df[col].mean():.2f}")
        print(f"  最大值: {df[col].max():.2f}")
        print(f"  最小值: {df[col].min():.2f}")
        
        # 显示有库存的样本数据
        has_stock = df[df[col] > 0]
        if len(has_stock) > 0:
            print(f"\n  有库存的样本数据(前5条):")
            print(has_stock[['商品名称', col, '日期']].head().to_string(index=False))
else:
    print("\n❌ 数据中没有库存字段!")
    print(f"\n所有列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

# 检查一级分类
print("\n" + "-"*80)
print("一级分类统计")
print("-"*80)

if '一级分类名' in df.columns:
    category_stats = df.groupby('一级分类名').agg({
        '商品名称': 'nunique',
        '剩余库存': lambda x: (x > 0).sum() if '剩余库存' in df.columns else 0
    })
    category_stats.columns = ['商品数', '有库存记录数']
    print(category_stats)

print("\n" + "="*80)
print("诊断完成!")
print("="*80)

if stock_cols and (df[stock_cols[0]] > 0).sum() > 0:
    print("\n✅ 库存数据正常")
    print("\n下一步: 重启看板验证")
    print("  .\\启动看板.ps1")
else:
    print("\n❌ 库存数据异常")
    print("\n可能原因:")
    print("  1. Excel文件没有'剩余库存'列")
    print("  2. 导入脚本没有读取库存字段")
    print("  3. 数据源管理器没有映射库存字段")

"""查看数据库字段结构和营销相关数据"""
import pandas as pd
from database.data_source_manager import DataSourceManager

DATA_SOURCE_MANAGER = DataSourceManager()
df = DATA_SOURCE_MANAGER.load_from_database(store_name='共橙超市-南通海安店')

print("=" * 60)
print("所有字段列表:")
print("=" * 60)
for i, col in enumerate(df.columns.tolist(), 1):
    print(f'{i:2d}. {col}')

print("\n" + "=" * 60)
print("营销相关字段:")
print("=" * 60)
marketing_keywords = ['营销', '活动', '优惠', '减免', '立减', '满减', '折扣', '券', '补贴', '赠']
marketing_cols = [col for col in df.columns if any(kw in col for kw in marketing_keywords)]
print('\n'.join(marketing_cols))
print(f'\n共 {len(marketing_cols)} 个营销相关字段')

if marketing_cols:
    print("\n" + "=" * 60)
    print("营销字段样例数据 (前5行):")
    print("=" * 60)
    print(df[marketing_cols].head(5).to_string())
    
    print("\n" + "=" * 60)
    print("营销字段统计摘要:")
    print("=" * 60)
    for col in marketing_cols:
        if df[col].dtype in ['float64', 'int64']:
            total = df[col].sum()
            non_zero = (df[col] > 0).sum()
            print(f"{col}: 总额={total:,.2f}, 非零记录={non_zero}/{len(df)} ({non_zero/len(df)*100:.1f}%)")
        else:
            unique_count = df[col].nunique()
            print(f"{col}: {unique_count} 个不同值")

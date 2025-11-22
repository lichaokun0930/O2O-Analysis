from database.data_source_manager import DataSourceManager
import pandas as pd

mgr = DataSourceManager()
result = mgr.load_from_database(store_name='惠宜选超市（徐州祥和路店）')
df = result['full']

print(f"数据行数: {len(df):,}")
print(f"\n库存字段检查:")

if '剩余库存' in df.columns:
    print(f"  剩余库存字段存在: ✅")
    has_stock = (df['剩余库存'] > 0).sum()
    print(f"  有库存的记录: {has_stock:,} / {len(df):,} ({has_stock/len(df)*100:.1f}%)")
    print(f"  平均库存: {df['剩余库存'].mean():.1f}")
    
    print(f"\n示例数据 (前5行):")
    print(df[['商品名称', '销量', '剩余库存']].head(5).to_string(index=False))
else:
    print("  ❌ 剩余库存字段不存在!")
    print(f"  可用字段: {df.columns.tolist()}")

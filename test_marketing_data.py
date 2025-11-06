"""测试数据库营销活动数据加载"""
from database.data_source_manager import DataSourceManager

mgr = DataSourceManager()
df = mgr.load_from_database(store_name='共橙超市-徐州新沂2店')

print(f'\n加载数据: {len(df)} 行')
print(f'\n营销活动字段检查:')
print(f'  满减金额: ¥{df["满减金额"].sum():.2f}')
print(f'  商品减免金额: ¥{df["商品减免金额"].sum():.2f}')
print(f'  商家代金券: ¥{df["商家代金券"].sum():.2f}')
print(f'  配送费减免: ¥{df["配送费减免金额"].sum():.2f}')
print(f'  商家承担部分券: ¥{df["商家承担部分券"].sum():.2f}')
print(f'  打包袋金额: ¥{df["打包袋金额"].sum():.2f}')

# 计算商家活动成本
merchant_cost = (
    df['满减金额'].fillna(0) +
    df['商品减免金额'].fillna(0) +
    df['商家代金券'].fillna(0) +
    df['商家承担部分券'].fillna(0)
).sum()

print(f'\n商家活动总成本: ¥{merchant_cost:.2f}')

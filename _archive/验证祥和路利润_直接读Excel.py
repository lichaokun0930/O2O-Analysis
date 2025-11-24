shujuk """
直接读取Excel文件验证祥和路店美团闪购利润
"""
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("🔍 验证祥和路店美团闪购利润 (直接读取Excel)")
print("="*80)

# 读取文件
excel_file = Path("实际数据/2025-10-25 00_00_00至2025-11-23 23_59_59订单明细数据导出汇总.xlsx")

if not excel_file.exists():
    print(f"❌ 文件不存在: {excel_file}")
    exit(1)

print(f"\n📂 读取文件: {excel_file.name}")
df = pd.read_excel(excel_file)

print(f"✅ 总行数: {len(df):,}")
print(f"✅ 总订单数: {df['订单ID'].nunique():,}")

# 查看列名
print(f"\n📋 数据列:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i}. {col}")

# 查看门店名称
print(f"\n🏪 门店列表:")
stores = df['门店'].unique() if '门店' in df.columns else df['门店名称'].unique() if '门店名称' in df.columns else []
for store in stores:
    count = len(df[df['门店'] == store]) if '门店' in df.columns else len(df[df['门店名称'] == store])
    print(f"   {store}: {count:,} 行")

# 查看渠道
print(f"\n📱 渠道列表:")
channels = df['渠道'].unique() if '渠道' in df.columns else []
for channel in channels:
    count = len(df[df['渠道'] == channel])
    print(f"   {channel}: {count:,} 行")

# 祥和路店数据
store_col = '门店' if '门店' in df.columns else '门店名称'
df_xianghelu = df[df[store_col].str.contains('祥和路', na=False)].copy()

if len(df_xianghelu) == 0:
    print(f"\n❌ 没有找到祥和路店数据!")
    print(f"\n完整门店列表:")
    print(df[store_col].unique())
else:
    print(f"\n✅ 祥和路店数据: {len(df_xianghelu):,} 行, {df_xianghelu['订单ID'].nunique():,} 订单")
    
    # 美团闪购数据
    df_mt = df_xianghelu[df_xianghelu['渠道'] == '美团闪购'].copy()
    
    if len(df_mt) == 0:
        print(f"\n❌ 祥和路店没有美团闪购数据!")
        print(f"\n祥和路店的渠道:")
        print(df_xianghelu['渠道'].unique())
    else:
        print(f"\n✅ 美团闪购数据: {len(df_mt):,} 行, {df_mt['订单ID'].nunique():,} 订单")
        
        # 方法1: 简单sum
        print(f"\n{'='*80}")
        print("方法1: 直接sum(可能错误)")
        print("="*80)
        simple_profit = df_mt['利润额'].sum() if '利润额' in df_mt.columns else 0
        simple_service = df_mt['平台服务费'].sum() if '平台服务费' in df_mt.columns else 0
        simple_delivery = df_mt['物流配送费'].sum() if '物流配送费' in df_mt.columns else 0
        simple_actual = simple_profit - simple_service - simple_delivery
        
        print(f"利润额: ¥{simple_profit:,.2f}")
        print(f"平台服务费: ¥{simple_service:,.2f}")
        print(f"物流配送费: ¥{simple_delivery:,.2f}")
        print(f"订单实际利润: ¥{simple_actual:,.2f}")
        
        # 方法2: 按订单聚合
        print(f"\n{'='*80}")
        print("方法2: 按订单聚合(正确方法)")
        print("="*80)
        
        df_mt['订单ID'] = df_mt['订单ID'].astype(str)
        
        order_agg = df_mt.groupby('订单ID').agg({
            '利润额': 'sum',
            '平台服务费': 'sum',
            '物流配送费': 'first',
        }).reset_index()
        
        print(f"聚合后订单数: {len(order_agg):,}")
        
        order_agg['订单实际利润'] = (
            order_agg['利润额'] 
            - order_agg['平台服务费'] 
            - order_agg['物流配送费']
        )
        
        total_profit = order_agg['利润额'].sum()
        total_service = order_agg['平台服务费'].sum()
        total_delivery = order_agg['物流配送费'].sum()
        total_actual = order_agg['订单实际利润'].sum()
        
        print(f"利润额: ¥{total_profit:,.2f}")
        print(f"平台服务费: ¥{total_service:,.2f}")
        print(f"物流配送费: ¥{total_delivery:,.2f}")
        print(f"订单实际利润: ¥{total_actual:,.2f}")
        
        # 检查服务费=0的订单
        zero_fee_orders = order_agg[order_agg['平台服务费'] <= 0]
        if len(zero_fee_orders) > 0:
            print(f"\n⚠️ 发现 {len(zero_fee_orders)} 个服务费=0的订单")
            print(f"   这些订单的实际利润: ¥{zero_fee_orders['订单实际利润'].sum():,.2f}")
            
            filtered_agg = order_agg[order_agg['平台服务费'] > 0]
            filtered_actual = filtered_agg['订单实际利润'].sum()
            print(f"\n✅ 剔除后的订单实际利润: ¥{filtered_actual:,.2f}")

print(f"\n{'='*80}")

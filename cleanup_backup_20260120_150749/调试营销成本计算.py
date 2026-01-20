"""
调试营销成本计算 - 直接调用后端函数
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime

# 导入后端函数
from app.api.v1.orders import calculate_order_metrics, calculate_channel_metrics

# 数据库配置
DATABASE_URL = "postgresql+pg8000://postgres:postgres@localhost:5432/o2o_dashboard"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 100)
print("调试营销成本计算")
print("=" * 100)
print(f"测试门店: {TEST_STORE}")
print(f"测试日期: {START_DATE} 至 {END_DATE}")
print()

# 查询数据
print("步骤1: 从数据库查询数据...")
query = text("""
    SELECT *
    FROM orders
    WHERE "门店名称" = :store_name
        AND "订单完成时间" >= :start_date
        AND "订单完成时间" < :end_date::date + interval '1 day'
        AND "订单状态" = '订单完成'
""")

with Session() as session:
    result = session.execute(query, {
        "store_name": TEST_STORE,
        "start_date": START_DATE,
        "end_date": END_DATE
    })
    
    rows = result.fetchall()
    columns = result.keys()
    df = pd.DataFrame(rows, columns=columns)

print(f"✅ 查询到 {len(df)} 条订单数据")
print()

# 按渠道分组测试
print("步骤2: 测试各渠道的营销成本计算...")
print("-" * 100)

for channel in ['饿了么', '美团共橙']:
    channel_df = df[df['渠道'] == channel].copy()
    
    if channel_df.empty:
        print(f"{channel}: 无数据")
        continue
    
    print(f"\n【{channel}】")
    print(f"  原始订单数: {len(channel_df)}")
    
    # 调用calculate_order_metrics
    order_agg = calculate_order_metrics(channel_df)
    print(f"  聚合后订单数: {len(order_agg)}")
    
    # 检查商家活动成本字段
    if '商家活动成本' in order_agg.columns:
        marketing_total = order_agg['商家活动成本'].sum()
        print(f"  商家活动成本总额: ¥{marketing_total:.2f}")
        print(f"  单均营销: ¥{marketing_total / len(order_agg):.2f}")
        
        # 打印各个营销字段的值
        print(f"  营销字段明细:")
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', 
                           '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
        for field in marketing_fields:
            if field in order_agg.columns:
                value = order_agg[field].sum()
                print(f"    {field}: ¥{value:.2f}")
    else:
        print(f"  ⚠️ 缺少'商家活动成本'字段")
    
    # 调用calculate_channel_metrics
    print(f"\n  调用calculate_channel_metrics:")
    metrics = calculate_channel_metrics(channel_df)
    print(f"    订单数: {metrics['order_count']}")
    print(f"    单均营销: ¥{metrics['avg_marketing_per_order']:.2f}")
    print(f"    单均配送: ¥{metrics['avg_delivery_per_order']:.2f}")

print()
print("=" * 100)
print("调试完成")
print("=" * 100)

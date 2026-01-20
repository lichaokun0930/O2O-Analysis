"""
直接测试营销成本计算逻辑
不依赖API，直接从数据库读取数据并计算
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime

# 数据库配置
DATABASE_URL = "sqlite:///订单数据看板/订单数据看板/实际数据/orders.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 80)
print("直接测试营销成本计算逻辑")
print("=" * 80)
print(f"测试门店: {TEST_STORE}")
print(f"测试日期: {START_DATE} 至 {END_DATE}")
print()

# 查询数据
print("步骤1: 从数据库查询数据...")
query = text("""
    SELECT 
        渠道,
        COUNT(*) as order_count,
        -- 8个营销字段
        SUM(COALESCE(配送费减免金额, 0)) as 配送费减免,
        SUM(COALESCE(满减金额, 0)) as 满减,
        SUM(COALESCE(商品减免金额, 0)) as 商品减免,
        SUM(COALESCE(商家代金券, 0)) as 商家代金券,
        SUM(COALESCE(商家承担部分券, 0)) as 商家承担部分券,
        SUM(COALESCE(满赠金额, 0)) as 满赠,
        SUM(COALESCE(商家其他优惠, 0)) as 商家其他优惠,
        SUM(COALESCE(新客减免金额, 0)) as 新客减免,
        -- 配送相关
        SUM(COALESCE(物流配送费, 0)) as 物流配送费,
        SUM(COALESCE(用户支付配送费, 0)) as 用户支付配送费
    FROM orders
    WHERE 门店名称 = :store_name
        AND 订单完成时间 >= :start_date
        AND 订单完成时间 < date(:end_date, '+1 day')
        AND 订单状态 = '订单完成'
    GROUP BY 渠道
    ORDER BY order_count DESC
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

print(f"✅ 查询到 {len(df)} 个渠道的数据")
print()

# 计算营销成本
print("步骤2: 计算营销成本...")
print("-" * 80)
print(f"{'渠道':<20} {'订单数':>10} {'营销总额':>12} {'单均营销':>12} {'配送总额':>12} {'单均配送':>12}")
print("-" * 80)

for _, row in df.iterrows():
    channel = row['渠道']
    order_count = row['order_count']
    
    # 计算营销总成本（8个字段）
    marketing_total = (
        row['配送费减免'] +
        row['满减'] +
        row['商品减免'] +
        row['商家代金券'] +
        row['商家承担部分券'] +
        row['满赠'] +
        row['商家其他优惠'] +
        row['新客减免']
    )
    
    # 计算单均营销
    avg_marketing = marketing_total / order_count if order_count > 0 else 0
    
    # 计算配送净成本
    delivery_net = row['物流配送费'] - row['用户支付配送费'] + row['配送费减免']
    avg_delivery = delivery_net / order_count if order_count > 0 else 0
    
    print(f"{channel:<20} {order_count:>10} {marketing_total:>12.2f} {avg_marketing:>12.2f} {delivery_net:>12.2f} {avg_delivery:>12.2f}")

print("-" * 80)
print()

# 详细分解（饿了么和美团共橙）
print("步骤3: 详细分解营销成本（饿了么和美团共橙）...")
print()

for channel_name in ["饿了么", "美团共橙"]:
    channel_data = df[df['渠道'] == channel_name]
    if len(channel_data) == 0:
        continue
    
    row = channel_data.iloc[0]
    order_count = row['order_count']
    
    print(f"【{channel_name}】")
    print(f"  订单数: {order_count}")
    print(f"  营销成本明细:")
    print(f"    1. 配送费减免金额: {row['配送费减免']:.2f} (单均: {row['配送费减免']/order_count:.2f})")
    print(f"    2. 满减金额: {row['满减']:.2f} (单均: {row['满减']/order_count:.2f})")
    print(f"    3. 商品减免金额: {row['商品减免']:.2f} (单均: {row['商品减免']/order_count:.2f})")
    print(f"    4. 商家代金券: {row['商家代金券']:.2f} (单均: {row['商家代金券']/order_count:.2f})")
    print(f"    5. 商家承担部分券: {row['商家承担部分券']:.2f} (单均: {row['商家承担部分券']/order_count:.2f})")
    print(f"    6. 满赠金额: {row['满赠']:.2f} (单均: {row['满赠']/order_count:.2f})")
    print(f"    7. 商家其他优惠: {row['商家其他优惠']:.2f} (单均: {row['商家其他优惠']/order_count:.2f})")
    print(f"    8. 新客减免金额: {row['新客减免']:.2f} (单均: {row['新客减免']/order_count:.2f})")
    
    marketing_total = (
        row['配送费减免'] + row['满减'] + row['商品减免'] + row['商家代金券'] +
        row['商家承担部分券'] + row['满赠'] + row['商家其他优惠'] + row['新客减免']
    )
    avg_marketing = marketing_total / order_count
    
    print(f"  营销总成本: {marketing_total:.2f}")
    print(f"  单均营销: {avg_marketing:.2f}")
    print()

print("=" * 80)
print("测试完成")
print("=" * 80)
print()
print("对比Dash版本的预期值:")
print("  饿了么: 单均营销 7.87, 单均配送 1.61")
print("  美团共橙: 单均营销 10.17, 单均配送 3.89")

# -*- coding: utf-8 -*-
"""
验证单均配送费修复

对比 Dash 版本和 React 版本的单均配送费计算

问题：
- Dash 版本：单均配送费 = 配送净成本 / 订单数
- React 版本（修复前）：单均配送费 = 物流配送费 / 订单数

配送净成本公式：
配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返

以惠宜选-泰州泰兴店为例验证
"""

import pandas as pd
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order

def load_store_data(store_name: str, channel_prefix: str = None) -> pd.DataFrame:
    """加载指定门店的数据"""
    session = SessionLocal()
    try:
        query = session.query(Order).filter(Order.store_name == store_name)
        
        if channel_prefix:
            query = query.filter(Order.order_number.like(f'{channel_prefix}%'))
        
        orders = query.all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '渠道': order.channel,
                '物流配送费': float(order.delivery_fee or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_metrics(df: pd.DataFrame) -> dict:
    """计算订单级指标"""
    if df.empty:
        return {}
    
    # 订单级聚合
    order_agg = df.groupby('订单ID').agg({
        '物流配送费': 'first',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '企客后返': 'sum',  # 商品级字段
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '满赠金额': 'first',
        '商家其他优惠': 'first',
        '新客减免金额': 'first',
    }).reset_index()
    
    # 计算配送净成本（Dash 版本公式）
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] -
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
        order_agg['企客后返']
    )
    
    # 计算商家活动成本（7个营销字段）
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                       '满赠金额', '商家其他优惠', '新客减免金额']
    order_agg['商家活动成本'] = sum(order_agg[field].fillna(0) for field in marketing_fields)
    
    order_count = len(order_agg)
    
    return {
        'order_count': order_count,
        'total_delivery_fee': order_agg['物流配送费'].sum(),
        'total_delivery_cost': order_agg['配送净成本'].sum(),
        'total_marketing_cost': order_agg['商家活动成本'].sum(),
        'avg_delivery_fee_old': order_agg['物流配送费'].sum() / order_count if order_count > 0 else 0,
        'avg_delivery_fee_new': order_agg['配送净成本'].sum() / order_count if order_count > 0 else 0,
        'avg_marketing_cost': order_agg['商家活动成本'].sum() / order_count if order_count > 0 else 0,
    }


def main():
    store_name = "惠宜选-泰州泰兴店"
    
    print("="*80)
    print(f"验证单均配送费修复 - {store_name}")
    print("="*80)
    
    # 测试美团渠道（SG前缀）
    print("\n📊 美团渠道 (SG前缀):")
    print("-"*60)
    df_meituan = load_store_data(store_name, 'SG')
    if not df_meituan.empty:
        metrics = calculate_metrics(df_meituan)
        print(f"  订单数: {metrics['order_count']}")
        print(f"  物流配送费总计: ¥{metrics['total_delivery_fee']:.2f}")
        print(f"  配送净成本总计: ¥{metrics['total_delivery_cost']:.2f}")
        print(f"  商家活动成本总计: ¥{metrics['total_marketing_cost']:.2f}")
        print(f"  单均配送费(旧-物流配送费): ¥{metrics['avg_delivery_fee_old']:.2f}")
        print(f"  单均配送费(新-配送净成本): ¥{metrics['avg_delivery_fee_new']:.2f}")
        print(f"  单均营销费: ¥{metrics['avg_marketing_cost']:.2f}")
    else:
        print("  无数据")
    
    # 测试饿了么渠道（ELE前缀）
    print("\n📊 饿了么渠道 (ELE前缀):")
    print("-"*60)
    df_ele = load_store_data(store_name, 'ELE')
    if not df_ele.empty:
        metrics = calculate_metrics(df_ele)
        print(f"  订单数: {metrics['order_count']}")
        print(f"  物流配送费总计: ¥{metrics['total_delivery_fee']:.2f}")
        print(f"  配送净成本总计: ¥{metrics['total_delivery_cost']:.2f}")
        print(f"  商家活动成本总计: ¥{metrics['total_marketing_cost']:.2f}")
        print(f"  单均配送费(旧-物流配送费): ¥{metrics['avg_delivery_fee_old']:.2f}")
        print(f"  单均配送费(新-配送净成本): ¥{metrics['avg_delivery_fee_new']:.2f}")
        print(f"  单均营销费: ¥{metrics['avg_marketing_cost']:.2f}")
    else:
        print("  无数据")
    
    print("\n" + "="*80)
    print("📋 Dash 版本参考值:")
    print("  美团渠道: 单均配送 ¥3.89")
    print("  饿了么渠道: 单均配送 ¥1.61")
    print("="*80)
    
    print("\n✅ 修复说明:")
    print("  - 旧版本使用'物流配送费'计算单均配送费")
    print("  - 新版本使用'配送净成本'计算单均配送费（与Dash版本一致）")
    print("  - 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返")


if __name__ == "__main__":
    main()

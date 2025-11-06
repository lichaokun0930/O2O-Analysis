"""
按照业务逻辑最终确认.md中的公式计算如皋店配送成本
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.models import Order
from database.connection import SessionLocal
import pandas as pd

def calculate_delivery_cost_by_doc():
    print("=" * 80)
    print("📋 按业务逻辑文档计算如皋店配送成本")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # 1. 从数据库加载如皋店数据
        print("\n【步骤1: 加载如皋店数据】")
        print("-" * 80)
        
        rugao_orders = db.query(Order).filter(
            Order.store_name == '惠宜选-南通如皋店'
        ).all()
        
        print(f"加载记录数: {len(rugao_orders):,}")
        
        # 2. 转换为DataFrame
        data = []
        for order in rugao_orders:
            data.append({
                '订单ID': order.order_id,
                '用户支付配送费': order.user_paid_delivery_fee or 0,
                '配送费减免金额': order.delivery_discount or 0,
                '物流配送费': order.delivery_fee or 0,
            })
        
        df = pd.DataFrame(data)
        print(f"DataFrame行数: {len(df):,}")
        
        # 3. 按订单聚合(订单级字段用first)
        print("\n【步骤2: 按订单ID聚合】")
        print("-" * 80)
        
        order_agg = df.groupby('订单ID').agg({
            '用户支付配送费': 'first',
            '配送费减免金额': 'first',
            '物流配送费': 'first'
        }).reset_index()
        
        print(f"聚合后订单数: {len(order_agg):,}")
        print(f"\n示例数据(前10个订单):")
        print(order_agg.head(10).to_string())
        
        # 4. 按文档公式计算配送成本
        print("\n【步骤3: 计算配送成本】")
        print("-" * 80)
        print("\n📋 业务逻辑文档公式:")
        print("   配送成本 = 用户支付配送费 - 配送费减免金额 - 物流配送费")
        print()
        
        order_agg['配送成本'] = (
            order_agg['用户支付配送费'] - 
            order_agg['配送费减免金额'] - 
            order_agg['物流配送费']
        )
        
        # 5. 统计分析
        print("【步骤4: 统计分析】")
        print("-" * 80)
        
        total_user_paid = order_agg['用户支付配送费'].sum()
        total_discount = order_agg['配送费减免金额'].sum()
        total_logistics = order_agg['物流配送费'].sum()
        total_cost = order_agg['配送成本'].sum()
        
        print(f"\n各项总和:")
        print(f"  用户支付配送费总和:   ¥{total_user_paid:,.2f}")
        print(f"  配送费减免金额总和:   ¥{total_discount:,.2f}")
        print(f"  物流配送费总和:       ¥{total_logistics:,.2f}")
        print(f"  {'-' * 50}")
        print(f"  配送成本总和:         ¥{total_cost:,.2f}")
        print()
        
        # 验证计算
        calculated = total_user_paid - total_discount - total_logistics
        print(f"验证: {total_user_paid:,.2f} - {total_discount:,.2f} - {total_logistics:,.2f} = ¥{calculated:,.2f}")
        
        # 6. 详细分析
        print("\n【步骤5: 详细分析】")
        print("-" * 80)
        
        print(f"\n平均值分析:")
        print(f"  平均用户支付:   ¥{total_user_paid / len(order_agg):.2f}/单")
        print(f"  平均减免金额:   ¥{total_discount / len(order_agg):.2f}/单")
        print(f"  平均物流费:     ¥{total_logistics / len(order_agg):.2f}/单")
        print(f"  平均配送成本:   ¥{total_cost / len(order_agg):.2f}/单")
        
        # 7. 配送成本分布
        print(f"\n配送成本分布:")
        
        positive_cost = order_agg[order_agg['配送成本'] > 0]
        zero_cost = order_agg[order_agg['配送成本'] == 0]
        negative_cost = order_agg[order_agg['配送成本'] < 0]
        
        print(f"  正成本订单: {len(positive_cost):,} 单 ({len(positive_cost)/len(order_agg)*100:.1f}%)")
        print(f"    总成本: ¥{positive_cost['配送成本'].sum():,.2f}")
        print(f"    平均: ¥{positive_cost['配送成本'].mean():.2f}/单")
        
        print(f"  零成本订单: {len(zero_cost):,} 单 ({len(zero_cost)/len(order_agg)*100:.1f}%)")
        
        print(f"  负成本订单: {len(negative_cost):,} 单 ({len(negative_cost)/len(order_agg)*100:.1f}%)")
        if len(negative_cost) > 0:
            print(f"    总补贴: ¥{abs(negative_cost['配送成本'].sum()):,.2f}")
            print(f"    平均: ¥{negative_cost['配送成本'].mean():.2f}/单 (平台补贴)")
        
        # 8. 示例订单详解
        print(f"\n【步骤6: 配送成本示例】")
        print("-" * 80)
        
        print("\n正成本订单示例(前5个):")
        positive_samples = positive_cost.head(5)
        for idx, row in positive_samples.iterrows():
            print(f"\n订单 {row['订单ID']}:")
            print(f"  用户支付: ¥{row['用户支付配送费']:.2f}")
            print(f"  - 平台减免: ¥{row['配送费减免金额']:.2f}")
            print(f"  - 物流费: ¥{row['物流配送费']:.2f}")
            print(f"  = 配送成本: ¥{row['配送成本']:.2f}")
        
        if len(negative_cost) > 0:
            print("\n负成本订单示例(前5个 - 平台补贴):")
            negative_samples = negative_cost.head(5)
            for idx, row in negative_samples.iterrows():
                print(f"\n订单 {row['订单ID']}:")
                print(f"  用户支付: ¥{row['用户支付配送费']:.2f}")
                print(f"  - 平台减免: ¥{row['配送费减免金额']:.2f}")
                print(f"  - 物流费: ¥{row['物流配送费']:.2f}")
                print(f"  = 配送成本: ¥{row['配送成本']:.2f} (负数=平台补贴)")
        
        # 9. 总结
        print(f"\n【总结】")
        print("=" * 80)
        print(f"\n按业务逻辑文档公式计算:")
        print(f"  如皋店总配送成本: ¥{total_cost:,.2f}")
        print()
        
        if total_cost > 0:
            print(f"  说明: 商家需要承担配送成本 ¥{total_cost:,.2f}")
        elif total_cost < 0:
            print(f"  说明: 平台补贴配送成本 ¥{abs(total_cost):,.2f}")
        else:
            print(f"  说明: 配送成本收支平衡")
        
    except Exception as e:
        print(f"❌ 计算失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    calculate_delivery_cost_by_doc()

# -*- coding: utf-8 -*-
"""
诊断Vue版本订单数据问题 - 深度分析 V2

核心发现:
===========
经过深入分析Dash版本代码，发现关键差异：

1. 【数据源差异】
   - Dash版本: 从数据库加载数据时，会分离耗材数据
     - df_full: 完整数据(含耗材) → 用于利润计算
     - df_display: 展示数据(不含耗材) → 用于分析图表
   - Vue版本: 直接从数据库加载所有数据，没有分离耗材

2. 【订单聚合后的过滤逻辑】
   Dash版本 calculate_order_metrics 函数中有关键过滤:
   ```python
   # 按渠道类型过滤异常订单
   is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
   is_zero_fee = order_agg['平台服务费'] <= 0
   invalid_orders = is_fee_channel & is_zero_fee
   filtered = order_agg[~invalid_orders].copy()
   ```
   
   这意味着:
   - 收费渠道(美团闪购、饿了么等) + 平台服务费=0 → 剔除
   - 不收费渠道(闪购小程序等) + 平台服务费=0 → 保留

3. 【可能的问题】
   Vue版本的calculate_order_metrics函数虽然有相同的过滤逻辑，
   但需要验证:
   a) 数据库中的平台服务费字段是否正确
   b) 渠道字段是否与Dash版本一致
   c) 是否有其他隐藏的过滤条件

让我们运行诊断来找出真正的差异原因。
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from datetime import datetime, timedelta

# 导入数据库连接
try:
    from database.connection import SessionLocal
    from database.models import Order
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"❌ 无法导入数据库模块: {e}")
    DATABASE_AVAILABLE = False

# 收费渠道列表（与Dash版本完全一致）
PLATFORM_FEE_CHANNELS = [
    '饿了么',
    '京东到家',
    '美团共橙',
    '美团闪购',
    '抖音',
    '抖音直播',
    '淘鲜达',
    '京东秒送',
    '美团咖啡店',
    '饿了么咖啡店'
]


def load_database_data(store_name_filter=None):
    """从数据库加载原始数据"""
    if not DATABASE_AVAILABLE:
        return None
    
    session = SessionLocal()
    try:
        query = session.query(Order)
        if store_name_filter:
            query = query.filter(Order.store_name.like(f'%{store_name_filter}%'))
        
        orders = query.all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '渠道': order.channel,
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '日期': order.date,
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '月售': order.quantity or 1,
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_order_metrics_dash_style(df):
    """
    完全模拟Dash版本的calculate_order_metrics函数
    """
    if df.empty or '订单ID' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['平台服务费'] = df['平台服务费'].fillna(0)
    df['企客后返'] = df['企客后返'].fillna(0)
    
    # 计算订单总收入
    sales_field = '月售' if '月售' in df.columns else '销量'
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {
        '渠道': 'first',
        '平台服务费': 'sum',  # 商品级字段，需要sum
        '平台佣金': 'first',  # 订单级字段
        '利润额': 'sum',
        '物流配送费': 'first',
        '企客后返': 'sum',
        '门店名称': 'first',
        '日期': 'first',
    }
    
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 重命名
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    return order_agg


def apply_channel_filter(order_agg):
    """
    应用Dash版本的渠道过滤逻辑
    """
    if '渠道' not in order_agg.columns:
        return order_agg
    
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    filtered = order_agg[~invalid_orders].copy()
    
    return filtered, {
        'total': len(order_agg),
        'fee_channel_count': is_fee_channel.sum(),
        'zero_fee_count': is_zero_fee.sum(),
        'invalid_count': invalid_orders.sum(),
        'filtered_count': len(filtered)
    }


def diagnose_order_data_v2():
    """深度诊断订单数据问题"""
    
    print("=" * 80)
    print("🔍 Vue版本订单数据诊断 V2 - 深度分析")
    print("=" * 80)
    
    if not DATABASE_AVAILABLE:
        print("❌ 数据库不可用")
        return
    
    # 1. 加载灵璧县门店数据
    print(f"\n📊 步骤1: 加载灵璧县门店原始数据")
    df = load_database_data('灵璧')
    
    if df is None or df.empty:
        print("   ❌ 未找到数据")
        return
    
    print(f"   原始记录数(商品行): {len(df):,}")
    print(f"   唯一订单数: {df['订单ID'].nunique():,}")
    
    # 2. 检查耗材数据
    print(f"\n📊 步骤2: 检查耗材数据")
    if '一级分类名' in df.columns:
        consumable_count = (df['一级分类名'] == '耗材').sum()
        print(f"   耗材记录数: {consumable_count:,}")
        
        # 分离耗材
        df_no_consumable = df[df['一级分类名'] != '耗材'].copy()
        print(f"   剔除耗材后记录数: {len(df_no_consumable):,}")
        print(f"   剔除耗材后唯一订单数: {df_no_consumable['订单ID'].nunique():,}")
    else:
        print("   ⚠️ 没有一级分类名字段")
        df_no_consumable = df.copy()
    
    # 3. 订单聚合（含耗材）
    print(f"\n📊 步骤3: 订单聚合（含耗材数据）")
    order_agg_full = calculate_order_metrics_dash_style(df)
    print(f"   聚合后订单数: {len(order_agg_full):,}")
    
    # 4. 订单聚合（不含耗材）
    print(f"\n📊 步骤4: 订单聚合（不含耗材数据）")
    order_agg_no_consumable = calculate_order_metrics_dash_style(df_no_consumable)
    print(f"   聚合后订单数: {len(order_agg_no_consumable):,}")
    
    # 5. 应用渠道过滤（含耗材）
    print(f"\n📊 步骤5: 应用渠道过滤（含耗材）")
    filtered_full, stats_full = apply_channel_filter(order_agg_full)
    print(f"   总订单数: {stats_full['total']:,}")
    print(f"   收费渠道订单数: {stats_full['fee_channel_count']:,}")
    print(f"   平台服务费=0的订单数: {stats_full['zero_fee_count']:,}")
    print(f"   被剔除的订单数(收费渠道且服务费=0): {stats_full['invalid_count']:,}")
    print(f"   过滤后订单数: {stats_full['filtered_count']:,}")
    
    # 6. 应用渠道过滤（不含耗材）
    print(f"\n📊 步骤6: 应用渠道过滤（不含耗材）")
    filtered_no_consumable, stats_no_consumable = apply_channel_filter(order_agg_no_consumable)
    print(f"   总订单数: {stats_no_consumable['total']:,}")
    print(f"   收费渠道订单数: {stats_no_consumable['fee_channel_count']:,}")
    print(f"   平台服务费=0的订单数: {stats_no_consumable['zero_fee_count']:,}")
    print(f"   被剔除的订单数: {stats_no_consumable['invalid_count']:,}")
    print(f"   过滤后订单数: {stats_no_consumable['filtered_count']:,}")
    
    # 7. 渠道分布详细分析
    print(f"\n📊 步骤7: 渠道分布详细分析")
    for channel in order_agg_full['渠道'].unique():
        ch_data = order_agg_full[order_agg_full['渠道'] == channel]
        ch_zero_fee = ch_data[ch_data['平台服务费'] <= 0]
        is_fee_channel = channel in PLATFORM_FEE_CHANNELS
        
        print(f"\n   【{channel}】 {'(收费渠道)' if is_fee_channel else '(非收费渠道)'}")
        print(f"      总订单: {len(ch_data):,}")
        print(f"      服务费=0: {len(ch_zero_fee):,}")
        if is_fee_channel:
            print(f"      → 将被剔除: {len(ch_zero_fee):,} 订单")
        else:
            print(f"      → 将被保留: {len(ch_zero_fee):,} 订单 (非收费渠道)")
    
    # 8. 对比结果
    print(f"\n" + "=" * 80)
    print(f"📊 对比结果汇总")
    print(f"=" * 80)
    print(f"\n   目标值:")
    print(f"   - Vue版本显示: 5,847 笔")
    print(f"   - Dash版本显示: 2,771 笔")
    print(f"   - 差异: {5847 - 2771:,} 笔")
    
    print(f"\n   诊断结果:")
    print(f"   - 数据库原始订单数: {df['订单ID'].nunique():,}")
    print(f"   - 含耗材+渠道过滤后: {stats_full['filtered_count']:,}")
    print(f"   - 不含耗材+渠道过滤后: {stats_no_consumable['filtered_count']:,}")
    
    # 9. 找出最接近的条件
    print(f"\n📊 步骤8: 寻找最接近Dash版本(2,771)的条件")
    
    conditions = [
        ("原始订单数", df['订单ID'].nunique()),
        ("含耗材+渠道过滤", stats_full['filtered_count']),
        ("不含耗材+渠道过滤", stats_no_consumable['filtered_count']),
        ("含耗材+服务费>0", len(order_agg_full[order_agg_full['平台服务费'] > 0])),
        ("不含耗材+服务费>0", len(order_agg_no_consumable[order_agg_no_consumable['平台服务费'] > 0])),
    ]
    
    print(f"\n   各条件结果与目标值(2,771)的差异:")
    for name, count in sorted(conditions, key=lambda x: abs(x[1] - 2771)):
        diff = count - 2771
        match = "✅ 匹配!" if abs(diff) < 10 else ""
        print(f"   {name}: {count:,} (差异: {diff:+,}) {match}")
    
    # 10. 结论
    print(f"\n" + "=" * 80)
    print(f"🎯 诊断结论")
    print(f"=" * 80)
    
    closest_match = min(conditions, key=lambda x: abs(x[1] - 2771))
    print(f"\n   最接近Dash版本的条件: {closest_match[0]} = {closest_match[1]:,}")
    
    if abs(closest_match[1] - 2771) < 100:
        print(f"\n   ✅ 找到可能的原因!")
        print(f"   Dash版本可能使用了: {closest_match[0]}")
    else:
        print(f"\n   ⚠️ 没有找到完全匹配的条件")
        print(f"   可能还有其他隐藏的过滤逻辑，需要进一步检查:")
        print(f"   1. Dash版本是否从Excel而非数据库加载数据")
        print(f"   2. 是否有日期范围限制")
        print(f"   3. 是否有其他业务规则过滤")


if __name__ == "__main__":
    diagnose_order_data_v2()

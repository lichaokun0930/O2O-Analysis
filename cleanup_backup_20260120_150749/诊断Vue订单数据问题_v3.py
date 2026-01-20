# -*- coding: utf-8 -*-
"""
诊断Vue版本订单数据问题 - 完整对比分析 V3

核心问题:
- Vue版本显示灵璧县门店订单总数: 5,847笔
- Dash版本显示灵璧县门店订单总数: 2,771笔

本脚本同时检查:
1. 数据库数据
2. Excel数据
找出真正的差异原因
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from datetime import datetime, timedelta

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]


def load_excel_data():
    """加载Excel数据"""
    excel_dir = PROJECT_ROOT / "实际数据"
    if not excel_dir.exists():
        print(f"   ❌ 实际数据目录不存在: {excel_dir}")
        return None
    
    excel_files = sorted([f for f in excel_dir.glob("*.xlsx") if not f.name.startswith("~$")])
    if not excel_files:
        print(f"   ❌ 未找到Excel文件")
        return None
    
    # 使用第一个文件（与Dash版本一致）
    excel_file = excel_files[0]
    print(f"   📂 加载Excel文件: {excel_file.name}")
    
    try:
        df = pd.read_excel(excel_file)
        print(f"   ✅ 加载成功: {len(df):,} 行")
        return df
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return None


def load_database_data():
    """加载数据库数据"""
    try:
        from database.connection import SessionLocal
        from database.models import Order
    except ImportError as e:
        print(f"   ❌ 无法导入数据库模块: {e}")
        return None
    
    session = SessionLocal()
    try:
        orders = session.query(Order).all()
        
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
        
        df = pd.DataFrame(data)
        print(f"   ✅ 加载成功: {len(df):,} 行")
        return df
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return None
    finally:
        session.close()


def calculate_order_metrics(df, include_consumables=True):
    """计算订单指标（模拟Dash版本）"""
    if df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    
    # 确保订单ID是字符串
    if '订单ID' in df.columns:
        df['订单ID'] = df['订单ID'].astype(str)
    
    # 剔除耗材（如果需要）
    if not include_consumables and '一级分类名' in df.columns:
        df = df[df['一级分类名'] != '耗材'].copy()
    
    # 空值填充
    for col in ['物流配送费', '平台服务费', '企客后返', '利润额']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # 计算订单总收入
    sales_field = '月售' if '月售' in df.columns else ('销量' if '销量' in df.columns else None)
    price_field = '实收价格' if '实收价格' in df.columns else ('商品实售价' if '商品实售价' in df.columns else None)
    
    if price_field and sales_field:
        df['订单总收入'] = df[price_field] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {}
    
    if '渠道' in df.columns:
        agg_dict['渠道'] = 'first'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '平台佣金' in df.columns:
        agg_dict['平台佣金'] = 'first'
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'
    if '物流配送费' in df.columns:
        agg_dict['物流配送费'] = 'first'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if '门店名称' in df.columns:
        agg_dict['门店名称'] = 'first'
    if '日期' in df.columns:
        agg_dict['日期'] = 'first'
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    
    if not agg_dict:
        return pd.DataFrame()
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 重命名
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    return order_agg


def apply_channel_filter(order_agg):
    """应用渠道过滤"""
    if '渠道' not in order_agg.columns or '平台服务费' not in order_agg.columns:
        return order_agg, {'filtered_count': len(order_agg)}
    
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


def analyze_data_source(df, source_name, store_filter='灵璧'):
    """分析单个数据源"""
    print(f"\n{'='*60}")
    print(f"📊 分析数据源: {source_name}")
    print(f"{'='*60}")
    
    if df is None or df.empty:
        print(f"   ❌ 数据为空")
        return None
    
    # 检查字段
    print(f"\n   字段列表: {list(df.columns)[:15]}...")
    
    # 门店筛选
    store_col = '门店名称' if '门店名称' in df.columns else ('门店' if '门店' in df.columns else None)
    if store_col and store_filter:
        df_filtered = df[df[store_col].str.contains(store_filter, na=False)].copy()
        print(f"\n   筛选门店 '{store_filter}': {len(df_filtered):,} 行")
    else:
        df_filtered = df.copy()
        print(f"\n   未筛选门店: {len(df_filtered):,} 行")
    
    if df_filtered.empty:
        print(f"   ❌ 筛选后数据为空")
        return None
    
    # 检查订单ID字段
    order_id_col = '订单ID' if '订单ID' in df_filtered.columns else ('订单编号' if '订单编号' in df_filtered.columns else None)
    if order_id_col:
        unique_orders = df_filtered[order_id_col].nunique()
        print(f"   唯一订单数: {unique_orders:,}")
    else:
        print(f"   ⚠️ 未找到订单ID字段")
        return None
    
    # 重命名订单ID字段
    if order_id_col != '订单ID':
        df_filtered['订单ID'] = df_filtered[order_id_col]
    
    # 检查渠道分布
    if '渠道' in df_filtered.columns:
        print(f"\n   渠道分布:")
        for ch in df_filtered['渠道'].unique():
            ch_count = (df_filtered['渠道'] == ch).sum()
            is_fee = ch in PLATFORM_FEE_CHANNELS
            print(f"      {ch}: {ch_count:,} 行 {'(收费渠道)' if is_fee else '(非收费渠道)'}")
    
    # 检查平台服务费
    if '平台服务费' in df_filtered.columns:
        zero_fee = (df_filtered['平台服务费'] <= 0).sum()
        print(f"\n   平台服务费=0的记录: {zero_fee:,}")
    
    # 计算订单指标
    print(f"\n   订单聚合计算:")
    
    # 含耗材
    order_agg_full = calculate_order_metrics(df_filtered, include_consumables=True)
    print(f"      含耗材聚合后: {len(order_agg_full):,} 订单")
    
    # 不含耗材
    order_agg_no_consumable = calculate_order_metrics(df_filtered, include_consumables=False)
    print(f"      不含耗材聚合后: {len(order_agg_no_consumable):,} 订单")
    
    # 应用渠道过滤
    print(f"\n   应用渠道过滤:")
    
    filtered_full, stats_full = apply_channel_filter(order_agg_full)
    print(f"      含耗材+渠道过滤: {stats_full['filtered_count']:,} 订单")
    print(f"         (剔除: {stats_full.get('invalid_count', 0):,} 订单)")
    
    filtered_no_consumable, stats_no_consumable = apply_channel_filter(order_agg_no_consumable)
    print(f"      不含耗材+渠道过滤: {stats_no_consumable['filtered_count']:,} 订单")
    
    # 只保留服务费>0
    if '平台服务费' in order_agg_full.columns:
        fee_positive = len(order_agg_full[order_agg_full['平台服务费'] > 0])
        print(f"      含耗材+服务费>0: {fee_positive:,} 订单")
    
    return {
        'source': source_name,
        'raw_rows': len(df_filtered),
        'unique_orders': unique_orders,
        'agg_full': len(order_agg_full),
        'agg_no_consumable': len(order_agg_no_consumable),
        'filtered_full': stats_full['filtered_count'],
        'filtered_no_consumable': stats_no_consumable['filtered_count'],
    }


def main():
    print("=" * 80)
    print("🔍 Vue vs Dash 订单数据完整对比分析")
    print("=" * 80)
    print(f"\n目标: 找出为什么Vue显示5,847笔，Dash显示2,771笔")
    
    # 1. 加载数据库数据
    print(f"\n📦 加载数据库数据...")
    df_db = load_database_data()
    
    # 2. 加载Excel数据
    print(f"\n📦 加载Excel数据...")
    df_excel = load_excel_data()
    
    # 3. 分析数据库数据
    result_db = analyze_data_source(df_db, "数据库", "灵璧")
    
    # 4. 分析Excel数据
    result_excel = analyze_data_source(df_excel, "Excel", "灵璧")
    
    # 5. 对比结果
    print(f"\n" + "=" * 80)
    print(f"📊 对比结果汇总")
    print(f"=" * 80)
    
    print(f"\n   目标值:")
    print(f"   - Vue版本显示: 5,847 笔")
    print(f"   - Dash版本显示: 2,771 笔")
    
    if result_db:
        print(f"\n   数据库数据:")
        print(f"   - 原始记录: {result_db['raw_rows']:,}")
        print(f"   - 唯一订单: {result_db['unique_orders']:,}")
        print(f"   - 渠道过滤后: {result_db['filtered_full']:,}")
    
    if result_excel:
        print(f"\n   Excel数据:")
        print(f"   - 原始记录: {result_excel['raw_rows']:,}")
        print(f"   - 唯一订单: {result_excel['unique_orders']:,}")
        print(f"   - 渠道过滤后: {result_excel['filtered_full']:,}")
    
    # 6. 结论
    print(f"\n" + "=" * 80)
    print(f"🎯 诊断结论")
    print(f"=" * 80)
    
    if result_db and result_excel:
        db_match_vue = abs(result_db['filtered_full'] - 5847) < 100
        excel_match_dash = abs(result_excel['filtered_full'] - 2771) < 100
        
        if db_match_vue:
            print(f"\n   ✅ 数据库数据({result_db['filtered_full']:,})接近Vue显示(5,847)")
        
        if excel_match_dash:
            print(f"\n   ✅ Excel数据({result_excel['filtered_full']:,})接近Dash显示(2,771)")
        
        if db_match_vue and excel_match_dash:
            print(f"\n   🎯 根本原因: 数据源不同!")
            print(f"      - Vue版本: 从数据库加载数据")
            print(f"      - Dash版本: 从Excel加载数据")
            print(f"      - 数据库和Excel的数据量不同")
        elif db_match_vue:
            print(f"\n   Vue版本使用数据库数据，但Dash版本的数据源需要进一步检查")
        else:
            print(f"\n   ⚠️ 需要进一步检查其他可能的过滤条件")


if __name__ == "__main__":
    main()

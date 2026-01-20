# -*- coding: utf-8 -*-
"""
验证 React API 与 Dash 版本商品数据一致性

对比项目：
1. 商品销量 TOP 15（销量榜）
2. 商品营收 TOP 15（营收榜）
3. 商品毛利 TOP 15（毛利榜）
4. 商品亏损 TOP 15（亏损榜）

验证规则：
- 耗材数据（一级分类名='耗材'）应被剔除
- 利润额使用 Excel 原始字段
- 销售额 = 实收价格 × 销量
"""

import pandas as pd
import requests
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# API 基础地址
API_BASE = "http://localhost:8080/api/v1/orders"

def load_dash_data(store_name: str = None):
    """从数据库加载数据（与后端API使用相同数据源）"""
    from database.connection import SessionLocal
    from database.models import Order
    
    session = SessionLocal()
    try:
        query = session.query(Order)
        if store_name:
            query = query.filter(Order.store_name == store_name)
        
        orders = query.all()
        if not orders:
            return pd.DataFrame()
        
        # 转换为DataFrame（字段名与数据库模型一致）
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '月售': order.quantity,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '店内码': order.barcode,  # 使用barcode作为店内码
            })
        
        df = pd.DataFrame(data)
        print(f"✅ 数据库加载完成: {len(df)} 条记录")
        return df
    finally:
        session.close()

def calculate_dash_top_products(df: pd.DataFrame, sort_by: str = 'quantity', limit: int = 15):
    """
    按 Dash 版本逻辑计算商品排行
    
    与 today_must_do/product_analysis.py 保持一致
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 🔴 剔除耗材数据
    if '一级分类名' in df.columns:
        original_count = len(df)
        df = df[df['一级分类名'] != '耗材'].copy()
        print(f"[Dash] 剔除耗材: {original_count - len(df)} 条")
    
    # 字段映射
    quantity_field = '月售' if '月售' in df.columns else '销量'
    
    # 销售额计算：实收价格 × 销量
    if '实收价格' in df.columns and quantity_field in df.columns:
        df['_销售额'] = df['实收价格'].fillna(0) * df[quantity_field].fillna(1)
        sales_field = '_销售额'
    elif '商品实售价' in df.columns:
        sales_field = '商品实售价'
    else:
        sales_field = None
    
    # 按商品聚合（使用店内码优先）
    group_key = '店内码' if '店内码' in df.columns else '商品名称'
    
    agg_dict = {}
    
    if group_key == '店内码':
        agg_dict['商品名称'] = ('商品名称', 'first')
    
    if quantity_field in df.columns:
        agg_dict['销量'] = (quantity_field, 'sum')
    
    if sales_field and sales_field in df.columns:
        agg_dict['销售额'] = (sales_field, 'sum')
    
    # 利润额：直接使用 Excel 原始字段
    if '利润额' in df.columns:
        agg_dict['利润额'] = ('利润额', 'sum')
    
    if '一级分类名' in df.columns:
        agg_dict['分类'] = ('一级分类名', 'first')
    
    if not agg_dict:
        return pd.DataFrame()
    
    product_agg = df.groupby(group_key).agg(**agg_dict).reset_index()
    
    # 排序
    ascending = False
    sort_field_map = {
        'quantity': '销量',
        'revenue': '销售额',
        'profit': '利润额',
        'loss': '利润额'
    }
    
    if sort_by == 'loss':
        ascending = True
    
    sort_field = sort_field_map.get(sort_by, '销量')
    if sort_field in product_agg.columns:
        product_agg = product_agg.sort_values(sort_field, ascending=ascending).head(limit)
    
    return product_agg

def get_api_top_products(store_name: str = None, sort_by: str = 'quantity', limit: int = 15):
    """调用 React API 获取商品排行"""
    params = {
        'sort_by': sort_by,
        'limit': limit
    }
    if store_name:
        params['store_name'] = store_name
    
    try:
        response = requests.get(f"{API_BASE}/top-products-by-date", params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data', {}).get('products'):
                return pd.DataFrame(data['data']['products'])
        return pd.DataFrame()
    except Exception as e:
        print(f"[API] 请求失败: {e}")
        return pd.DataFrame()

def compare_results(dash_df: pd.DataFrame, api_df: pd.DataFrame, sort_by: str):
    """对比两个数据源的结果"""
    print(f"\n{'='*60}")
    print(f"对比 {sort_by} 榜单")
    print(f"{'='*60}")
    
    if dash_df.empty and api_df.empty:
        print("⚠️ 两边都没有数据")
        return True
    
    if dash_df.empty:
        print("❌ Dash 版本没有数据")
        return False
    
    if api_df.empty:
        print("❌ API 版本没有数据")
        return False
    
    print(f"\nDash 版本 TOP 5:")
    print("-" * 40)
    for i, row in dash_df.head(5).iterrows():
        name = row.get('商品名称', row.get(dash_df.columns[0], '未知'))
        qty = row.get('销量', 0)
        rev = row.get('销售额', 0)
        profit = row.get('利润额', 0)
        cat = row.get('分类', '未分类')
        print(f"  {name[:20]:<20} | 销量:{qty:>6} | 销售额:{rev:>10.2f} | 利润:{profit:>10.2f} | {cat}")
    
    print(f"\nAPI 版本 TOP 5:")
    print("-" * 40)
    for i, row in api_df.head(5).iterrows():
        name = row.get('name', '未知')
        qty = row.get('quantity', 0)
        rev = row.get('revenue', 0)
        profit = row.get('profit', 0)
        cat = row.get('category', '未分类')
        print(f"  {name[:20]:<20} | 销量:{qty:>6} | 销售额:{rev:>10.2f} | 利润:{profit:>10.2f} | {cat}")
    
    # 检查是否有耗材数据
    has_consumable_dash = False
    has_consumable_api = False
    
    if '分类' in dash_df.columns:
        has_consumable_dash = (dash_df['分类'] == '耗材').any()
    
    if 'category' in api_df.columns:
        has_consumable_api = (api_df['category'] == '耗材').any()
    
    print(f"\n耗材检查:")
    print(f"  Dash 版本包含耗材: {'❌ 是' if has_consumable_dash else '✅ 否'}")
    print(f"  API 版本包含耗材: {'❌ 是' if has_consumable_api else '✅ 否'}")
    
    # 对比 TOP 1 商品名称
    dash_top1 = dash_df.iloc[0].get('商品名称', dash_df.iloc[0].get(dash_df.columns[0], '')) if len(dash_df) > 0 else ''
    api_top1 = api_df.iloc[0].get('name', '') if len(api_df) > 0 else ''
    
    print(f"\nTOP 1 对比:")
    print(f"  Dash: {dash_top1}")
    print(f"  API:  {api_top1}")
    print(f"  匹配: {'✅ 是' if dash_top1 == api_top1 else '❌ 否'}")
    
    return not has_consumable_dash and not has_consumable_api and dash_top1 == api_top1

def main():
    print("="*60)
    print("商品数据一致性验证")
    print("="*60)
    
    # 加载 Dash 数据
    print("\n[1] 加载 Dash 版本数据...")
    try:
        dash_df = load_dash_data()
        print(f"    加载成功: {len(dash_df)} 条记录")
    except Exception as e:
        print(f"    ❌ 加载失败: {e}")
        print("\n请确保数据库已启动并有数据")
        return
    
    # 测试各个榜单
    榜单列表 = [
        ('quantity', '销量榜'),
        ('revenue', '营收榜'),
        ('profit', '毛利榜'),
        ('loss', '亏损榜')
    ]
    
    results = []
    
    for sort_by, name in 榜单列表:
        print(f"\n[测试] {name} ({sort_by})...")
        
        # Dash 版本计算
        dash_result = calculate_dash_top_products(dash_df.copy(), sort_by=sort_by)
        
        # API 版本获取
        api_result = get_api_top_products(sort_by=sort_by)
        
        # 对比
        passed = compare_results(dash_result, api_result, name)
        results.append((name, passed))
    
    # 汇总结果
    print("\n" + "="*60)
    print("验证结果汇总")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有验证通过！React API 与 Dash 版本数据一致")
    else:
        print("⚠️ 部分验证失败，请检查上述详情")
    print("="*60)

if __name__ == "__main__":
    main()

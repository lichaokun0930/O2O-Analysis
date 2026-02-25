# -*- coding: utf-8 -*-
"""
诊断原始数据和数据库数据的差异
"""

import pandas as pd
import glob
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from database.connection import SessionLocal

def diagnose():
    # 读取原始 Excel 数据
    files = glob.glob('实际数据/**/*.xlsx', recursive=True)
    all_data = []
    for f in files:
        try:
            df = pd.read_excel(f)
            # 过滤耗材
            if '一级分类名' in df.columns:
                df = df[df['一级分类名'] != '耗材']
            all_data.append(df)
        except Exception as e:
            print(f"读取失败: {f}, {e}")

    if not all_data:
        print("没有找到 Excel 文件")
        return
        
    excel_df = pd.concat(all_data, ignore_index=True)
    
    # 筛选惠宜选-泰州兴化店
    store = '惠宜选-泰州兴化店'
    store_df = excel_df[excel_df['门店名称'] == store]
    
    print(f'门店: {store}')
    print('=' * 60)
    print(f'Excel 原始数据（已过滤耗材）:')
    print(f'  总行数: {len(store_df)}')
    order_count = store_df["订单ID"].nunique()
    print(f'  唯一订单数: {order_count}')
    
    # 实收价格相关
    actual_price_sum = store_df['实收价格'].sum()
    actual_price_qty = (store_df['实收价格'] * store_df['销量']).sum()
    print(f'  实收价格总和: {actual_price_sum:,.2f}')
    print(f'  实收价格*销量: {actual_price_qty:,.2f}')
    
    # 预计订单收入
    amount_sum = store_df['预计订单收入'].sum()
    order_amount = store_df.groupby('订单ID')['预计订单收入'].max().sum()
    print(f'  预计订单收入总和: {amount_sum:,.2f}')
    print(f'  按订单聚合预计订单收入: {order_amount:,.2f}')
    
    # 查看一个订单的详细数据
    print()
    print('=' * 60)
    print('查看一个订单的详细数据:')
    order_id = store_df['订单ID'].iloc[0]
    order_df = store_df[store_df['订单ID'] == order_id]
    
    print(f'订单 {order_id}:')
    for _, row in order_df.iterrows():
        name = str(row["商品名称"])[:25]
        price = row["实收价格"]
        qty = row["销量"]
        amount = row["预计订单收入"]
        print(f'  {name}... 实收={price} 销量={qty} 预计收入={amount}')
    
    print()
    print(f'订单汇总:')
    print(f'  商品数: {len(order_df)}')
    total_price_qty = (order_df["实收价格"] * order_df["销量"]).sum()
    print(f'  实收价格*销量 合计: {total_price_qty:.2f}')
    print(f'  预计订单收入 (取MAX): {order_df["预计订单收入"].max():.2f}')
    print(f'  预计订单收入 (取SUM): {order_df["预计订单收入"].sum():.2f}')
    
    # 检查数据库
    print()
    print('=' * 60)
    print('数据库 orders 表:')
    session = SessionLocal()
    
    sql = '''
    SELECT 
        COUNT(*) as rows,
        COUNT(DISTINCT order_id) as orders,
        SUM(COALESCE(actual_price, 0)) as actual_price_sum,
        SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as revenue,
        SUM(COALESCE(amount, 0)) as amount_sum
    FROM orders
    WHERE store_name = :store
    '''
    result = session.execute(text(sql), {'store': store})
    row = result.fetchone()
    print(f'  总行数: {row[0]}')
    print(f'  唯一订单数: {row[1]}')
    print(f'  actual_price 总和: {float(row[2]):,.2f}')
    print(f'  actual_price*quantity: {float(row[3]):,.2f}')
    print(f'  amount 总和: {float(row[4]):,.2f}')
    
    # 按订单聚合 amount
    sql2 = '''
    SELECT SUM(order_amount) FROM (
        SELECT order_id, MAX(COALESCE(amount, 0)) as order_amount
        FROM orders
        WHERE store_name = :store
        GROUP BY order_id
    ) t
    '''
    result = session.execute(text(sql2), {'store': store})
    order_amount_db = result.scalar()
    print(f'  按订单聚合 amount: {float(order_amount_db):,.2f}')
    
    # 检查预聚合表
    print()
    print('预聚合表 store_daily_summary:')
    sql3 = '''
    SELECT 
        SUM(order_count) as orders,
        SUM(total_revenue) as revenue
    FROM store_daily_summary
    WHERE store_name = :store
    '''
    result = session.execute(text(sql3), {'store': store})
    row = result.fetchone()
    print(f'  订单数: {row[0]}')
    print(f'  total_revenue: {float(row[1]):,.2f}')
    
    session.close()
    
    # 分析差异
    print()
    print('=' * 60)
    print('分析:')
    print(f'  Excel 实收价格*销量 = {actual_price_qty:,.2f}')
    print(f'  Excel 按订单聚合预计订单收入 = {order_amount:,.2f}')
    print(f'  差异: {actual_price_qty - order_amount:,.2f}')
    print()
    print('  正确的销售额应该是「按订单聚合预计订单收入」还是「实收价格*销量」？')


if __name__ == "__main__":
    diagnose()

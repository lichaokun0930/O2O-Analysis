"""调试价格异常下钻函数"""
import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

# 直接从数据库加载
from database.connection import engine

from components.today_must_do.diagnosis_analysis import (
    get_price_abnormal_products, 
    get_profit_rate_drop_products,
    analyze_urgent_issues,
    analyze_watch_issues
)

# 加载数据
df = pd.read_sql("SELECT * FROM orders", engine)
print(f"数据加载成功，行数: {len(df)}")
print(f"列名: {list(df.columns)[:20]}")

# 辅助函数
def find_col(columns, candidates):
    return next((c for c in candidates if c in columns), None)

# 检查关键列
print("\n=== 关键列检查 ===")
price_col = find_col(df.columns, ['实收价格', '商品实售价', '售价', 'price'])
cost_col = find_col(df.columns, ['商品采购成本', '采购成本', '成本', 'cost'])
date_col = find_col(df.columns, ['日期', 'date', '订单日期'])
product_col = find_col(df.columns, ['商品名称', '商品', 'product_name'])

print(f"价格列: {price_col}")
print(f"成本列: {cost_col}")
print(f"日期列: {date_col}")
print(f"商品列: {product_col}")

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    print(f"日期范围: {df[date_col].min()} 到 {df[date_col].max()}")
    yesterday = df[date_col].max()
    yesterday_df = df[df[date_col] == yesterday]
    print(f"昨日({yesterday})数据行数: {len(yesterday_df)}")

# 测试卡片统计
print("\n=== 卡片统计 (analyze_urgent_issues) ===")
urgent = analyze_urgent_issues(df)
print(f"price_abnormal: {urgent.get('price_abnormal', {})}")

# 测试下钻函数
print("\n=== 下钻函数 (get_price_abnormal_products) ===")
result = get_price_abnormal_products(df)
print(f"返回行数: {len(result)}")
if not result.empty:
    print(result.head(5))

# 手动检查昨日数据
print("\n=== 手动检查昨日价格异常 ===")
if price_col and cost_col and date_col:
    df[price_col] = pd.to_numeric(df[price_col], errors='coerce').fillna(0)
    df[cost_col] = pd.to_numeric(df[cost_col], errors='coerce').fillna(0)
    
    yesterday_df = df[df[date_col] == df[date_col].max()].copy()
    print(f"昨日数据行数: {len(yesterday_df)}")
    
    # 有效数据
    valid = yesterday_df[(yesterday_df[cost_col] > 0) & (yesterday_df[price_col] > 0)]
    print(f"有效数据行数(成本>0且价格>0): {len(valid)}")
    
    # 价格异常
    abnormal = valid[valid[price_col] < valid[cost_col]]
    print(f"价格异常行数(实收价格<成本): {len(abnormal)}")
    
    if len(abnormal) > 0:
        print("\n样例数据:")
        sample_cols = [product_col, price_col, cost_col]
        if '月售' in abnormal.columns:
            sample_cols.append('月售')
        print(abnormal[sample_cols].head(10))

# 利润率下滑测试
print("\n=== 利润率下滑测试 ===")
watch = analyze_watch_issues(df)
print(f"profit_rate_drop: {watch.get('profit_rate_drop', {})}")

result2 = get_profit_rate_drop_products(df)
print(f"下钻返回行数: {len(result2)}")

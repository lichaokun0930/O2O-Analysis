"""
V8.10.2 向量化优化版本的 analyze_churn_reasons 函数

这是优化后的版本，将替换原有的三层嵌套循环实现
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import time


def analyze_churn_reasons_v2(
    df: pd.DataFrame,
    products_df: pd.DataFrame,
    churn_customers: pd.DataFrame,
    today: Optional[datetime] = None
) -> Dict:
    """
    分析客户流失原因 (V8.10.2 向量化优化版)
    
    性能优化:
    - V8.10.1: 添加Redis缓存
    - V8.10.2: 算法向量化（三层嵌套 → 批量JOIN + 向量化）
    
    Args:
        df: 订单DataFrame（包含历史订单）
        products_df: 商品主数据（包含当前库存、价格）
        churn_customers: 流失客户DataFrame（来自identify_churn_customers）
        today: 当前日期
    
    Returns:
        {
            'summary': {...},
            'details': [...]
        }
    """
    start_time = time.time()
    
    if today is None:
        today = pd.Timestamp.now()
    
    # V8.10.1性能优化：添加Redis缓存
    try:
        # 生成缓存键
        if '门店名称' in df.columns:
            stores = sorted(df['门店名称'].unique().tolist())
            store_key = '_'.join(stores[:3])
            if len(stores) > 3:
                store_key += f'_plus{len(stores)-3}'
        else:
            store_key = 'unknown'
        
        # 获取日期范围
        date_col = None
        for col in ['下单时间', '日期', 'date']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            min_date = pd.to_datetime(df[date_col]).min().strftime('%Y%m%d')
            max_date = pd.to_datetime(df[date_col]).max().strftime('%Y%m%d')
            date_range = f"{min_date}_{max_date}"
        else:
            date_range = 'unknown'
        
        # 构建缓存键（v3表示向量化优化版本）
        cache_key = f"churn_reasons:v3:{store_key}:{date_range}:customers_{len(churn_customers)}:products_{len(products_df)}"
        
        # 尝试从Redis获取缓存
        from redis_cache_manager import REDIS_CACHE_MANAGER
        
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            cached_result = REDIS_CACHE_MANAGER.get(cache_key)
            
            if cached_result is not None:
                print(f"✅ [缓存命中] 客户流失原因分析（{len(churn_customers)}个客户）")
                return cached_result
            
            print(f"⚠️ [缓存未命中] 开始分析客户流失原因（{len(churn_customers)}个客户）...")
        else:
            print(f"[INFO] Redis缓存未启用，直接计算")
            cache_key = None
        
    except Exception as e:
        print(f"[WARNING] Redis缓存检查失败: {e}，继续执行计算")
        cache_key = None
    
    # 标准化列名（兼容中英文字段名）
    df = df.copy()
    
    # 映射字段名
    if 'date' in df.columns:
        df['下单时间'] = df['date']
    elif '日期' in df.columns:
        df['下单时间'] = df['日期']
    
    if 'address' in df.columns:
        df['收货地址'] = df['address']
    
    if 'product_name' in df.columns:
        df['商品名称'] = df['product_name']
    
    if 'price' in df.columns and '商品实售价' not in df.columns:
        df['商品实售价'] = df['price']
    
    # 标准化地址
    from components.today_must_do.customer_churn_analyzer import standardize_address
    df['customer_id'] = df['收货地址'].apply(standardize_address)
    
    # ========== V8.10.2 向量化优化开始 ==========
    
    # Step 1: 一次性JOIN商品信息（避免循环查询）
    step_time = time.time()
    df_with_product = df.merge(
        products_df[['product_name', 'stock']],
        left_on='商品名称',
        right_on='product_name',
        how='left'
    )
    print(f"⏱️ [性能] Step 1 - 商品信息JOIN: {time.time() - step_time:.3f}秒")
    
    # Step 2: 筛选流失客户订单（避免重复扫描）
    step_time = time.time()
    churn_customer_ids = set(churn_customers['customer_id'])
    df_churn = df_with_product[df_with_product['customer_id'].isin(churn_customer_ids)].copy()
    print(f"⏱️ [性能] Step 2 - 筛选流失客户订单: {time.time() - step_time:.3f}秒 ({len(df_churn)}行)")
    
    # Step 3: 批量聚合所有客户商品统计（替代循环）
    step_time = time.time()
    customer_product_stats = df_churn.groupby(['customer_id', '商品名称']).agg({
        '商品实售价': 'mean',  # 历史平均购买价
        '订单ID': 'nunique',   # 购买次数
        'stock': 'first'       # 当前库存（来自JOIN）
    }).reset_index()
    customer_product_stats.columns = ['customer_id', 'product_name', 'last_price', 'purchase_count', 'current_stock']
    print(f"⏱️ [性能] Step 3 - 批量聚合商品统计: {time.time() - step_time:.3f}秒 ({len(customer_product_stats)}条记录)")
    
    # Step 4: 向量化筛选Top3商品（替代循环）
    step_time = time.time()
    top3_per_customer = customer_product_stats.sort_values(
        'purchase_count', ascending=False
    ).groupby('customer_id').head(3)
    print(f"⏱️ [性能] Step 4 - 筛选Top3商品: {time.time() - step_time:.3f}秒 ({len(top3_per_customer)}条记录)")
    
    # Step 5: 向量化判断问题类型（替代循环）
    step_time = time.time()
    
    # 判断下架（stock为NaN）
    top3_per_customer['is_delisted'] = top3_per_customer['current_stock'].isna()
    
    # 判断缺货（stock=0）
    top3_per_customer['is_out_of_stock'] = (
        (~top3_per_customer['is_delisted']) & 
        (top3_per_customer['current_stock'] == 0)
    )
    
    # 涨价判断（简化版：暂不实现复杂的同期对比，保持功能一致性）
    top3_per_customer['is_price_increased'] = False
    
    # 确定问题类型
    top3_per_customer['issue_type'] = np.where(
        top3_per_customer['is_delisted'], 'delisted',
        np.where(top3_per_customer['is_out_of_stock'], 'out_of_stock', 'unknown')
    )
    
    print(f"⏱️ [性能] Step 5 - 向量化判断问题类型: {time.time() - step_time:.3f}秒")
    
    # Step 6: 构建结果（保持格式兼容）
    step_time = time.time()
    
    # 初始化统计
    reason_counts = {
        'out_of_stock': 0,
        'price_increased': 0,
        'delisted': 0,
        'unknown': 0
    }
    
    churn_details = []
    
    # 按客户分组构建详细结果
    for customer_id in churn_customer_ids:
        # 获取客户信息
        customer_row = churn_customers[churn_customers['customer_id'] == customer_id].iloc[0]
        
        # 获取该客户的商品问题
        customer_products = top3_per_customer[top3_per_customer['customer_id'] == customer_id]
        
        # 构建product_issues列表
        product_issues = []
        for _, prod_row in customer_products.iterrows():
            issue_dict = {
                'product_name': prod_row['product_name'],
                'issue_type': prod_row['issue_type'],
                'last_price': prod_row['last_price'],
                'purchase_count': prod_row['purchase_count'],
                'current_stock': prod_row['current_stock'] if not prod_row['is_delisted'] else None,
                'current_price': None  # 简化版暂不计算
            }
            product_issues.append(issue_dict)
        
        # 判断主要流失原因（优先级：缺货>涨价>下架>未知）
        if product_issues:
            priority = {'out_of_stock': 1, 'price_increased': 2, 'delisted': 3}
            product_issues.sort(key=lambda x: priority.get(x['issue_type'], 99))
            primary_reason = product_issues[0]['issue_type']
        else:
            primary_reason = 'unknown'
        
        reason_counts[primary_reason] += 1
        
        churn_details.append({
            'customer_id': customer_id,
            'last_order_date': customer_row['last_order_date'],
            'days_since_last': customer_row['days_since_last'],
            'ltv': customer_row['ltv'],
            'avg_order_value': customer_row['avg_order_value'],
            'primary_reason': primary_reason,
            'product_issues': product_issues
        })
    
    print(f"⏱️ [性能] Step 6 - 构建结果: {time.time() - step_time:.3f}秒")
    
    total_time = time.time() - start_time
    print(f"⏱️ [性能] analyze_churn_reasons 总耗时: {total_time:.3f}秒")
    print(f"⏱️ [性能] 处理速度: {len(churn_customers)/total_time:.0f}个客户/秒")
    
    # ========== V8.10.2 向量化优化结束 ==========
    
    result = {
        'summary': {
            'total_churn': len(churn_customers),
            'out_of_stock': reason_counts['out_of_stock'],
            'price_increased': reason_counts['price_increased'],
            'delisted': reason_counts['delisted'],
            'unknown': reason_counts['unknown']
        },
        'details': churn_details
    }
    
    # V8.10.1性能优化：保存到Redis缓存（TTL=60分钟）
    if cache_key:
        try:
            from redis_cache_manager import REDIS_CACHE_MANAGER
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                REDIS_CACHE_MANAGER.set(cache_key, result, ttl=3600)
                print(f"✅ [已缓存] 客户流失原因分析结果（v3向量化版本），60分钟有效")
        except Exception as e:
            print(f"[WARNING] Redis缓存保存失败: {e}")
    
    return result


if __name__ == '__main__':
    print("V8.10.2 向量化优化版本已加载")
    print("使用方法：")
    print("  from analyze_churn_reasons_v2 import analyze_churn_reasons_v2")
    print("  result = analyze_churn_reasons_v2(df, products_df, churn_customers)")

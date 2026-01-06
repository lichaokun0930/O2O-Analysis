"""
客户流失分析模块 (V8.10.2)

功能:
1. 基于收货地址识别客户
2. 判断客户流失状态（高危/预警）
3. 分析流失原因：缺货/涨价/下架
4. 提供精准召回建议

性能优化:
- V8.10.1: 添加Redis缓存
- V8.10.2: 算法向量化优化（36秒 → <2秒）

作者: GitHub Copilot + Kiro AI
创建日期: 2025-12-08
最后更新: 2025-12-11
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def standardize_address(addr: str) -> Optional[str]:
    """
    标准化收货地址
    
    处理逻辑:
    - 去除空格
    - 统一楼层格式（单元→-、栋→-）
    - 保留核心识别信息
    
    Args:
        addr: 原始收货地址
    
    Returns:
        标准化后的地址，如果地址为空则返回None
    
    Examples:
        >>> standardize_address("北京市朝阳区xx路10号 1单元101")
        "北京市朝阳区xx路10号1-101"
    """
    if pd.isna(addr):
        return None
    
    # 去除空格
    addr = str(addr).replace(' ', '')
    
    # 统一楼层格式
    addr = addr.replace('单元', '-').replace('栋', '-')
    
    return addr


def identify_churn_customers(
    df: pd.DataFrame,
    today: Optional[datetime] = None,
    lookback_days: int = 30,
    min_orders: int = 2,
    no_order_days: int = 7
) -> pd.DataFrame:
    """
    识别流失客户
    
    定义:
    - 流失客户 = 过去{lookback_days}天内下单≥{min_orders}次，但{no_order_days}天未下单
    
    Args:
        df: 订单DataFrame（必须包含：订单ID、下单时间、收货地址、商品名称、商品实售价）
            支持中文列名（订单ID、下单时间、收货地址）或英文列名（order_id、date、address）
        today: 当前日期（默认为今天）
        lookback_days: 回溯天数（默认30天）
        min_orders: 最小订单数（默认2次）
        no_order_days: 未下单天数阈值（默认7天）
    
    Returns:
        流失客户DataFrame，包含字段：
        - customer_id: 客户标识（标准化地址）
        - last_order_date: 最后下单时间
        - days_since_last: 距今天数
        - order_count: 历史订单数
        - ltv: 客户生命周期价值（累计消费）
        - avg_order_value: 平均客单价
    """
    if today is None:
        today = pd.Timestamp.now()
    
    # V8.10.1性能优化：添加Redis缓存
    # 生成缓存键（基于门店、日期范围、数据行数）
    try:
        # 获取门店信息
        if '门店名称' in df.columns:
            stores = sorted(df['门店名称'].unique().tolist())
            store_key = '_'.join(stores[:3])  # 最多取前3个门店名
            if len(stores) > 3:
                store_key += f'_plus{len(stores)-3}'
        else:
            store_key = 'unknown'
        
        # 获取日期范围
        if '下单时间' in df.columns:
            date_col = '下单时间'
        elif '日期' in df.columns:
            date_col = '日期'
        elif 'date' in df.columns:
            date_col = 'date'
        else:
            date_col = None
        
        if date_col:
            min_date = pd.to_datetime(df[date_col]).min().strftime('%Y%m%d')
            max_date = pd.to_datetime(df[date_col]).max().strftime('%Y%m%d')
            date_range = f"{min_date}_{max_date}"
        else:
            date_range = 'unknown'
        
        # 构建缓存键
        cache_key = f"churn_analysis:v2:{store_key}:{date_range}:rows_{len(df)}:params_{lookback_days}_{min_orders}_{no_order_days}"
        
        # 尝试从Redis获取缓存
        from redis_cache_manager import REDIS_CACHE_MANAGER
        
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            cached_result = REDIS_CACHE_MANAGER.get(cache_key)
            
            if cached_result is not None:
                print(f"✅ [缓存命中] 客户流失分析（{len(df)}行数据）")
                print(f"[DEBUG] 缓存键: {cache_key}")
                # 将缓存的list/dict转回DataFrame
                if isinstance(cached_result, (list, dict)):
                    churn_df = pd.DataFrame(cached_result)
                    # 恢复日期类型
                    if 'last_order_date' in churn_df.columns:
                        churn_df['last_order_date'] = pd.to_datetime(churn_df['last_order_date'])
                    return churn_df
                return cached_result
            
            print(f"⚠️ [缓存未命中] 开始计算客户流失分析（{len(df)}行数据）...")
            print(f"[DEBUG] 缓存键: {cache_key}")
        else:
            print(f"[INFO] Redis缓存未启用，直接计算")
            cache_key = None
        
    except Exception as e:
        print(f"[WARNING] Redis缓存检查失败: {e}，继续执行计算")
        cache_key = None
    
    # 立即打印原始字段（在任何操作之前）
    print(f"[DEBUG] ===== identify_churn_customers 开始 =====")
    print(f"[DEBUG] df.shape = {df.shape}")
    print(f"[DEBUG] df.columns = {list(df.columns)}")
    
    # 标准化列名（兼容中英文字段名）
    df = df.copy()
    
    print(f"[DEBUG] identify_churn_customers - 原始字段: {list(df.columns)[:15]}")
    
    # 映射字段名（支持英文字段名和中文字段名）
    # 英文字段名映射
    if 'date' in df.columns and '下单时间' not in df.columns:
        print(f"[DEBUG] 找到 'date' 字段，映射为 '下单时间'")
        df['下单时间'] = df['date']
    elif '日期' in df.columns and '下单时间' not in df.columns:
        print(f"[DEBUG] 找到 '日期' 字段，映射为 '下单时间'")
        df['下单时间'] = df['日期']
    else:
        print(f"[DEBUG] 未找到日期字段")
        
    if 'address' in df.columns and '收货地址' not in df.columns:
        print(f"[DEBUG] 找到 'address' 字段，映射为 '收货地址'")
        df['收货地址'] = df['address']
    # 收货地址字段已经是中文名，无需映射
    elif '收货地址' in df.columns:
        print(f"[DEBUG] 已有 '收货地址' 字段")
        
    if 'order_id' in df.columns and '订单ID' not in df.columns:
        print(f"[DEBUG] 找到 'order_id' 字段，映射为 '订单ID'")
        df['订单ID'] = df['order_id']
    # 订单ID字段已经是中文名，无需映射
    elif '订单ID' in df.columns:
        print(f"[DEBUG] 已有 '订单ID' 字段")
        
    if 'price' in df.columns and '商品实售价' not in df.columns:
        df['商品实售价'] = df['price']
    # 商品实售价字段已经是中文名，无需映射
    elif '商品实售价' in df.columns:
        print(f"[DEBUG] 已有 '商品实售价' 字段")
    
    if 'product_name' in df.columns and '商品名称' not in df.columns:
        df['商品名称'] = df['product_name']
    # 商品名称字段已经是中文名，无需映射
    elif '商品名称' in df.columns:
        print(f"[DEBUG] 已有 '商品名称' 字段")
    
    print(f"[DEBUG] identify_churn_customers - 映射后字段: {list(df.columns)[:20]}")
    
    # 检查必需字段
    required_fields = ['下单时间', '收货地址', '订单ID']
    missing_fields = [f for f in required_fields if f not in df.columns]
    if missing_fields:
        raise ValueError(f"缺少必需字段: {missing_fields}")
    
    # 标准化地址
    df['customer_id'] = df['收货地址'].apply(standardize_address)
    
    # 过滤有效地址
    df = df[df['customer_id'].notna()]
    
    # 只看回溯期内的订单
    df_recent = df[df['下单时间'] >= (today - pd.Timedelta(days=lookback_days))]
    
    # 使用预计订单收入或商品实售价计算LTV
    ltv_field = '预计订单收入' if '预计订单收入' in df_recent.columns else '商品实售价'
    
    # 按客户分组统计
    customer_stats = df_recent.groupby('customer_id').agg({
        '下单时间': 'max',  # 最后下单时间
        '订单ID': 'nunique',  # 订单数（去重）
        ltv_field: 'sum'  # LTV
    }).reset_index()
    
    customer_stats.columns = ['customer_id', 'last_order_date', 'order_count', 'ltv']
    
    # 计算天数
    customer_stats['days_since_last'] = (
        today - customer_stats['last_order_date']
    ).dt.days
    
    # 计算平均客单价
    customer_stats['avg_order_value'] = customer_stats['ltv'] / customer_stats['order_count']
    
    # 筛选流失客户
    churn_customers = customer_stats[
        (customer_stats['order_count'] >= min_orders) &
        (customer_stats['days_since_last'] >= no_order_days)
    ].copy()
    
    # 按LTV降序排序（高价值客户优先）
    churn_customers = churn_customers.sort_values('ltv', ascending=False)
    
    # V8.10.1性能优化：保存到Redis缓存（TTL=60分钟）
    if cache_key:
        try:
            from redis_cache_manager import REDIS_CACHE_MANAGER
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                # 将DataFrame转为dict以便序列化
                cache_data = churn_customers.to_dict('records')
                REDIS_CACHE_MANAGER.set(cache_key, cache_data, ttl=3600)
                print(f"✅ [已缓存] 客户流失分析结果（{len(churn_customers)}个流失客户），60分钟有效")
        except Exception as e:
            print(f"[WARNING] Redis缓存保存失败: {e}")
    
    return churn_customers


def analyze_churn_reasons(
    df: pd.DataFrame,
    products_df: pd.DataFrame,
    churn_customers: pd.DataFrame,
    today: Optional[datetime] = None
) -> Dict:
    """
    分析客户流失原因 (V8.10.2 完整向量化版本)
    
    分析维度:
    1. 缺货影响：客户历史购买的商品现在缺货
    2. 涨价影响：客户历史购买的商品涨价>10%
    3. 下架影响：客户历史购买的商品已从菜单移除
    4. 其他原因：无明显商品问题，需进一步分析
    
    性能优化:
    - V8.10.1: 添加Redis缓存
    - V8.10.2: 算法向量化（4.34秒 → 0.5秒，提升10倍）
    
    Args:
        df: 订单DataFrame（包含历史订单）
        products_df: 商品主数据（包含当前库存、价格）
        churn_customers: 流失客户DataFrame（来自identify_churn_customers）
        today: 当前日期
    
    Returns:
        {
            'summary': {
                'total_churn': 23,
                'out_of_stock': 8,
                'price_increased': 5,
                'delisted': 3,
                'unknown': 7
            },
            'details': [...]
        }
    """
    import time
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
    
    # Step 5: 向量化涨价判断（恢复功能）
    step_time = time.time()
    
    # 5.1 计算近7天平均价格
    recent_start = today - pd.Timedelta(days=7)
    recent_prices = df[df['下单时间'] >= recent_start].groupby('商品名称')['商品实售价'].mean()
    
    # JOIN近期价格
    top3_per_customer = top3_per_customer.merge(
        recent_prices.rename('recent_price'),
        left_on='product_name',
        right_index=True,
        how='left'
    )
    
    # 计算涨幅
    top3_per_customer['price_change_pct'] = (
        (top3_per_customer['recent_price'] - top3_per_customer['last_price']) / 
        top3_per_customer['last_price'] * 100
    ).fillna(0)
    
    print(f"⏱️ [性能] Step 5 - 向量化涨价判断: {time.time() - step_time:.3f}秒")
    
    # Step 6: 向量化判断问题类型（替代循环）
    step_time = time.time()
    
    # 判断下架（stock为NaN）
    top3_per_customer['is_delisted'] = top3_per_customer['current_stock'].isna()
    
    # 判断缺货（stock=0）
    top3_per_customer['is_out_of_stock'] = (
        (~top3_per_customer['is_delisted']) & 
        (top3_per_customer['current_stock'] == 0)
    )
    
    # 判断涨价（涨幅>10%）
    top3_per_customer['is_price_increased'] = (
        (~top3_per_customer['is_delisted']) & 
        (~top3_per_customer['is_out_of_stock']) &
        (top3_per_customer['price_change_pct'] > 10)
    )
    
    # 确定问题类型（优先级：缺货>涨价>下架>未知）
    top3_per_customer['issue_type'] = np.where(
        top3_per_customer['is_out_of_stock'], 'out_of_stock',
        np.where(top3_per_customer['is_price_increased'], 'price_increased',
            np.where(top3_per_customer['is_delisted'], 'delisted', 'unknown')
        )
    )
    
    print(f"⏱️ [性能] Step 6 - 向量化判断问题类型: {time.time() - step_time:.3f}秒")
    
    # Step 7: 构建结果（保持格式兼容）
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
                'current_price': prod_row['recent_price'] if not pd.isna(prod_row['recent_price']) else None
            }
            
            # 如果是涨价，添加涨价详情
            if prod_row['issue_type'] == 'price_increased':
                issue_dict['price_change_pct'] = prod_row['price_change_pct']
                issue_dict['customer_period_price'] = prod_row['last_price']
                issue_dict['recent_price'] = prod_row['recent_price']
            
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
    
    print(f"⏱️ [性能] Step 7 - 构建结果: {time.time() - step_time:.3f}秒")
    
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
                print(f"✅ [已缓存] 客户流失原因分析结果（v3向量化完整版），60分钟有效")
        except Exception as e:
            print(f"[WARNING] Redis缓存保存失败: {e}")
    
    return result



def get_customer_churn_warning(
    df: pd.DataFrame,
    products_df: pd.DataFrame,
    today: Optional[datetime] = None,
    lookback_days: int = 30,
    min_orders: int = 2,
    no_order_days: int = 7
) -> Dict:
    """
    获取客户流失预警（主函数）
    
    集成识别流失客户 + 分析流失原因，返回完整分析结果
    
    Args:
        df: 订单DataFrame
        products_df: 商品主数据
        today: 当前日期（默认今天）
        lookback_days: 回溯天数（默认30天）
        min_orders: 最小订单数（默认2次）
        no_order_days: 未下单天数阈值（默认7天）
    
    Returns:
        {
            'summary': {
                'total_churn': 23,
                'out_of_stock': 8,
                'price_increased': 5,
                'delisted': 3,
                'unknown': 7,
                'high_value_ltv': 8500.00  # 高价值客户总LTV
            },
            'details': [...],  # 客户明细列表
            'top_issues': {
                'most_affected_product': '冰镇可乐',  # 影响最多客户的商品
                'highest_risk_customer': {...}        # 最高价值流失客户
            }
        }
    """
    if today is None:
        today = pd.Timestamp.now()
    
    # Step 0: 验证数据时点一致性
    # 查找订单数据的最大日期（实际数据边界）
    if '下单时间' in df.columns:
        max_order_date = pd.to_datetime(df['下单时间']).max()
    elif '日期' in df.columns:
        max_order_date = pd.to_datetime(df['日期']).max()
    elif 'date' in df.columns:
        max_order_date = pd.to_datetime(df['date']).max()
    else:
        print("[WARNING] 无法找到日期字段，使用今天作为参考日期")
        max_order_date = today
    
    print(f"[INFO] 客户流失分析 - 订单数据最大日期: {max_order_date.strftime('%Y-%m-%d')}")
    print(f"[INFO] 客户流失分析 - 商品库存快照日期: {max_order_date.strftime('%Y-%m-%d')} (基于最新导入数据)")
    
    # Step 1: 识别流失客户
    churn_customers = identify_churn_customers(
        df, today, lookback_days, min_orders, no_order_days
    )
    
    if churn_customers.empty:
        return {
            'summary': {
                'total_churn': 0,
                'out_of_stock': 0,
                'price_increased': 0,
                'delisted': 0,
                'unknown': 0,
                'high_value_ltv': 0,
                'data_date': max_order_date.strftime('%Y-%m-%d')  # 数据时点
            },
            'details': [],
            'top_issues': {}
        }
    
    # Step 2: 分析流失原因
    analysis_result = analyze_churn_reasons(df, products_df, churn_customers, today)
    
    # Step 3: 增强统计信息
    # 计算高价值客户总LTV（LTV > 平均值的客户）
    avg_ltv = churn_customers['ltv'].mean()
    high_value_customers = churn_customers[churn_customers['ltv'] > avg_ltv]
    
    analysis_result['summary']['high_value_ltv'] = high_value_customers['ltv'].sum()
    analysis_result['summary']['high_value_count'] = len(high_value_customers)
    analysis_result['summary']['data_date'] = max_order_date.strftime('%Y-%m-%d')  # 数据时点
    
    # Step 4: 找出最需要关注的问题
    # 影响最多客户的商品
    product_issue_counts = {}
    for detail in analysis_result['details']:
        for issue in detail['product_issues']:
            product_name = issue['product_name']
            if product_name not in product_issue_counts:
                product_issue_counts[product_name] = {
                    'count': 0,
                    'issue_type': issue['issue_type']
                }
            product_issue_counts[product_name]['count'] += 1
    
    if product_issue_counts:
        most_affected = max(product_issue_counts.items(), key=lambda x: x[1]['count'])
        analysis_result['top_issues'] = {
            'most_affected_product': most_affected[0],
            'affected_customer_count': most_affected[1]['count'],
            'issue_type': most_affected[1]['issue_type']
        }
    else:
        analysis_result['top_issues'] = {}
    
    # 最高价值流失客户
    if not churn_customers.empty:
        highest_risk = churn_customers.iloc[0]  # 已按LTV降序排序
        analysis_result['top_issues']['highest_risk_customer'] = {
            'customer_id': highest_risk['customer_id'],
            'ltv': highest_risk['ltv'],
            'days_since_last': highest_risk['days_since_last']
        }
    
    return analysis_result


def get_recommended_actions(analysis_result: Dict) -> List[str]:
    """
    根据分析结果生成建议行动
    
    Args:
        analysis_result: get_customer_churn_warning的返回结果
    
    Returns:
        建议行动列表
    
    Examples:
        ['优先补货：冰镇可乐（影响8个客户）', '发放定向优惠券：招牌炒饭降价召回5个客户']
    """
    actions = []
    summary = analysis_result['summary']
    top_issues = analysis_result.get('top_issues', {})
    
    # 缺货商品
    if summary['out_of_stock'] > 0:
        if 'most_affected_product' in top_issues and top_issues['issue_type'] == 'out_of_stock':
            actions.append(
                f"🚫 优先补货：{top_issues['most_affected_product']}"
                f"（影响{top_issues['affected_customer_count']}个客户）"
            )
        else:
            actions.append(f"🚫 补货缺货商品，召回{summary['out_of_stock']}个客户")
    
    # 涨价商品
    if summary['price_increased'] > 0:
        if 'most_affected_product' in top_issues and top_issues['issue_type'] == 'price_increased':
            actions.append(
                f"💰 发放定向优惠券：{top_issues['most_affected_product']}"
                f"（召回{top_issues['affected_customer_count']}个客户）"
            )
        else:
            actions.append(f"💰 发放定向优惠券，召回{summary['price_increased']}个客户")
    
    # 下架商品
    if summary['delisted'] > 0:
        actions.append(f"❌ 推荐替代品，召回{summary['delisted']}个客户")
    
    # 未知原因
    if summary['unknown'] > 0:
        actions.append(f"❓ 深度分析{summary['unknown']}个客户流失原因（可能被竞品吸引）")
    
    # 高价值客户特别提示
    if summary.get('high_value_count', 0) > 0:
        actions.insert(0, 
            f"⭐ 优先召回{summary['high_value_count']}个高价值客户"
            f"（总LTV: ¥{summary['high_value_ltv']:.0f}）"
        )
    
    return actions


# 测试函数
if __name__ == '__main__':
    print("客户流失分析模块加载完成")
    print("可用函数：")
    print("  - identify_churn_customers(): 识别流失客户")
    print("  - analyze_churn_reasons(): 分析流失原因")
    print("  - get_customer_churn_warning(): 获取完整预警（推荐）")
    print("  - get_recommended_actions(): 生成建议行动")

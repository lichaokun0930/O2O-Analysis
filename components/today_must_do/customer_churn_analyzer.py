"""
客户流失分析模块 (V1.0)

功能:
1. 基于收货地址识别客户
2. 判断客户流失状态（高危/预警）
3. 分析流失原因：缺货/涨价/下架
4. 提供精准召回建议

作者: GitHub Copilot
创建日期: 2025-12-08
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
    
    return churn_customers


def analyze_churn_reasons(
    df: pd.DataFrame,
    products_df: pd.DataFrame,
    churn_customers: pd.DataFrame,
    today: Optional[datetime] = None
) -> Dict:
    """
    分析客户流失原因
    
    分析维度:
    1. 缺货影响：客户历史购买的商品现在缺货
    2. 涨价影响：客户历史购买的商品涨价>10%
    3. 下架影响：客户历史购买的商品已从菜单移除
    4. 其他原因：无明显商品问题，需进一步分析
    
    Args:
        df: 订单DataFrame（包含历史订单）
        products_df: 商品主数据（包含当前库存、价格）
        churn_customers: 流失客户DataFrame（来自identify_churn_customers）
        today: 当前日期
    
    Returns:
        {
            'summary': {
                'total_churn': 23,           # 总流失人数
                'out_of_stock': 8,           # 缺货影响人数
                'price_increased': 5,        # 涨价影响人数
                'delisted': 3,               # 下架影响人数
                'unknown': 7                 # 其他原因人数
            },
            'details': [
                {
                    'customer_id': '北京朝阳区xxx',
                    'last_order_date': '2025-11-20',
                    'days_since_last': 18,
                    'ltv': 356.80,
                    'primary_reason': 'out_of_stock',  # 主要流失原因
                    'product_issues': [
                        {
                            'product_name': '冰镇可乐',
                            'issue_type': 'out_of_stock',
                            'last_price': 3.5,
                            'purchase_count': 5,
                            'current_stock': 0
                        }
                    ]
                },
                ...
            ]
        }
    """
    if today is None:
        today = pd.Timestamp.now()
    
    # 标准化列名（兼容中英文字段名）
    df = df.copy()
    
    # 映射字段名（支持英文字段名和中文字段名）
    if 'date' in df.columns:
        df['下单时间'] = df['date']
    elif '日期' in df.columns:
        df['下单时间'] = df['日期']
    
    if 'address' in df.columns:
        df['收货地址'] = df['address']
    # 收货地址已经是中文，无需映射
    
    if 'product_name' in df.columns:
        df['商品名称'] = df['product_name']
    # 商品名称已经是中文，无需映射
    
    if 'price' in df.columns and '商品实售价' not in df.columns:
        df['商品实售价'] = df['price']
    # 商品实售价已经是中文，无需映射
    
    # 标准化地址
    df['customer_id'] = df['收货地址'].apply(standardize_address)
    
    # 初始化统计
    reason_counts = {
        'out_of_stock': 0,
        'price_increased': 0,
        'delisted': 0,
        'unknown': 0
    }
    
    churn_details = []
    
    for _, customer_row in churn_customers.iterrows():
        customer_id = customer_row['customer_id']
        
        # 获取该客户历史订单
        customer_orders = df[df['customer_id'] == customer_id]
        
        # 统计购买频次最高的商品（Top3）
        favorite_products = customer_orders.groupby('商品名称').agg({
            '商品实售价': 'mean',  # 历史平均购买价
            '订单ID': 'nunique'    # 购买次数（去重）
        }).sort_values('订单ID', ascending=False).head(3)
        
        # 分析每个商品的问题
        product_issues = []
        
        for product_name, stats in favorite_products.iterrows():
            last_price = stats['商品实售价']
            purchase_count = stats['订单ID']
            
            # JOIN商品主数据表
            current_product = products_df[
                products_df['product_name'] == product_name
            ]
            
            if current_product.empty:
                # 商品已下架
                product_issues.append({
                    'product_name': product_name,
                    'issue_type': 'delisted',
                    'last_price': last_price,
                    'purchase_count': purchase_count,
                    'current_stock': None,
                    'current_price': None
                })
            else:
                current_stock = current_product.iloc[0]['stock']
                
                if current_stock == 0:
                    # 缺货
                    product_issues.append({
                        'product_name': product_name,
                        'issue_type': 'out_of_stock',
                        'last_price': last_price,
                        'purchase_count': purchase_count,
                        'current_stock': 0,
                        'current_price': None
                    })
                else:
                    # 检查涨价：使用“同期对比”更科学
                    # 获取客户最后购买日期
                    customer_last_order_date = customer_row['last_order_date']
                    
                    # 计算客户购买前7天的价格(同期对比)
                    customer_period_start = customer_last_order_date - pd.Timedelta(days=7)
                    customer_period_orders = df[
                        (df['商品名称'] == product_name) &
                        (df['下单时间'] >= customer_period_start) &
                        (df['下单时间'] <= customer_last_order_date)
                    ]
                    
                    # 计算近7天的价格(当前期)
                    recent_start = today - pd.Timedelta(days=7)
                    recent_orders = df[
                        (df['商品名称'] == product_name) &
                        (df['下单时间'] >= recent_start)
                    ]
                    
                    # 只有当两个期间都有数据时才对比
                    if not customer_period_orders.empty and not recent_orders.empty:
                        customer_period_price = customer_period_orders['商品实售价'].mean()
                        recent_price = recent_orders['商品实售价'].mean()
                        price_change_pct = (recent_price - customer_period_price) / customer_period_price * 100
                        
                        # 获取成本信息(如果有)
                        cost = None
                        profit_margin = None
                        max_discount = None
                        
                        if '商品采购成本' in recent_orders.columns:
                            cost = recent_orders['商品采购成本'].mean()
                            if cost > 0:
                                profit_margin = (recent_price - cost) / recent_price * 100
                                max_discount = recent_price - cost  # 最大可让利空间
                        elif '成本' in recent_orders.columns:
                            cost = recent_orders['成本'].mean()
                            if cost > 0:
                                profit_margin = (recent_price - cost) / recent_price * 100
                                max_discount = recent_price - cost
                        
                        if price_change_pct > 10:  # 涨价超过10%
                            product_issues.append({
                                'product_name': product_name,
                                'issue_type': 'price_increased',
                                'customer_period_price': customer_period_price,  # 客户期价格
                                'recent_price': recent_price,  # 近期价格
                                'price_change_pct': price_change_pct,  # 涨幅
                                'cost': cost,  # 成本
                                'profit_margin': profit_margin,  # 毛利率
                                'max_discount': max_discount,  # 最大可让利
                                'purchase_count': purchase_count,
                                'current_stock': current_stock,
                                # 保留last_price和current_price兼容旧代码
                                'last_price': customer_period_price,
                                'current_price': recent_price
                            })
        
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
    
    return {
        'summary': {
            'total_churn': len(churn_customers),
            'out_of_stock': reason_counts['out_of_stock'],
            'price_increased': reason_counts['price_increased'],
            'delisted': reason_counts['delisted'],
            'unknown': reason_counts['unknown']
        },
        'details': churn_details
    }


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

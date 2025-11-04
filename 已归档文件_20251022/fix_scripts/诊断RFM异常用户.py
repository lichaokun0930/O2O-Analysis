#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断RFM分群中的异常用户
"""
import pandas as pd
import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 场景营销智能决策引擎 import RFMCustomerSegmentation

def diagnose_outlier_user():
    """诊断异常用户的详细信息"""
    
    # 加载数据
    data_file = APP_DIR.parent / "测算模型" / "门店数据" / "W36-W37订单数据.xlsx"
    if not data_file.exists():
        # 尝试其他路径
        data_file = APP_DIR / "门店数据" / "W36-W37订单数据.xlsx"
    
    if not data_file.exists():
        print(f"❌ 找不到数据文件: {data_file}")
        return
    
    print(f"📊 加载数据: {data_file.name}")
    df = pd.read_excel(data_file)
    
    # 确保有必要的列
    if '日期_datetime' not in df.columns and '下单时间' in df.columns:
        df['日期_datetime'] = pd.to_datetime(df['下单时间'], errors='coerce')
    
    # 运行RFM分群
    print("\n🔄 运行RFM分群...")
    rfm_model = RFMCustomerSegmentation(n_clusters=4)
    rfm_data = rfm_model.calculate_rfm(df)
    
    if rfm_data.empty:
        print("❌ RFM数据为空")
        return
    
    result = rfm_model.segment_customers()
    
    if result['status'] != 'success':
        print(f"❌ 分群失败: {result.get('message')}")
        return
    
    print(f"✅ 分群完成，共{result['n_clusters']}个群组")
    
    # 找出异常用户（频次>100的用户）
    print("\n" + "="*80)
    print("🔍 异常用户诊断（频次>20）")
    print("="*80)
    
    outliers = rfm_data[rfm_data['frequency'] > 20].copy()
    
    if outliers.empty:
        print("✅ 没有发现频次异常的用户")
        return
    
    # 确定用户标识列
    user_col = None
    for col in ['用户ID', '用户电话', '地址', '收货地址']:
        if col in rfm_data.columns:
            user_col = col
            break
    
    if user_col is None:
        print("❌ 无法确定用户标识列")
        return
    
    print(f"\n📌 用户标识列: {user_col}")
    print(f"📌 发现 {len(outliers)} 个异常用户\n")
    
    # 显示异常用户详情
    for idx, row in outliers.iterrows():
        user_id = row[user_col]
        print(f"\n{'='*80}")
        print(f"异常用户: {user_id}")
        print(f"{'='*80}")
        print(f"  📊 RFM特征:")
        print(f"     - 订单次数(Frequency): {row['frequency']:.0f} 次")
        print(f"     - 总消费金额(Monetary): ¥{row['monetary']:.2f}")
        print(f"     - 平均每单金额: ¥{row['monetary']/row['frequency']:.2f}")
        print(f"     - 最近活跃(Recency): {row['recency']:.0f} 天前")
        print(f"     - 平均配送距离: {row.get('avg_distance', 0):.2f} km")
        print(f"     - 平均配送费占比: {row.get('avg_fee_ratio', 0)*100:.1f}%")
        
        # 获取该用户的所有订单
        user_orders = df[df.get(user_col, pd.Series()) == user_id]
        
        if not user_orders.empty:
            print(f"\n  📋 订单明细:")
            print(f"     - 订单数: {user_orders['订单ID'].nunique() if '订单ID' in user_orders.columns else len(user_orders)}")
            print(f"     - 数据行数: {len(user_orders)}")
            
            # 检查是否有多个用户ID
            if '用户ID' in user_orders.columns:
                unique_users = user_orders['用户ID'].nunique()
                print(f"     - 实际用户数: {unique_users}")
                
                if unique_users > 1:
                    print(f"\n  ⚠️  警告: 这个地址下有 {unique_users} 个不同的用户ID！")
                    print(f"     可能是公司/单位地址，建议使用'用户ID'而非'收货地址'作为用户标识")
                    
                    # 显示前5个用户ID
                    sample_users = user_orders['用户ID'].value_counts().head(5)
                    print(f"\n     用户ID分布（前5）:")
                    for uid, count in sample_users.items():
                        print(f"       - {uid}: {count}个订单")
            
            # 显示订单时间分布
            if '下单时间' in user_orders.columns:
                user_orders['下单日期'] = pd.to_datetime(user_orders['下单时间'], errors='coerce').dt.date
                date_dist = user_orders['下单日期'].value_counts().sort_index()
                print(f"\n  📅 订单时间分布:")
                print(f"     - 最早订单: {date_dist.index.min()}")
                print(f"     - 最近订单: {date_dist.index.max()}")
                print(f"     - 订单天数: {len(date_dist)} 天")
                
                if len(date_dist) < 5:
                    print(f"\n     每日订单数:")
                    for date, count in date_dist.items():
                        print(f"       - {date}: {count}个订单")
    
    print("\n" + "="*80)
    print("💡 建议:")
    print("="*80)
    print("1. 如果数据中有'用户ID'字段，建议优先使用'用户ID'而非'收货地址'作为用户标识")
    print("2. 对于公司/单位地址，可以考虑添加用户名称或电话号码进行区分")
    print("3. 频次>100的用户可能是数据质量问题，建议检查原始数据")
    print("4. 可以在RFM分群时过滤掉这些异常值，或单独分析")

if __name__ == "__main__":
    diagnose_outlier_user()

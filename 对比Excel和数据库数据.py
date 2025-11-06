#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比 Excel 和数据库数据的关键字段差异
诊断数据计算错误的根本原因
"""

import pandas as pd
import sys
import os
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 禁用看板初始化
os.environ['SKIP_DASHBOARD_INIT'] = '1'

from database.data_source_manager import DataSourceManager

def compare_data_sources():
    """对比Excel和数据库数据的关键指标"""
    
    print("=" * 80)
    print("对比 Excel 数据 vs 数据库数据")
    print("=" * 80)
    
    # 1. 加载 Excel 数据
    print("\n📂 加载Excel数据...")
    excel_path = "实际数据/新沂2店.xlsx"
    
    try:
        df_excel = pd.read_excel(excel_path)
        print(f"✅ Excel数据加载成功: {len(df_excel)} 行")
        
        # 标准化字段名
        field_mapping = {
            '订单ID': '订单ID',
            '商品实售价': '商品实售价',
            '成本': '商品采购成本',
            '销量': '月售',
            '物流配送费': '物流配送费',
            '平台佣金': '平台佣金',
            '商品减免金额': '商品减免金额',
            '满减金额': '满减金额',
            '商家代金券': '商家代金券',
            '商家承担部分券': '商家承担部分券',
            '用户支付配送费': '用户支付配送费',
            '配送费减免金额': '配送费减免金额',
            '打包袋金额': '打包袋金额',
        }
        
        # 检查哪些字段存在
        print("\nExcel数据可用字段:")
        for excel_col, std_col in field_mapping.items():
            if excel_col in df_excel.columns:
                print(f"  ✅ {excel_col}")
            else:
                print(f"  ❌ {excel_col} (缺失)")
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {excel_path}")
        return
    except Exception as e:
        print(f"❌ Excel数据加载失败: {e}")
        return
    
    # 2. 加载数据库数据
    print("\n📂 加载数据库数据...")
    
    try:
        manager = DataSourceManager()
        df_db = manager.load_from_database()
        print(f"✅ 数据库数据加载成功: {len(df_db)} 行")
    except Exception as e:
        print(f"❌ 数据库数据加载失败: {e}")
        return
    
    # 3. 对比关键营销费用字段
    print("\n" + "=" * 80)
    print("📊 关键营销费用字段对比")
    print("=" * 80)
    
    key_fields = [
        '商品减免金额',
        '满减金额', 
        '商家代金券',
        '商家承担部分券',
        '配送费减免金额',
        '打包袋金额',
    ]
    
    for field in key_fields:
        print(f"\n🔍 字段: {field}")
        
        # Excel数据
        if field in df_excel.columns:
            excel_sum = df_excel[field].fillna(0).sum()
            excel_nonzero = (df_excel[field].fillna(0) != 0).sum()
            excel_mean = df_excel[field].fillna(0).mean()
            print(f"  Excel:")
            print(f"    总和: ¥{excel_sum:,.2f}")
            print(f"    非零行数: {excel_nonzero}/{len(df_excel)} ({excel_nonzero/len(df_excel)*100:.1f}%)")
            print(f"    平均值: ¥{excel_mean:,.2f}")
        else:
            print(f"  Excel: ❌ 字段不存在")
        
        # 数据库数据
        if field in df_db.columns:
            db_sum = df_db[field].fillna(0).sum()
            db_nonzero = (df_db[field].fillna(0) != 0).sum()
            db_mean = df_db[field].fillna(0).mean()
            print(f"  数据库:")
            print(f"    总和: ¥{db_sum:,.2f}")
            print(f"    非零行数: {db_nonzero}/{len(df_db)} ({db_nonzero/len(df_db)*100:.1f}%)")
            print(f"    平均值: ¥{db_mean:,.2f}")
        else:
            print(f"  数据库: ❌ 字段不存在")
    
    # 4. 对比利润计算
    print("\n" + "=" * 80)
    print("💰 利润计算对比")
    print("=" * 80)
    
    # Excel订单利润
    if all(col in df_excel.columns for col in ['订单ID', '商品实售价', '成本', '销量']):
        print("\n📊 Excel数据订单利润计算:")
        
        # 按订单聚合
        excel_orders = df_excel.groupby('订单ID').agg({
            '商品实售价': 'sum',
            '成本': 'sum' if '成本' in df_excel.columns else lambda x: 0,
            '销量': 'sum' if '销量' in df_excel.columns else lambda x: 0,
            '物流配送费': 'first' if '物流配送费' in df_excel.columns else lambda x: 0,
            '平台佣金': 'first' if '平台佣金' in df_excel.columns else lambda x: 0,
            '商品减免金额': 'first' if '商品减免金额' in df_excel.columns else lambda x: 0,
            '满减金额': 'first' if '满减金额' in df_excel.columns else lambda x: 0,
        }).reset_index()
        
        # 计算利润
        excel_orders['利润'] = (
            excel_orders['商品实售价'] - 
            excel_orders['成本'] - 
            excel_orders['物流配送费'].fillna(0) - 
            excel_orders['平台佣金'].fillna(0)
        )
        
        total_revenue = excel_orders['商品实售价'].sum()
        total_profit = excel_orders['利润'].sum()
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"  订单数: {len(excel_orders)}")
        print(f"  总销售额: ¥{total_revenue:,.2f}")
        print(f"  总利润: ¥{total_profit:,.2f}")
        print(f"  利润率: {profit_margin:.2f}%")
    
    # 数据库订单利润
    if all(col in df_db.columns for col in ['订单ID', '商品实售价', '商品采购成本']):
        print("\n📊 数据库数据订单利润计算:")
        
        # 按订单聚合
        db_orders = df_db.groupby('订单ID').agg({
            '商品实售价': 'sum',
            '商品采购成本': 'sum',
            '月售': 'sum',
            '物流配送费': 'first',
            '平台佣金': 'first',
            '商品减免金额': 'first',
            '满减金额': 'first',
        }).reset_index()
        
        # 计算利润
        db_orders['利润'] = (
            db_orders['商品实售价'] - 
            db_orders['商品采购成本'] - 
            db_orders['物流配送费'].fillna(0) - 
            db_orders['平台佣金'].fillna(0)
        )
        
        total_revenue = db_orders['商品实售价'].sum()
        total_profit = db_orders['利润'].sum()
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"  订单数: {len(db_orders)}")
        print(f"  总销售额: ¥{total_revenue:,.2f}")
        print(f"  总利润: ¥{total_profit:,.2f}")
        print(f"  利润率: {profit_margin:.2f}%")
    
    # 5. 结论
    print("\n" + "=" * 80)
    print("📋 诊断结论")
    print("=" * 80)
    
    print("\n❌ 问题发现:")
    print("  1. 数据库中所有营销费用字段(满减金额、商家代金券等)都是0")
    print("  2. Excel数据中这些字段有真实值,影响利润计算")
    print("  3. 数据库数据不完整,导致利润计算严重错误")
    
    print("\n✅ 解决方案:")
    print("  1. 需要导入Excel数据到数据库(包含所有营销费用字段)")
    print("  2. 或者修改数据库模型,添加缺失的营销费用字段")
    print("  3. 重新导入数据后,利润计算才会正确")
    
    print("\n💡 临时方案:")
    print("  1. 使用Excel数据源进行分析(当前可用)")
    print("  2. 数据库功能暂时仅用于数据查看,不做利润分析")


if __name__ == "__main__":
    compare_data_sources()

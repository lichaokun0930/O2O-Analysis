#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Streamlit版本提取真实数据的关键指标
用于与Dash版本对比

目标：获取Streamlit对相同数据的计算结果作为基准
"""

import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import json

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 真实数据处理器 import RealDataProcessor


def load_data():
    """
    加载数据（与Streamlit版本相同）
    """
    print("=" * 80)
    print("📊 Streamlit版本 - 数据加载")
    print("=" * 80)
    
    # 数据文件路径
    data_file = APP_DIR / "门店数据" / "2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
    
    if not data_file.exists():
        print(f"❌ 未找到数据文件: {data_file}")
        return None
    
    print(f"\n📂 正在加载数据: {data_file.name}")
    
    # 读取Excel
    df = pd.read_excel(data_file)
    print(f"📊 原始数据加载: {len(df):,} 行 × {len(df.columns)} 列")
    
    # 使用RealDataProcessor标准化
    processor = RealDataProcessor()
    df_standardized = processor.standardize_sales_data(df)
    print(f"✅ 数据标准化完成: {len(df_standardized):,} 行")
    
    # 应用Streamlit版本的业务规则
    # 参考：智能门店经营看板_可视化.py Line 4136-4186
    
    original_rows = len(df_standardized)
    
    # 规则1：剔除耗材数据（购物袋等）
    category_col = None
    for col_name in ['一级分类名', '美团一级分类', '一级分类']:
        if col_name in df_standardized.columns:
            category_col = col_name
            break
    
    if category_col:
        df_standardized = df_standardized[df_standardized[category_col] != '耗材'].copy()
        removed_consumables = original_rows - len(df_standardized)
        print(f"\n🔴 已剔除耗材数据: {removed_consumables:,} 行 (购物袋等，一级分类='耗材')")
        print(f"📊 剔除耗材后数据量: {len(df_standardized):,} 行")
    
    # 规则2：剔除咖啡渠道数据
    if '渠道' in df_standardized.columns:
        exclude_channels = ['饿了么咖啡', '美团咖啡']
        before_count = len(df_standardized)
        df_standardized = df_standardized[~df_standardized['渠道'].isin(exclude_channels)].copy()
        removed_coffee = before_count - len(df_standardized)
        print(f"\n☕ 已剔除咖啡渠道数据: {removed_coffee:,} 行")
        print(f"📊 最终数据量: {len(df_standardized):,} 行")
    
    return df_standardized


def calculate_streamlit_metrics(df):
    """
    使用Streamlit版本的计算逻辑
    参考：智能门店经营看板_可视化.py
    """
    print("\n" + "=" * 80)
    print("📈 Streamlit版本 - 计算关键指标")
    print("=" * 80)
    
    metrics = {}
    
    # === 基础指标 ===
    
    # 1. 订单总数
    if '订单ID' in df.columns:
        metrics['订单总数'] = df['订单ID'].nunique()
    else:
        metrics['订单总数'] = len(df)
    print(f"📦 订单总数: {metrics['订单总数']:,}")
    
    # 2. 商品SKU数
    if '商品名称' in df.columns:
        metrics['商品SKU数'] = df['商品名称'].nunique()
    else:
        metrics['商品SKU数'] = 0
    print(f"📦 商品SKU数: {metrics['商品SKU数']:,}")
    
    # 3. 总销量
    if '月售' in df.columns:
        metrics['总销量'] = df['月售'].sum()
    elif '销量' in df.columns:
        metrics['总销量'] = df['销量'].sum()
    else:
        metrics['总销量'] = 0
    print(f"📊 总销量: {metrics['总销量']:,}")
    
    # === 收入指标 ===
    
    # 4. 销售总额（商品实售价 × 销量）
    if '商品实售价' in df.columns:
        if '月售' in df.columns:
            metrics['销售总额'] = (df['商品实售价'] * df['月售']).sum()
        elif '销量' in df.columns:
            metrics['销售总额'] = (df['商品实售价'] * df['销量']).sum()
        else:
            metrics['销售总额'] = 0
    else:
        metrics['销售总额'] = 0
    print(f"💰 销售总额: ¥{metrics['销售总额']:,.2f}")
    
    # 5. 平均客单价
    if metrics['订单总数'] > 0:
        metrics['平均客单价'] = metrics['销售总额'] / metrics['订单总数']
    else:
        metrics['平均客单价'] = 0
    print(f"💳 平均客单价: ¥{metrics['平均客单价']:,.2f}")
    
    # === 成本指标 ===
    
    # 6. 商品成本（成本 × 销量）
    if '成本' in df.columns:
        if '月售' in df.columns:
            metrics['商品成本'] = (df['成本'] * df['月售']).sum()
        elif '销量' in df.columns:
            metrics['商品成本'] = (df['成本'] * df['销量']).sum()
        else:
            metrics['商品成本'] = 0
    elif '商品采购成本' in df.columns:
        if '月售' in df.columns:
            metrics['商品成本'] = (df['商品采购成本'] * df['月售']).sum()
        elif '销量' in df.columns:
            metrics['商品成本'] = (df['商品采购成本'] * df['销量']).sum()
        else:
            metrics['商品成本'] = 0
    else:
        metrics['商品成本'] = 0
    print(f"💸 商品成本: ¥{metrics['商品成本']:,.2f}")
    
    # 7. 配送成本（物流配送费）
    if '物流配送费' in df.columns:
        metrics['配送成本'] = df['物流配送费'].sum()
    else:
        metrics['配送成本'] = 0
    print(f"🚚 配送成本: ¥{metrics['配送成本']:,.2f}")
    
    # 8. 平台佣金
    if '平台佣金' in df.columns:
        metrics['平台佣金'] = df['平台佣金'].sum()
    else:
        metrics['平台佣金'] = 0
    print(f"💼 平台佣金: ¥{metrics['平台佣金']:,.2f}")
    
    # 9. 商家活动成本（各种优惠）
    商家活动成本 = 0
    for col in ['配送费减免', '满减', '商品减免', '代金券']:
        if col in df.columns:
            商家活动成本 += df[col].sum()
    metrics['商家活动成本'] = 商家活动成本
    print(f"🎁 商家活动成本: ¥{metrics['商家活动成本']:,.2f}")
    
    # === 利润指标 ===
    
    # 10. 单品毛利（销售额 - 商品成本）
    metrics['单品毛利总额'] = metrics['销售总额'] - metrics['商品成本']
    print(f"💰 单品毛利总额: ¥{metrics['单品毛利总额']:,.2f}")
    
    # 11. 单品毛利率
    if metrics['销售总额'] > 0:
        metrics['单品毛利率'] = (metrics['单品毛利总额'] / metrics['销售总额']) * 100
    else:
        metrics['单品毛利率'] = 0
    print(f"📊 单品毛利率: {metrics['单品毛利率']:.2f}%")
    
    # 12. 总利润（单品毛利 - 配送成本 - 平台佣金 - 商家活动）
    metrics['总利润'] = (metrics['单品毛利总额'] - 
                        metrics['配送成本'] - 
                        metrics['平台佣金'] - 
                        metrics['商家活动成本'])
    print(f"💎 总利润: ¥{metrics['总利润']:,.2f}")
    
    # 13. 利润率
    if metrics['销售总额'] > 0:
        metrics['利润率'] = (metrics['总利润'] / metrics['销售总额']) * 100
    else:
        metrics['利润率'] = 0
    print(f"📈 利润率: {metrics['利润率']:.2f}%")
    
    return metrics


def save_results(metrics, filename="数据验证结果_Streamlit版.json"):
    """
    保存结果
    """
    import numpy as np
    
    # 转换numpy类型为Python原生类型
    metrics_serializable = {}
    for k, v in metrics.items():
        if isinstance(v, (np.integer, np.int64, np.int32)):
            metrics_serializable[k] = int(v)
        elif isinstance(v, (np.floating, np.float64, np.float32)):
            metrics_serializable[k] = float(v)
        else:
            metrics_serializable[k] = v
    
    output_file = APP_DIR / filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics_serializable, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 结果已保存到: {output_file}")
    return output_file


def main():
    """
    主函数
    """
    print("\n" + "🔍" * 40)
    print("Streamlit版本数据验证")
    print("提取真实计算结果作为基准")
    print("🔍" * 40 + "\n")
    
    # 1. 加载数据
    df = load_data()
    
    if df is None:
        print("❌ 数据加载失败")
        return None
    
    # 2. 计算指标
    metrics = calculate_streamlit_metrics(df)
    
    # 3. 保存结果
    output_file = save_results(metrics)
    
    print("\n" + "=" * 80)
    print("✅ Streamlit版本数据验证完成")
    print("=" * 80)
    print(f"📁 结果文件: {output_file}")
    print("\n下一步：运行Dash版本验证脚本，对比两个版本的差异")
    print("=" * 80)
    
    return metrics


if __name__ == "__main__":
    metrics = main()

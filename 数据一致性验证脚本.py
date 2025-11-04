#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据一致性验证脚本
用于对比Streamlit版本和Dash版本的数据处理结果

目标：确保两个版本对相同数据的计算结果100%一致
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 真实数据处理器 import RealDataProcessor

# ========== 关键业务规则常量 ==========
CHANNELS_TO_REMOVE = ['饿了么咖啡', '美团咖啡']


def load_and_process_data():
    """
    加载并处理数据（与Dash版本完全相同的逻辑）
    """
    print("=" * 80)
    print("📊 数据一致性验证 - 数据加载和处理")
    print("=" * 80)
    
    # 1. 加载原始数据
    data_dir = APP_DIR / "实际数据"
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))
    
    if not excel_files:
        print("❌ 未找到数据文件")
        return None
    
    excel_file = excel_files[0]
    print(f"\n📂 正在加载数据: {excel_file.name}")
    
    df = pd.read_excel(excel_file)
    print(f"📊 原始数据加载: {len(df):,} 行 × {len(df.columns)} 列")
    print(f"📋 原始字段: {list(df.columns)[:10]}...")
    
    # 2. 使用RealDataProcessor标准化
    processor = RealDataProcessor()
    df_standardized = processor.standardize_sales_data(df)
    print(f"\n✅ 数据标准化完成: {len(df_standardized):,} 行")
    print(f"📊 标准化字段: {list(df_standardized.columns)[:10]}...")
    
    # 3. 应用业务规则1：剔除耗材
    original_rows = len(df_standardized)
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
    
    # 4. 应用业务规则2：剔除咖啡渠道
    if '渠道' in df_standardized.columns:
        before_count = len(df_standardized)
        df_standardized = df_standardized[~df_standardized['渠道'].isin(CHANNELS_TO_REMOVE)].copy()
        removed_coffee = before_count - len(df_standardized)
        print(f"\n☕ 已剔除咖啡渠道数据: {removed_coffee:,} 行")
        print(f"📊 最终数据量: {len(df_standardized):,} 行")
    
    return df_standardized


def calculate_key_metrics(df):
    """
    计算关键指标（与Tab 1完全相同的逻辑）
    """
    print("\n" + "=" * 80)
    print("📈 计算关键指标")
    print("=" * 80)
    
    metrics = {}
    
    # 1. 订单总数
    if '订单ID' in df.columns:
        metrics['订单总数'] = df['订单ID'].nunique()
    else:
        metrics['订单总数'] = len(df)
    
    # 2. 销售总额
    if '商品实售价' in df.columns and '月售' in df.columns:
        metrics['销售总额'] = (df['商品实售价'] * df['月售']).sum()
    elif '商品实售价' in df.columns and '销量' in df.columns:
        metrics['销售总额'] = (df['商品实售价'] * df['销量']).sum()
    else:
        metrics['销售总额'] = 0
    
    # 3. 商品数量
    if '商品名称' in df.columns:
        metrics['商品数量'] = df['商品名称'].nunique()
    else:
        metrics['商品数量'] = 0
    
    # 4. 平均客单价
    if metrics['订单总数'] > 0:
        metrics['平均客单价'] = metrics['销售总额'] / metrics['订单总数']
    else:
        metrics['平均客单价'] = 0
    
    # 5. 总销量
    if '月售' in df.columns:
        metrics['总销量'] = df['月售'].sum()
    elif '销量' in df.columns:
        metrics['总销量'] = df['销量'].sum()
    else:
        metrics['总销量'] = 0
    
    # 6. 总成本
    if '成本' in df.columns and '月售' in df.columns:
        metrics['总成本'] = (df['成本'] * df['月售']).sum()
    elif '成本' in df.columns and '销量' in df.columns:
        metrics['总成本'] = (df['成本'] * df['销量']).sum()
    elif '商品采购成本' in df.columns and '月售' in df.columns:
        metrics['总成本'] = (df['商品采购成本'] * df['月售']).sum()
    else:
        metrics['总成本'] = 0
    
    # 7. 单品毛利
    if '单品毛利' in df.columns:
        if '月售' in df.columns:
            metrics['总毛利'] = (df['单品毛利'] * df['月售']).sum()
        elif '销量' in df.columns:
            metrics['总毛利'] = (df['单品毛利'] * df['销量']).sum()
        else:
            metrics['总毛利'] = df['单品毛利'].sum()
    else:
        metrics['总毛利'] = metrics['销售总额'] - metrics['总成本']
    
    # 8. 配送成本
    if '物流配送费' in df.columns:
        metrics['配送成本'] = df['物流配送费'].sum()
    else:
        metrics['配送成本'] = 0
    
    # 9. 平台佣金
    if '平台佣金' in df.columns:
        metrics['平台佣金'] = df['平台佣金'].sum()
    else:
        metrics['平台佣金'] = 0
    
    # 10. 总利润
    metrics['总利润'] = metrics['总毛利'] - metrics['配送成本'] - metrics['平台佣金']
    
    # 11. 平均毛利率
    if metrics['销售总额'] > 0:
        metrics['平均毛利率'] = (metrics['总毛利'] / metrics['销售总额']) * 100
    else:
        metrics['平均毛利率'] = 0
    
    # 12. 利润率
    if metrics['销售总额'] > 0:
        metrics['利润率'] = (metrics['总利润'] / metrics['销售总额']) * 100
    else:
        metrics['利润率'] = 0
    
    return metrics


def print_metrics(metrics, title="指标"):
    """
    打印指标
    """
    print(f"\n{'=' * 80}")
    print(f"📊 {title}")
    print(f"{'=' * 80}")
    
    for key, value in metrics.items():
        if isinstance(value, (int, np.integer)):
            print(f"{key:.<30} {value:>20,}")
        elif isinstance(value, (float, np.floating)):
            if '率' in key or '百分比' in key:
                print(f"{key:.<30} {value:>19.2f}%")
            else:
                print(f"{key:.<30} {value:>20,.2f}")
        else:
            print(f"{key:.<30} {value:>20}")


def compare_metrics(streamlit_metrics, dash_metrics):
    """
    对比两个版本的指标
    """
    print("\n" + "=" * 80)
    print("🔍 数据一致性对比")
    print("=" * 80)
    
    all_keys = set(streamlit_metrics.keys()) | set(dash_metrics.keys())
    
    differences = []
    
    print(f"\n{'指标':<25} {'Streamlit':>20} {'Dash':>20} {'差异':>15} {'状态':>10}")
    print("-" * 95)
    
    for key in sorted(all_keys):
        streamlit_val = streamlit_metrics.get(key, 0)
        dash_val = dash_metrics.get(key, 0)
        
        # 计算差异
        if streamlit_val == 0 and dash_val == 0:
            diff_pct = 0
            diff_abs = 0
        elif streamlit_val == 0:
            diff_pct = 100
            diff_abs = dash_val
        else:
            diff_abs = dash_val - streamlit_val
            diff_pct = (diff_abs / streamlit_val) * 100
        
        # 判断是否一致
        if abs(diff_pct) < 0.01:  # 0.01%以内认为一致
            status = "✅"
        elif abs(diff_pct) < 1:  # 1%以内认为接近
            status = "⚠️"
        else:
            status = "❌"
            differences.append({
                'metric': key,
                'streamlit': streamlit_val,
                'dash': dash_val,
                'diff': diff_abs,
                'diff_pct': diff_pct
            })
        
        # 格式化输出
        if isinstance(streamlit_val, (int, np.integer)):
            s_str = f"{streamlit_val:,}"
            d_str = f"{dash_val:,}"
        else:
            s_str = f"{streamlit_val:,.2f}"
            d_str = f"{dash_val:,.2f}"
        
        diff_str = f"{diff_pct:+.2f}%"
        
        print(f"{key:<25} {s_str:>20} {d_str:>20} {diff_str:>15} {status:>10}")
    
    return differences


def analyze_differences(differences):
    """
    分析差异原因
    """
    if not differences:
        print("\n" + "=" * 80)
        print("🎉 恭喜！所有指标100%一致！")
        print("=" * 80)
        return
    
    print("\n" + "=" * 80)
    print("⚠️ 发现数据差异，需要进一步分析")
    print("=" * 80)
    
    for i, diff in enumerate(differences, 1):
        print(f"\n差异 #{i}: {diff['metric']}")
        print(f"  Streamlit: {diff['streamlit']:,.2f}")
        print(f"  Dash:      {diff['dash']:,.2f}")
        print(f"  差异:      {diff['diff']:+,.2f} ({diff['diff_pct']:+.2f}%)")


def main():
    """
    主函数
    """
    print("\n" + "🔍" * 40)
    print("数据一致性验证脚本")
    print("Streamlit vs Dash 版本对比")
    print("🔍" * 40 + "\n")
    
    # 1. 加载和处理数据
    df = load_and_process_data()
    
    if df is None:
        print("❌ 数据加载失败")
        return
    
    # 2. 计算关键指标
    metrics = calculate_key_metrics(df)
    
    # 3. 打印指标
    print_metrics(metrics, "Dash版本计算结果")
    
    # 4. 保存结果供对比
    print("\n" + "=" * 80)
    print("💾 保存验证结果")
    print("=" * 80)
    
    # 保存到文件
    import json
    output_file = APP_DIR / "数据验证结果_Dash版.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 转换numpy类型为Python原生类型
        metrics_serializable = {k: float(v) if isinstance(v, (np.integer, np.floating)) else v 
                               for k, v in metrics.items()}
        json.dump(metrics_serializable, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 结果已保存到: {output_file}")
    
    print("\n" + "=" * 80)
    print("📋 下一步操作")
    print("=" * 80)
    print("1. 在Streamlit版本中运行相同的数据")
    print("2. 记录Streamlit的计算结果")
    print("3. 对比两个版本的差异")
    print("4. 定位差异原因")
    print("5. 修复Dash版本的计算逻辑")
    print("=" * 80)


if __name__ == "__main__":
    main()

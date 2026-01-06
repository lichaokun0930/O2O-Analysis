#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8.6 快速性能测试 - 直接测试核心优化函数

测试方法：
1. 直接加载Excel数据
2. 测试订单聚合性能
3. 对比优化前后的耗时
"""

import sys
import time
import pandas as pd
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

def main():
    print("\n" + "="*80)
    print("V8.6 快速性能测试")
    print("="*80)
    
    # 1. 加载数据
    print("\n[1/3] 加载测试数据...")
    try:
        data_dir = APP_DIR / "实际数据"
        # 排除Excel临时文件（~$开头）
        excel_files = [f for f in data_dir.glob("*.xlsx") if not f.name.startswith('~$')]
        
        if not excel_files:
            print("❌ 未找到Excel数据文件")
            return
        
        latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
        print(f"   文件: {latest_file.name}")
        
        df = pd.read_excel(latest_file)
        print(f"✅ 数据加载成功: {len(df):,} 行")
        
        # 标准化字段
        if '下单时间' in df.columns:
            df['日期'] = pd.to_datetime(df['下单时间'])
        if '销量' in df.columns:
            df['月售'] = df['销量']
        if '成本' in df.columns and '商品采购成本' not in df.columns:
            df['商品采购成本'] = df['成本']
        
        print(f"   日期范围: {df['日期'].min().date()} ~ {df['日期'].max().date()}")
        print(f"   订单数: {df['订单ID'].nunique():,}")
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 测试V8.6优化版本
    print("\n[2/3] 测试V8.6优化版本...")
    try:
        # 直接导入，避免callbacks模块的依赖问题
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "diagnosis_analysis",
            APP_DIR / "components" / "today_must_do" / "diagnosis_analysis.py"
        )
        diagnosis_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(diagnosis_module)
        
        calculate_order_aggregation = diagnosis_module.calculate_order_aggregation
        get_diagnosis_summary = diagnosis_module.get_diagnosis_summary
        
        # 测试统一订单聚合
        print("\n   测试1: 统一订单聚合函数")
        start = time.time()
        order_agg = calculate_order_aggregation(df)
        agg_time = time.time() - start
        
        print(f"   ✅ 订单聚合完成")
        print(f"      耗时: {agg_time:.2f}秒")
        print(f"      订单数: {len(order_agg):,}")
        print(f"      字段数: {len(order_agg.columns)}")
        
        # 测试完整诊断
        print("\n   测试2: 完整诊断分析")
        start = time.time()
        result = get_diagnosis_summary(df)
        total_time = time.time() - start
        
        print(f"   ✅ 诊断分析完成")
        print(f"      总耗时: {total_time:.2f}秒")
        print(f"      紧急问题:")
        print(f"         穿底订单: {result['urgent']['overflow']['count']}单")
        print(f"         高配送费: {result['urgent']['delivery']['count']}单")
        print(f"         热销缺货: {result['urgent']['stockout']['count']}个")
        
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 性能评估
    print("\n[3/3] 性能评估...")
    print(f"   实际耗时: {total_time:.2f}秒")
    
    v85_estimated = 70  # 用户反馈的V8.5耗时
    
    if total_time < 30:
        status = "✅ 优秀"
        improvement = v85_estimated / total_time
        print(f"   {status} - 性能提升 {improvement:.1f}倍")
        print(f"   时间节省: {v85_estimated - total_time:.1f}秒")
    elif total_time < 50:
        status = "⚠️ 良好"
        improvement = v85_estimated / total_time
        print(f"   {status} - 性能提升 {improvement:.1f}倍")
        print(f"   时间节省: {v85_estimated - total_time:.1f}秒")
    else:
        status = "❌ 需要进一步优化"
        print(f"   {status} - 仍需 {total_time:.1f}秒")
    
    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    
    if total_time < 30:
        print("✅ V8.6优化成功！")
        print(f"   加载时间从 {v85_estimated}秒 降低到 {total_time:.2f}秒")
        print(f"   性能提升 {v85_estimated/total_time:.1f}倍")
        print("\n🎉 优化达到预期目标！")
    elif total_time < 50:
        print("⚠️ V8.6优化有效，但仍有提升空间")
        print(f"   当前耗时: {total_time:.2f}秒")
        print(f"   建议: 继续实施V8.6.2（Redis缓存）")
    else:
        print("❌ 优化效果不明显")
        print(f"   当前耗时: {total_time:.2f}秒")
        print(f"   建议: 检查数据规模和代码逻辑")
    
    print("="*80 + "\n")


if __name__ == '__main__':
    main()

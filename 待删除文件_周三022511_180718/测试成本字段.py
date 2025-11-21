#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试成本结构分析的字段名"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from database.data_source_manager import DataSourceManager

# 初始化数据源管理器
dsm = DataSourceManager()

# 加载数据
print("🔍 加载数据...")
df, df_full = dsm.load_data('学习数据仓库/learning_data.db')

print(f"\n📊 数据形状: {df.shape}")
print(f"📋 所有字段: {df.columns.tolist()}\n")

# 检查成本相关字段
cost_fields = [col for col in df.columns if '成本' in col]
print(f"🔍 包含'成本'的字段: {cost_fields}\n")

# 检查具体数据
if '商品采购成本' in df.columns:
    print("✅ '商品采购成本' 字段存在")
    print(f"   总计: ¥{df['商品采购成本'].sum():,.2f}")
    print(f"   非零行数: {(df['商品采购成本'] != 0).sum()}/{len(df)}")
    print(f"   数据范围: {df['商品采购成本'].min():.2f} ~ {df['商品采购成本'].max():.2f}")
    print(f"   均值: {df['商品采购成本'].mean():.2f}")
else:
    print("❌ '商品采购成本' 字段不存在")

if '商品成本' in df.columns:
    print("\n✅ '商品成本' 字段存在")
    print(f"   总计: ¥{df['商品成本'].sum():,.2f}")
    print(f"   非零行数: {(df['商品成本'] != 0).sum()}/{len(df)}")
else:
    print("\n❌ '商品成本' 字段不存在")

# 检查其他成本字段
if '配送费成本' in df.columns:
    print(f"\n✅ '配送费成本': ¥{df['配送费成本'].sum():,.2f}")
else:
    print("\n❌ '配送费成本' 字段不存在")

if '物流配送费' in df.columns:
    print(f"✅ '物流配送费': ¥{df['物流配送费'].sum():,.2f}")
else:
    print("❌ '物流配送费' 字段不存在")

print("\n" + "="*80)
print("💡 结论:")
print("   看板使用的字段名: '商品成本'")
print("   数据库返回的字段名: '商品采购成本'")
print("   需要: 在看板中将 '商品成本' 改为 '商品采购成本'")
print("="*80)

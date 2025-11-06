#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模拟完整数据处理流程，找出问题所在"""

import pandas as pd
import sys

# 模拟normalize_label函数
LABEL_MAPPINGS = {
    "订单编号": "订单ID",
    "单号": "订单ID",
    "销售额": "订单零售额",
    "实收金额": "实收价格",
    "订单金额": "订单零售额",
    "数量": "销量",
    "销售量": "销量",
    "卖价": "商品实售价",
    "售价": "商品实售价",
    "原售价": "商品原价",
    "商品成本": "成本",
    "商品成本价": "成本",
    "利润": "利润额",
    "配送费": "物流配送费",
    "配送成本": "物流配送费",
    "佣金": "平台佣金",
    "平台费用": "平台佣金",
    "距离": "配送距离",
    "送达距离": "配送距离",
    "地址": "收货地址",
    "收货地点": "收货地址",
    "一级分类": "一级分类名",
    "三级分类": "三级分类名",
    "门店ID": "门店ID",
    "店铺ID": "门店ID",
}

def normalize_label(label):
    label = str(label).strip()
    return LABEL_MAPPINGS.get(label, label)

def rename_columns(df):
    """统一DataFrame列名"""
    rename_map = {}
    for col in df.columns:
        normalized = normalize_label(col)
        rename_map[col] = normalized
    return df.rename(columns=rename_map)

# 读取真实数据
print("=" * 80)
print("步骤1: 读取原始Excel文件")
print("=" * 80)

file_path = "门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df_original = pd.read_excel(file_path)

print(f"\n原始数据:")
print(f"  形状: {df_original.shape}")
print(f"  列名数量: {len(df_original.columns)}")
print(f"  列名: {df_original.columns.tolist()}")
print(f"\n'订单ID'列类型: {type(df_original['订单ID'])}")
print(f"是DataFrame: {isinstance(df_original['订单ID'], pd.DataFrame)}")
print(f"是Series: {isinstance(df_original['订单ID'], pd.Series)}")

# 应用rename_columns
print("\n" + "=" * 80)
print("步骤2: 应用rename_columns函数")
print("=" * 80)

df_renamed = rename_columns(df_original)

print(f"\nrename后的数据:")
print(f"  形状: {df_renamed.shape}")
print(f"  列名数量: {len(df_renamed.columns)}")
print(f"  列名: {df_renamed.columns.tolist()}")

print(f"\n检查'订单ID'列:")
if '订单ID' in df_renamed.columns:
    print(f"  列类型: {type(df_renamed['订单ID'])}")
    print(f"  是DataFrame: {isinstance(df_renamed['订单ID'], pd.DataFrame)}")
    print(f"  是Series: {isinstance(df_renamed['订单ID'], pd.Series)}")
    
    # 检查是否有重复列名
    if isinstance(df_renamed['订单ID'], pd.DataFrame):
        print(f"  ⚠️ 警告：'订单ID'返回DataFrame！")
        print(f"  DataFrame形状: {df_renamed['订单ID'].shape}")
        print(f"  DataFrame列名: {df_renamed['订单ID'].columns.tolist()}")
    else:
        print(f"  ✅ '订单ID'是Series")
        print(f"  唯一值数量: {df_renamed['订单ID'].nunique()}")
else:
    print(f"  ❌ '订单ID'列不存在！")
    print(f"  可用列: {[c for c in df_renamed.columns if 'ID' in c or '订单' in c]}")

# 检查重复列名
print("\n" + "=" * 80)
print("步骤3: 检查rename后是否产生重复列名")
print("=" * 80)

from collections import Counter
col_counts = Counter(df_renamed.columns)
duplicates = {col: count for col, count in col_counts.items() if count > 1}

if duplicates:
    print(f"\n⚠️ 发现重复列名！")
    for col, count in duplicates.items():
        print(f"  '{col}': 出现 {count} 次")
        positions = [i for i, c in enumerate(df_renamed.columns.tolist()) if c == col]
        print(f"    位置: {positions}")
        print(f"    原始列名: {[df_original.columns[i] for i in positions]}")
else:
    print(f"\n✅ 没有重复列名")

# 测试groupby操作
print("\n" + "=" * 80)
print("步骤4: 测试groupby操作")
print("=" * 80)

# 添加时段列
df_renamed['下单时间'] = pd.to_datetime(df_renamed['下单时间'])
df_renamed['时段'] = df_renamed['下单时间'].dt.hour.apply(
    lambda x: '早餐刚需' if 6 <= x < 9 
    else '正餐高峰' if 11 <= x < 14 or 17 <= x < 20
    else '休闲娱乐' if 14 <= x < 17 or 20 <= x < 22
    else '深夜应急'
)

print(f"\n测试 groupby('时段')['订单ID'].nunique():")
try:
    result = df_renamed.groupby('时段')['订单ID'].nunique()
    print(f"✅ 成功:")
    print(result)
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试真实错误原因"""

import pandas as pd

# 读取数据
df = pd.read_excel("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")

print(f"数据形状: {df.shape}")
print(f"\n列名类型: {type(df.columns)}")
print(f"\n'订单ID'列的类型: {type(df['订单ID'])}")
print(f"\n是否为DataFrame: {isinstance(df['订单ID'], pd.DataFrame)}")
print(f"\n是否为Series: {isinstance(df['订单ID'], pd.Series)}")

print(f"\n\n测试groupby操作:")
try:
    # 添加时段列（模拟真实场景）
    df['时段'] = pd.to_datetime(df['下单时间']).dt.hour.apply(
        lambda x: '早餐刚需' if 6 <= x < 9 
        else '正餐高峰' if 11 <= x < 14 or 17 <= x < 20
        else '休闲娱乐' if 14 <= x < 17 or 20 <= x < 22
        else '深夜应急'
    )
    
    print("\n方法1: 直接groupby")
    result1 = df.groupby('时段')['订单ID'].nunique()
    print(f"✅ 成功: {result1}")
    
    print("\n\n方法2: 使用apply + iloc (原代码方式)")
    order_id_col = df['订单ID']
    result2 = df.groupby('时段').apply(lambda x: order_id_col.iloc[x.index].nunique())
    print(f"结果: {result2}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n\n检查索引:")
print(f"索引类型: {type(df.index)}")
print(f"索引前10个: {df.index[:10].tolist()}")
print(f"索引是否唯一: {df.index.is_unique}")

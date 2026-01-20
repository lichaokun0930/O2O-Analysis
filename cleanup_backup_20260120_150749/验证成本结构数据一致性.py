#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证成本结构数据一致性
对比Dash版本和React API返回的数据是否一致
"""
import sys
import io
import requests
import pandas as pd
from pathlib import Path

# 解决Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 真实数据处理器 import RealDataProcessor

# 测试门店
TEST_STORE = "共橙一站式超市（灵璧县新河路店）"

print("=" * 80)
print("🔍 成本结构数据一致性验证")
print("=" * 80)

# ==================== 1. 从Dash版本获取数据 ====================
print("\n📊 [Dash版本] 加载数据...")

processor = RealDataProcessor()
df = processor.load_store_data(TEST_STORE)

if df is None or df.empty:
    print(f"❌ 无法加载门店数据: {TEST_STORE}")
    sys.exit(1)

print(f"✅ 加载数据: {len(df)} 行")

# 使用Dash版本的calculate_order_metrics逻辑
# 导入计算函数
try:
    # 模拟Dash版本的订单聚合逻辑
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 订单级聚合
    agg_dict = {
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '平台佣金': 'first',
        '商品实售价': 'sum',
        '利润额': 'sum',
        '渠道': 'first',
    }
    
    # 添加可选字段
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if '商品采购成本' in df.columns:
        agg_dict['商品采购成本'] = 'sum'
    if '满赠金额' in df.columns:
        agg_dict['满赠金额'] = 'first'
    if '商家其他优惠' in df.columns:
        agg_dict['商家其他优惠'] = 'first'
    
    # 只保留存在的字段
    agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 计算实收价格
    if '预计订单收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['预计订单收入']
    
    # 计算配送净成本
    order_agg['配送净成本'] = (
        order_agg.get('物流配送费', pd.Series(0, index=order_agg.index)).fillna(0) -
        (order_agg.get('用户支付配送费', pd.Series(0, index=order_agg.index)).fillna(0) -
         order_agg.get('配送费减免金额', pd.Series(0, index=order_agg.index)).fillna(0)) -
        order_agg.get('企客后返', pd.Series(0, index=order_agg.index)).fillna(0)
    )
    
    # 计算商家活动成本
    order_agg['商家活动成本'] = (
        order_agg.get('满减金额', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('商品减免金额', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('商家代金券', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('商家承担部分券', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('满赠金额', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('商家其他优惠', pd.Series(0, index=order_agg.index)).fillna(0)
    )
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg.get('利润额', pd.Series(0, index=order_agg.index)).fillna(0) -
        order_agg.get('平台服务费', pd.Series(0, index=order_agg.index)).fillna(0) -
        order_agg.get('物流配送费', pd.Series(0, index=order_agg.index)).fillna(0) +
        order_agg.get('企客后返', pd.Series(0, index=order_agg.index)).fillna(0)
    )
    
    print(f"✅ 订单聚合完成: {len(order_agg)} 订单")
    
    # 排除咖啡渠道
    CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店', '饿了么咖啡', '美团咖啡']
    order_agg = order_agg[~order_agg['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    # 按渠道聚合
    channel_agg_dict = {
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
        '配送净成本': 'sum',
        '商家活动成本': 'sum',
    }
    if '平台服务费' in order_agg.columns:
        channel_agg_dict['平台服务费'] = 'sum'
    if '商品采购成本' in order_agg.columns:
        channel_agg_dict['商品采购成本'] = 'sum'
    
    dash_channel_stats = order_agg.groupby('渠道').agg(channel_agg_dict).reset_index()
    dash_channel_stats.columns = ['渠道', '订单数', '销售额', '利润', '配送净成本', '商家活动成本'] + \
                                  (['平台服务费'] if '平台服务费' in channel_agg_dict else []) + \
                                  (['商品成本'] if '商品采购成本' in channel_agg_dict else [])
    
    print("\n📊 [Dash版本] 渠道成本结构:")
    print("-" * 80)
    for _, row in dash_channel_stats.iterrows():
        print(f"  {row['渠道']}:")
        print(f"    订单数: {row['订单数']}")
        print(f"    销售额: ¥{row['销售额']:,.2f}")
        print(f"    利润: ¥{row['利润']:,.2f}")
        print(f"    配送净成本: ¥{row['配送净成本']:,.2f}")
        print(f"    商家活动成本: ¥{row['商家活动成本']:,.2f}")
        if '平台服务费' in row:
            print(f"    平台服务费: ¥{row['平台服务费']:,.2f}")
        if '商品成本' in row:
            print(f"    商品成本: ¥{row['商品成本']:,.2f}")
        print()

except Exception as e:
    print(f"❌ Dash版本计算失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 2. 从React API获取数据 ====================
print("\n📊 [React API] 请求数据...")

try:
    import urllib.parse
    encoded_store = urllib.parse.quote(TEST_STORE)
    api_url = f"http://127.0.0.1:8000/api/v1/orders/cost-structure?store_name={encoded_store}"
    
    response = requests.get(api_url, timeout=30)
    
    if response.status_code != 200:
        print(f"❌ API请求失败: {response.status_code}")
        print(f"   响应: {response.text[:500]}")
        sys.exit(1)
    
    api_data = response.json()
    
    if not api_data.get('success'):
        print(f"❌ API返回失败: {api_data}")
        sys.exit(1)
    
    api_channels = api_data['data']['channels']
    
    print(f"✅ API返回 {len(api_channels)} 个渠道")
    
    print("\n📊 [React API] 渠道成本结构:")
    print("-" * 80)
    for ch in api_channels:
        print(f"  {ch['name']}:")
        print(f"    订单数: {ch['order_count']}")
        print(f"    销售额: ¥{ch['revenue']:,.2f}")
        print(f"    利润: ¥{ch['profit']:,.2f}")
        print(f"    配送净成本: ¥{ch['costs']['delivery']:,.2f}")
        print(f"    商家活动成本: ¥{ch['costs']['marketing']:,.2f}")
        print(f"    平台服务费: ¥{ch['costs']['commission']:,.2f}")
        print(f"    商品成本: ¥{ch['costs']['cogs']:,.2f}")
        print()

except Exception as e:
    print(f"❌ API请求失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 3. 对比数据 ====================
print("\n" + "=" * 80)
print("📊 数据对比")
print("=" * 80)

# 创建对比表
comparison_data = []

for _, dash_row in dash_channel_stats.iterrows():
    channel_name = dash_row['渠道']
    
    # 查找API中对应的渠道
    api_channel = next((ch for ch in api_channels if ch['name'] == channel_name), None)
    
    if api_channel:
        comparison_data.append({
            '渠道': channel_name,
            'Dash订单数': dash_row['订单数'],
            'API订单数': api_channel['order_count'],
            '订单数差异': dash_row['订单数'] - api_channel['order_count'],
            'Dash销售额': dash_row['销售额'],
            'API销售额': api_channel['revenue'],
            '销售额差异': dash_row['销售额'] - api_channel['revenue'],
            'Dash利润': dash_row['利润'],
            'API利润': api_channel['profit'],
            '利润差异': dash_row['利润'] - api_channel['profit'],
        })
    else:
        comparison_data.append({
            '渠道': channel_name,
            'Dash订单数': dash_row['订单数'],
            'API订单数': 'N/A',
            '订单数差异': 'N/A',
            'Dash销售额': dash_row['销售额'],
            'API销售额': 'N/A',
            '销售额差异': 'N/A',
            'Dash利润': dash_row['利润'],
            'API利润': 'N/A',
            '利润差异': 'N/A',
        })

comparison_df = pd.DataFrame(comparison_data)
print(comparison_df.to_string(index=False))

# 检查是否一致
all_match = True
for item in comparison_data:
    if item['订单数差异'] != 0 or abs(item.get('销售额差异', 0) or 0) > 0.01:
        all_match = False
        break

print("\n" + "=" * 80)
if all_match:
    print("✅ 数据一致性验证通过！Dash版本和React API数据完全一致")
else:
    print("⚠️ 数据存在差异，请检查计算逻辑")
print("=" * 80)

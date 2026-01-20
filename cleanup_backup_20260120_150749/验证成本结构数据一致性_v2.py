#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证成本结构数据一致性 v2
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

# 测试门店
TEST_STORE = "共橙一站式超市（灵璧县新河路店）"

print("=" * 80)
print("🔍 成本结构数据一致性验证 v2")
print("=" * 80)

# ==================== 1. 使用与Dash版本相同的逻辑计算 ====================
print("\n📊 [Dash版本逻辑] 加载数据...")

# 加载数据
data_dir = APP_DIR / "实际数据"
order_file = None
for f in data_dir.glob("*.xlsx"):
    if "订单" in f.name:
        order_file = f
        break

if not order_file:
    print("❌ 未找到订单数据文件")
    sys.exit(1)

df = pd.read_excel(order_file)
print(f"✅ 加载数据: {len(df)} 行")

# 筛选门店
df = df[df['门店名称'] == TEST_STORE].copy()
print(f"✅ 筛选门店后: {len(df)} 行")

# 排除咖啡渠道
CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店', '饿了么咖啡', '美团咖啡']
df = df[~df['渠道'].isin(CHANNELS_TO_REMOVE)]
print(f"✅ 排除咖啡渠道后: {len(df)} 行")

# 订单级聚合（与Dash版本calculate_order_metrics一致）
df['订单ID'] = df['订单ID'].astype(str)

# 空值填充
df['物流配送费'] = df['物流配送费'].fillna(0)
df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
df['用户支付配送费'] = df['用户支付配送费'].fillna(0)

# 计算订单总收入
sales_field = '月售' if '月售' in df.columns else '销量'
if '实收价格' in df.columns and sales_field in df.columns:
    df['订单总收入'] = df['实收价格'] * df[sales_field]

# 订单级聚合
agg_dict = {
    '商品实售价': 'sum',
    '预计订单收入': 'sum',
    '用户支付配送费': 'first',
    '配送费减免金额': 'first',
    '物流配送费': 'first',
    '平台佣金': 'first',
    '渠道': 'first',
}

if sales_field in df.columns:
    agg_dict[sales_field] = 'sum'
if '平台服务费' in df.columns:
    agg_dict['平台服务费'] = 'sum'
if '订单总收入' in df.columns:
    agg_dict['订单总收入'] = 'sum'
if '利润额' in df.columns:
    agg_dict['利润额'] = 'sum'
if '企客后返' in df.columns:
    agg_dict['企客后返'] = 'sum'
if '商品采购成本' in df.columns:
    agg_dict['商品采购成本'] = 'sum'

# 商家活动成本相关字段 (v3.1更新：包含全部8个营销字段)
for field in ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']:
    if field in df.columns:
        agg_dict[field] = 'first'

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()

# 将订单总收入重命名为实收价格
if '订单总收入' in order_agg.columns:
    order_agg['实收价格'] = order_agg['订单总收入']

# 关键字段兜底
if '平台服务费' not in order_agg.columns:
    order_agg['平台服务费'] = 0
order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)

if '企客后返' not in order_agg.columns:
    order_agg['企客后返'] = 0
order_agg['企客后返'] = order_agg['企客后返'].fillna(0)

if '利润额' not in order_agg.columns:
    order_agg['利润额'] = 0
order_agg['利润额'] = order_agg['利润额'].fillna(0)

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] -
    order_agg['平台服务费'] -
    order_agg['物流配送费'] +
    order_agg['企客后返']
)

# 计算配送净成本
order_agg['配送净成本'] = (
    order_agg['物流配送费'] -
    (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) -
    order_agg['企客后返']
)

# 计算商家活动成本 (v3.1更新：包含全部8个营销字段)
marketing_fields = ['配送费减免金额', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
order_agg['商家活动成本'] = 0
for field in marketing_fields:
    if field in order_agg.columns:
        order_agg['商家活动成本'] += order_agg[field].fillna(0)

# ==================== 过滤异常订单（与Dash版本一致） ====================
# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播',
    '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
]

# 过滤：收费渠道 且 平台服务费<=0 的订单
is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
is_zero_fee = order_agg['平台服务费'] <= 0
invalid_orders = is_fee_channel & is_zero_fee
print(f"⚠️ 过滤异常订单: {invalid_orders.sum()} 单 (收费渠道但平台服务费=0)")
order_agg = order_agg[~invalid_orders].copy()

print(f"✅ 订单聚合完成: {len(order_agg)} 订单")

# 按渠道聚合
channel_agg_dict = {
    '订单ID': 'count',
    '实收价格': 'sum',
    '订单实际利润': 'sum',
    '配送净成本': 'sum',
    '商家活动成本': 'sum',
    '平台服务费': 'sum',
}
if '商品采购成本' in order_agg.columns:
    channel_agg_dict['商品采购成本'] = 'sum'

dash_channel_stats = order_agg.groupby('渠道').agg(channel_agg_dict).reset_index()

print("\n📊 [Dash版本] 渠道成本结构:")
print("-" * 80)
for _, row in dash_channel_stats.iterrows():
    print(f"  {row['渠道']}:")
    print(f"    订单数: {row['订单ID']}")
    print(f"    销售额: ¥{row['实收价格']:,.2f}")
    print(f"    利润: ¥{row['订单实际利润']:,.2f}")
    print(f"    配送净成本: ¥{row['配送净成本']:,.2f}")
    print(f"    商家活动成本: ¥{row['商家活动成本']:,.2f}")
    print(f"    平台服务费: ¥{row['平台服务费']:,.2f}")
    if '商品采购成本' in row:
        print(f"    商品成本: ¥{row['商品采购成本']:,.2f}")
    print()

# ==================== 2. 从React API获取数据 ====================
print("\n📊 [React API] 请求数据...")

try:
    import urllib.parse
    encoded_store = urllib.parse.quote(TEST_STORE)
    api_url = f"http://127.0.0.1:8080/api/v1/orders/cost-structure?store_name={encoded_store}"
    
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
            'Dash订单数': int(dash_row['订单ID']),
            'API订单数': api_channel['order_count'],
            '订单数差异': int(dash_row['订单ID']) - api_channel['order_count'],
            'Dash销售额': round(dash_row['实收价格'], 2),
            'API销售额': api_channel['revenue'],
            '销售额差异': round(dash_row['实收价格'] - api_channel['revenue'], 2),
            'Dash配送成本': round(dash_row['配送净成本'], 2),
            'API配送成本': api_channel['costs']['delivery'],
            '配送差异': round(dash_row['配送净成本'] - api_channel['costs']['delivery'], 2),
            'Dash营销成本': round(dash_row['商家活动成本'], 2),
            'API营销成本': api_channel['costs']['marketing'],
            '营销差异': round(dash_row['商家活动成本'] - api_channel['costs']['marketing'], 2),
        })
    else:
        comparison_data.append({
            '渠道': channel_name,
            'Dash订单数': int(dash_row['订单ID']),
            'API订单数': 'N/A',
            '订单数差异': 'N/A',
            'Dash销售额': round(dash_row['实收价格'], 2),
            'API销售额': 'N/A',
            '销售额差异': 'N/A',
            'Dash配送成本': round(dash_row['配送净成本'], 2),
            'API配送成本': 'N/A',
            '配送差异': 'N/A',
            'Dash营销成本': round(dash_row['商家活动成本'], 2),
            'API营销成本': 'N/A',
            '营销差异': 'N/A',
        })

comparison_df = pd.DataFrame(comparison_data)
print(comparison_df.to_string(index=False))

# 检查是否一致
all_match = True
for item in comparison_data:
    if isinstance(item['订单数差异'], int) and item['订单数差异'] != 0:
        all_match = False
        break
    if isinstance(item['销售额差异'], float) and abs(item['销售额差异']) > 0.01:
        all_match = False
        break
    if isinstance(item['配送差异'], float) and abs(item['配送差异']) > 0.01:
        all_match = False
        break
    if isinstance(item['营销差异'], float) and abs(item['营销差异']) > 0.01:
        all_match = False
        break

print("\n" + "=" * 80)
if all_match:
    print("✅ 数据一致性验证通过！Dash版本和React API数据完全一致")
else:
    print("⚠️ 数据存在差异，请检查计算逻辑")
print("=" * 80)

# TAB1实收价格修复总结

## 修复日期
2025年11月17日

## 问题描述
TAB1中所有关于"实收价格"字段的数据计算都没有乘以销量，导致TAB1中所有和"实收价格"字段相关的计算逻辑都是错误的。

## 根本原因
**字段含义理解错误**：
- `实收价格` = **单价**（不含销量）
- `成本` = **总额**（已乘销量）
- `利润额` = **总额**（已乘销量）

**错误做法**：
```python
# ❌ 直接sum单价
order_agg = df.groupby('订单ID').agg({'实收价格': 'sum'})
```

**正确做法**：
```python
# ✅ 先计算订单总收入 = 单价 × 销量，再sum
df['订单总收入'] = df['实收价格'] * df['销量']
order_agg = df.groupby('订单ID').agg({'订单总收入': 'sum'})
order_agg['实收价格'] = order_agg['订单总收入']  # 重命名
```

## 修复内容

### 1. 核心函数修复（行9625-9750）
**文件**: `智能门店看板_Dash版.py`  
**函数**: `calculate_order_metrics`

**修复点**：
1. 添加销量字段兼容（月售/销量）
2. 前置计算订单总收入 = 实收价格 × 销量
3. 修改聚合字典使用订单总收入
4. 聚合后重命名为实收价格

**代码**：
```python
# 兼容不同销量字段名
sales_field = '月售' if '月售' in df.columns else '销量'

# 前置计算订单总收入
if '实收价格' in df.columns and sales_field in df.columns:
    df['订单总收入'] = df['实收价格'] * df[sales_field]
    print(f"🔧 [实收价格修复] 计算订单总收入 = 实收价格 × {sales_field}")

# 聚合时使用订单总收入
if '订单总收入' in df.columns:
    agg_dict['订单总收入'] = 'sum'

# 聚合后重命名
order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
if '订单总收入' in order_agg.columns:
    order_agg['实收价格'] = order_agg['订单总收入']
```

### 2. 默认计算模式修复（行303-318）
**问题**: 默认模式`service_fee_positive`会过滤掉平台服务费=0的订单，导致丢失80个订单（1,015.46元）

**修复**：
```python
# 修复前
DEFAULT_CALCULATION_MODE = 'service_fee_positive'  # ❌ 会过滤订单

# 修复后
DEFAULT_CALCULATION_MODE = 'all_with_fallback'  # ✅ 包含所有订单
```

### 3. 渠道对比功能修复（行2619-2632）
**函数**: `_create_channel_comparison_cards`

**修复代码**：
```python
if '实收价格' not in order_agg.columns and '实收价格' in df.columns:
    if '月售' in df.columns:
        df_temp = df.copy()
        df_temp['订单总收入'] = df_temp['实收价格'] * df_temp['月售']
        order_actual_price = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
        order_actual_price.columns = ['订单ID', '实收价格']
        print(f"🔧 [渠道对比] 实收价格修复: 使用(实收价格×月售)聚合")
    else:
        # 兜底方案
        order_actual_price = df.groupby('订单ID')['实收价格'].sum().reset_index()
        print(f"⚠️ [渠道对比] 实收价格兜底: 直接sum（缺少月售字段）")
```

### 4. 一级分类聚合修复（行8880-8890）
**函数**: 分类统计相关

**修复代码**：
```python
# 如果都没有，从df按订单聚合实收价格
sales_col = '月售' if '月售' in df.columns else '销量'
if sales_col in df.columns:
    df_temp = df.copy()
    df_temp['订单总收入'] = df_temp['实收价格'] * df_temp[sales_col]
    order_sales = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
    order_sales.columns = ['订单ID', '实收价格']
    print(f"🔧 [一级分类聚合] 实收价格修复: 使用(实收价格×{sales_col})聚合")
```

### 5. 分类销售占比修复（行11558）
**函数**: `update_category_trend_by_channel`

**修复代码**：
```python
# 按分类聚合销售额
sales_col = '月售' if '月售' in df_filtered.columns else '销量'
if sales_col in df_filtered.columns:
    df_filtered_temp = df_filtered.copy()
    df_filtered_temp['订单总收入'] = df_filtered_temp['实收价格'] * df_filtered_temp[sales_col]
    category_sales = df_filtered_temp.groupby('一级分类名')['订单总收入'].sum().sort_values(ascending=False)
    print(f"🔧 [分类销售占比] 实收价格修复: 使用(实收价格×{sales_col})聚合")
```

### 6. 四象限分析修复（行12700-12720）
**函数**: 四象限分析相关

**修复代码**：
```python
# 计算每个订单的商品总销售额（用于分配利润）
sales_col = '月售' if '月售' in df.columns else '销量'
if sales_col in df.columns:
    df_temp = df.copy()
    df_temp['订单总收入'] = df_temp['实收价格'] * df_temp[sales_col]
    order_sales_sum = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
    order_sales_sum.columns = ['订单ID', '订单商品总额']
    print(f"🔧 [四象限分析] 实收价格修复: 使用(实收价格×{sales_col})计算订单商品总额")
    # 同时计算单个商品的总收入
    df_with_profit['商品总收入'] = df_with_profit['实收价格'] * df_with_profit[sales_col]
```

### 7. 时段分析修复（行14645-14655）
**函数**: `calculate_period_metrics`

**修复代码**：
```python
sales_col = '月售' if '月售' in period_df.columns else '销量'
if sales_col in period_df.columns:
    period_df_temp = period_df.copy()
    period_df_temp['订单总收入'] = period_df_temp['实收价格'] * period_df_temp[sales_col]
    order_sales = period_df_temp.groupby('订单ID')['订单总收入'].sum()
else:
    order_sales = period_df.groupby('订单ID')['实收价格'].sum()
```

### 8. 场景分析修复（行14685-14695）
**函数**: `calculate_scenario_metrics`

**修复代码**：
```python
sales_col = '月售' if '月售' in scenario_df.columns else '销量'
if sales_col in scenario_df.columns:
    scenario_df_temp = scenario_df.copy()
    scenario_df_temp['订单总收入'] = scenario_df_temp['实收价格'] * scenario_df_temp[sales_col]
    order_sales = scenario_df_temp.groupby('订单ID')['订单总收入'].sum()
else:
    order_sales = scenario_df.groupby('订单ID')['实收价格'].sum()
```

## 修复效果验证

### 测试数据
- 数据源：郭庄路.xlsx
- 记录数：6185条
- 订单数：2027个

### 验证结果
| 测试点 | 修复前 | 修复后 | 差异 | 状态 |
|--------|--------|--------|------|------|
| 核心函数 | 43,164.20元 | 46,775.27元 | +3,611.07元 (+8.4%) | ✅ |
| 订单数 | 1,947个 | 2,027个 | +80个 (+4.1%) | ✅ |
| 一级分类聚合 | - | 46,775.27元 | - | ✅ |
| 分类销售占比 | - | 46,775.27元 | - | ✅ |
| 四象限分析 | - | 46,775.27元 | - | ✅ |
| 时段分析 | - | 46,775.27元 | - | ✅ |
| 场景分析 | - | 46,775.27元 | - | ✅ |

### 数据准确性
所有测试点的计算结果都是**46,775.27元**，与正确值完全一致！

## 影响范围
1. **Tab1 - 订单数据概览**：所有使用实收价格的指标
2. **渠道对比功能**：渠道销售额计算
3. **分类统计**：一级分类销售额和占比
4. **四象限分析**：订单商品总额和利润分配
5. **时段分析**：时段销售额和客单价
6. **场景分析**：场景销售额和客单价

## 兼容性处理
1. **销量字段兼容**：支持"月售"或"销量"两种字段名
2. **兜底方案**：当缺少销量字段时，仍然使用直接sum（虽然不准确，但避免崩溃）
3. **调试信息**：每个修复点都添加了打印信息，方便追踪

## 注意事项
1. **order_agg['实收价格']含义变化**：修复后，`calculate_order_metrics`函数返回的`order_agg['实收价格']`是订单总收入（已乘销量），而不是单价
2. **向后兼容**：所有使用`order_agg['实收价格']`的地方无需修改，因为它们本来就期望得到订单总收入
3. **新增代码规范**：以后直接从df聚合实收价格时，必须先乘以销量

## 测试脚本
- `测试TAB1实收价格修复.py` - 核心功能测试
- `验证全部修复.py` - 全面验证所有修复点
- `调试订单ID差异.py` - 订单丢失问题诊断
- `检查订单过滤.py` - 订单过滤逻辑检查

## 总结
本次修复解决了TAB1中所有与实收价格相关的计算错误，主要包括：
1. ✅ 核心聚合逻辑修复（实收价格×销量）
2. ✅ 订单过滤问题修复（恢复80个订单）
3. ✅ 所有直接从df聚合实收价格的地方都已修复
4. ✅ 所有测试点验证通过

**总修复效果**：
- 数据准确性提升：+8.4%（销售额）
- 订单完整性提升：+4.1%（订单数）
- 所有计算结果与正确值完全一致

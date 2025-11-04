# 📊 Dash看板统一计算标准 v2.0

**制定日期**: 2025-10-24  
**适用范围**: 所有Dash版本看板  
**状态**: ✅ 生产标准

---

## 🎯 核心原则

**所有Dash看板必须遵循统一的数据处理和计算逻辑，确保指标口径一致！**

---

## 📐 第一层：数据预处理（入口层）

### 1.1 数据加载与标准化

**处理器**: `真实数据处理器.py` → `RealDataProcessor.standardize_sales_data()`

```python
from 真实数据处理器 import RealDataProcessor

# 标准加载流程
def load_and_standardize_data(df_raw):
    """统一数据加载流程"""
    # Step 1: 字段标准化映射（14个核心字段）
    processor = RealDataProcessor()
    df_std = processor.standardize_sales_data(df_raw)
    
    # Step 2: 业务规则过滤
    df_clean = apply_business_rules(df_std)
    
    # Step 3: 场景时段推断
    df_final = add_scene_and_timeslot_fields(df_clean)
    
    return df_final
```

#### 🔑 核心字段映射（14个）

| 标准字段名 | 可能来源字段 | 数据类型 | 说明 |
|-----------|------------|---------|------|
| **商品名称** | 商品名称, product_name, 名称 | str | 必需 |
| **商品实售价** | 售价, 商品实售价, price, 实售价 | float | 必需，用于毛利率计算 |
| **商品采购成本** | 成本, 原价, cost, 进货价 | float | 必需，用于利润计算 |
| **日期** | 日期, date, **下单时间**, 采集时间 | datetime | ⭐必需，时间分析基础 |
| **订单ID** | 订单ID, order_id, 订单号 | str | 订单聚合必需 |
| **一级分类名** | 美团一级分类, 一级分类名, category | str | 分类分析 |
| **三级分类名** | 美团三级分类, 三级分类名 | str | 细分分析 |
| **月售** | 月售, monthly_sales, 销量 | int | 销量指标 |
| **库存** | 库存, stock, 剩余库存 | int | 库存分析 |
| **物流配送费** | 物流配送费, 配送费 | float | 成本计算 |
| **平台佣金** | 平台佣金, 佣金, commission | float | 成本计算 |
| **场景** | 场景, scene | str | 场景分析（自动推断） |
| **时段** | 时段, time_period | str | 时段分析（自动推断） |
| **渠道** | 渠道, channel | str | 渠道过滤 |

---

### 1.2 业务规则过滤 ⭐关键

```python
def apply_business_rules(df):
    """应用统一业务规则"""
    original_rows = len(df)
    
    # 规则1：剔除耗材数据（购物袋等非销售商品）
    category_col = None
    for col in ['一级分类名', '美团一级分类', '一级分类']:
        if col in df.columns:
            category_col = col
            break
    
    if category_col:
        df = df[df[category_col] != '耗材'].copy()
        removed = original_rows - len(df)
        print(f"🔴 剔除耗材: {removed:,} 行")
    
    # 规则2：剔除咖啡渠道（非O2O零售核心品类）
    CHANNELS_TO_REMOVE = ['饿了么咖啡', '美团咖啡']
    if '渠道' in df.columns:
        before = len(df)
        df = df[~df['渠道'].isin(CHANNELS_TO_REMOVE)].copy()
        removed = before - len(df)
        print(f"☕ 剔除咖啡渠道: {removed:,} 行")
    
    print(f"📊 最终数据量: {len(df):,} 行")
    return df
```

**业务规则说明**:
- **耗材剔除原因**: 购物袋等耗材不属于销售商品，需单独核算
- **咖啡剔除原因**: 咖啡业务模式不同于O2O零售，需单独分析
- **数据影响**: 约减少5-10%数据量（具体看数据源）

---

### 1.3 场景与时段推断

```python
from scene_inference import add_scene_and_timeslot_fields

def add_scene_and_timeslot_fields(df):
    """自动推断场景和时段"""
    # 基于商品名称、分类、下单时间智能推断
    # 生成2个新字段：'场景'、'时段'
    return df_with_scene_timeslot
```

**推断逻辑**:
- 基于商品关键词（如"豆浆"→早餐场景）
- 基于下单时间（如6-9点→清晨时段）
- 基于商品分类（如"饮料"→下午茶场景）

---

## 📐 第二层：派生字段计算（计算层）

### 2.1 单品级别计算

```python
# 单品毛利
df['单品毛利'] = df['商品实售价'] - df['商品采购成本']

# 单品毛利率（百分比）
df['单品毛利率'] = (
    df['单品毛利'] / df['商品实售价'].where(df['商品实售价'] > 0) * 100
).fillna(0)

# 库存周转率
df['库存周转率'] = (
    df['月售'] / df['库存'].where(df['库存'] > 0)
).fillna(0)
```

**计算原则**:
- ✅ 毛利率基于**商品实售价**，不是预估订单收入
- ✅ 避免除以0，使用`.where()`判断
- ✅ 空值填充为0，不是NaN

---

### 2.2 订单级别聚合 ⭐核心

**原则**: 先按订单聚合，避免重复计算订单级字段

```python
def aggregate_to_order_level(df):
    """订单级聚合（标准流程）"""
    
    order_agg = df.groupby('订单ID').agg({
        # 商品销售额（求和）
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '单品毛利': 'sum',
        '月售': 'sum',
        
        # 订单级字段（取第一个值，避免重复）
        '物流配送费': 'first',
        '平台佣金': 'first',
        '用户支付配送费': 'first',
        '配送费减免': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '打包袋金额': 'first',
        
        # 保留关键信息
        '日期': 'first',
        '渠道': 'first',
        '场景': 'first',
        '时段': 'first'
    }).reset_index()
    
    return order_agg
```

**关键点**:
- ❌ **错误**: `df.groupby('订单ID')['物流配送费'].sum()` → 一个订单的配送费被计算N次
- ✅ **正确**: `df.groupby('订单ID')['物流配送费'].first()` → 每个订单配送费只计算1次

---

### 2.3 订单成本与利润计算 ⭐核心公式

```python
def calculate_order_profit(order_agg):
    """计算订单实际利润（统一标准）"""
    
    # A. 商家活动成本
    order_agg['商家活动成本'] = (
        order_agg['满减金额'].fillna(0) + 
        order_agg['商品减免金额'].fillna(0) + 
        order_agg['商家代金券'].fillna(0) +
        order_agg['商家承担部分券'].fillna(0)  # ⭐重要：商家承担的平台券
    )
    
    # B. 订单总收入
    order_agg['订单总收入'] = (
        order_agg['商品实售价'] +      # 商品销售额
        order_agg['打包袋金额'].fillna(0) +      # 打包袋收入
        order_agg['用户支付配送费'].fillna(0)    # 用户支付的配送费
    )
    
    # C. 订单实际利润 ⭐⭐⭐ 核心公式
    order_agg['订单实际利润'] = (
        order_agg['单品毛利'] -                    # 商品毛利（已扣除成本和活动）
        order_agg['物流配送费'].fillna(0) -       # 商家实际支付的配送成本
        order_agg['平台佣金'].fillna(0)           # 平台佣金
    )
    
    return order_agg
```

**公式说明**:
```
订单实际利润 = 商品毛利 - 物流配送费 - 平台佣金

其中:
- 商品毛利 = 商品销售额 - 商品成本 - 活动成本
- 物流配送费 = 商家实际支付给骑手的费用（不是用户支付的配送费）
- 平台佣金 = 平台抽成
```

---

## 📐 第三层：汇总指标计算（展示层）

### 3.1 基础汇总指标

```python
def calculate_summary_metrics(order_agg):
    """计算汇总指标"""
    
    metrics = {
        # 订单指标
        '订单总数': len(order_agg),
        
        # 销售指标（基于商品销售额）
        '商品销售额': order_agg['商品实售价'].sum(),
        '订单总收入': order_agg['订单总收入'].sum(),
        
        # 利润指标
        '总利润': order_agg['订单实际利润'].sum(),
        '利润率': 0,  # 后续计算
        
        # 成本指标
        '商品成本': order_agg['商品采购成本'].sum(),
        '配送成本': order_agg['物流配送费'].sum(),
        '佣金成本': order_agg['平台佣金'].sum(),
        '活动成本': order_agg['商家活动成本'].sum(),
        
        # 订单均值
        '平均客单价': 0,  # 后续计算
        '平均利润': 0     # 后续计算
    }
    
    # 计算率类指标
    if metrics['商品销售额'] > 0:
        metrics['利润率'] = metrics['总利润'] / metrics['商品销售额'] * 100
    
    if metrics['订单总数'] > 0:
        metrics['平均客单价'] = metrics['商品销售额'] / metrics['订单总数']
        metrics['平均利润'] = metrics['总利润'] / metrics['订单总数']
    
    # 计算盈利订单占比
    profitable_orders = (order_agg['订单实际利润'] > 0).sum()
    metrics['盈利订单占比'] = profitable_orders / metrics['订单总数'] * 100 if metrics['订单总数'] > 0 else 0
    
    return metrics
```

**指标说明**:
- **利润率**: 基于**商品销售额**计算，不是订单总收入
- **平均客单价**: 商品销售额 / 订单数
- **盈利订单占比**: 利润>0的订单数 / 总订单数

---

### 3.2 时间维度聚合

```python
def aggregate_by_time(order_agg, dimension='日期'):
    """按时间维度聚合"""
    
    # 确保日期列是datetime类型
    order_agg['日期'] = pd.to_datetime(order_agg['日期'])
    
    if dimension == '周':
        order_agg['周'] = order_agg['日期'].dt.isocalendar().week
        group_col = '周'
    elif dimension == '月':
        order_agg['月'] = order_agg['日期'].dt.to_period('M').astype(str)
        group_col = '月'
    else:  # 日
        group_col = '日期'
    
    time_agg = order_agg.groupby(group_col).agg({
        '订单ID': 'count',
        '商品实售价': 'sum',
        '订单实际利润': 'sum',
        '订单总收入': 'sum'
    }).reset_index()
    
    time_agg.columns = [group_col, '订单数', '销售额', '利润', '总收入']
    
    return time_agg
```

---

### 3.3 分类维度聚合

```python
def aggregate_by_category(df):
    """按分类聚合（注意：使用原始数据，不是订单聚合数据）"""
    
    # ⚠️ 分类分析要用原始商品明细数据
    # 因为配送费/佣金不能分摊到每个商品
    
    category_agg = df.groupby('一级分类名').agg({
        '商品实售价': 'sum',           # 销售额
        '商品采购成本': 'sum',         # 成本
        '单品毛利': 'sum',             # 毛利
        '月售': 'sum',                 # 销量
        '订单ID': 'nunique'            # 订单数（去重）
    }).reset_index()
    
    category_agg.columns = ['分类', '销售额', '成本', '毛利', '销量', '订单数']
    
    # 计算毛利率
    category_agg['毛利率'] = (
        category_agg['毛利'] / category_agg['销售额'] * 100
    ).fillna(0)
    
    return category_agg
```

**关键点**:
- ✅ 分类分析用**原始明细数据**（df），不是订单聚合数据（order_agg）
- ✅ 订单数使用`nunique()`去重
- ❌ 不要在分类维度计算配送费/佣金（这是订单级成本，无法分摊到商品）

---

## 📐 第四层：周期对比计算（诊断层）

### 4.1 销量下滑诊断

```python
def diagnose_sales_decline(df, current_period, compare_period, time_period='week'):
    """销量下滑诊断（统一标准）"""
    
    # Step 1: 过滤当前周期和对比周期数据
    df_current = filter_by_period(df, current_period, time_period)
    df_compare = filter_by_period(df, compare_period, time_period)
    
    # Step 2: 按商品聚合销量
    current_sales = df_current.groupby('商品名称').agg({
        '月售': 'sum',
        '商品实售价': 'mean',
        '单品毛利率': 'mean'
    }).reset_index()
    
    compare_sales = df_compare.groupby('商品名称').agg({
        '月售': 'sum'
    }).reset_index()
    
    # Step 3: 合并对比
    result = current_sales.merge(
        compare_sales, 
        on='商品名称', 
        how='outer', 
        suffixes=('_当前', '_对比')
    ).fillna(0)
    
    # Step 4: 计算变化
    result['销量变化'] = result['月售_当前'] - result['月售_对比']
    result['变化幅度%'] = (
        result['销量变化'] / result['月售_对比'].where(result['月售_对比'] > 0) * 100
    ).fillna(0)
    
    # Step 5: 筛选下滑商品
    decline_products = result[result['销量变化'] < 0].copy()
    
    # Step 6: 计算损失
    decline_products['收入损失'] = (
        decline_products['销量变化'].abs() * 
        decline_products['商品实售价_当前']
    )
    
    decline_products['利润损失'] = (
        decline_products['收入损失'] * 
        decline_products['单品毛利率_当前'] / 100
    )
    
    return decline_products
```

---

### 4.2 客单价归因分析

```python
def analyze_aov_attribution(df, current_period, compare_period):
    """客单价归因分析"""
    
    # Step 1: 计算订单级客单价
    df_current = filter_by_period(df, current_period)
    df_compare = filter_by_period(df, compare_period)
    
    # 订单聚合
    current_orders = aggregate_to_order_level(df_current)
    compare_orders = aggregate_to_order_level(df_compare)
    
    # 计算平均客单价
    current_aov = current_orders['商品实售价'].mean()
    compare_aov = compare_orders['商品实售价'].mean()
    
    # Step 2: 归因分解
    # 商品数量变化贡献
    current_items_per_order = df_current.groupby('订单ID').size().mean()
    compare_items_per_order = df_compare.groupby('订单ID').size().mean()
    quantity_effect = (current_items_per_order - compare_items_per_order) * compare_aov
    
    # 商品单价变化贡献
    current_avg_price = df_current['商品实售价'].mean()
    compare_avg_price = df_compare['商品实售价'].mean()
    price_effect = (current_avg_price - compare_avg_price) * current_items_per_order
    
    # 交互效应
    interaction_effect = (
        (current_items_per_order - compare_items_per_order) * 
        (current_avg_price - compare_avg_price)
    )
    
    attribution = {
        '客单价变化': current_aov - compare_aov,
        '数量效应': quantity_effect,
        '价格效应': price_effect,
        '交互效应': interaction_effect
    }
    
    return attribution
```

---

## 🔧 第五层：问题诊断引擎（智能层）

### 5.1 诊断引擎初始化

```python
from 问题诊断引擎 import ProblemDiagnosticEngine

# 初始化诊断引擎
engine = ProblemDiagnosticEngine(df_processed)

# 使用诊断功能
decline_result = engine.diagnose_sales_decline(
    current_period_idx=0,
    compare_period_idx=1,
    time_period='week',
    threshold=-100  # 显示所有下滑商品
)
```

**诊断引擎提供的功能**:
1. ✅ 销量下滑诊断
2. ✅ 客单价归因分析
3. ✅ 负毛利预警
4. ✅ 高配送费诊断
5. ✅ 商品角色失衡
6. ✅ 异常波动检测

---

## ⚠️ 常见错误与避免方法

### 错误1: 重复计算订单级字段

```python
# ❌ 错误示例
product_delivery = df.groupby('商品名称')['物流配送费'].sum()
# 问题：一个订单的配送费被计算了N次（N=商品数量）

# ✅ 正确做法
# 先按订单聚合
order_agg = df.groupby('订单ID')['物流配送费'].first()
# 再按商品分析
product_orders = df.groupby('商品名称')['订单ID'].apply(list)
```

---

### 错误2: 利润率基数错误

```python
# ❌ 错误示例
profit_rate = total_profit / total_revenue * 100
# 问题：基数应该是商品销售额，不是订单总收入

# ✅ 正确做法
profit_rate = total_profit / total_sales * 100
# total_sales = 商品销售额（不含配送费）
```

---

### 错误3: 忽略商家承担部分券

```python
# ❌ 错误示例
activity_cost = 满减金额 + 商品减免金额 + 商家代金券

# ✅ 正确做法
activity_cost = (
    满减金额 + 
    商品减免金额 + 
    商家代金券 + 
    商家承担部分券  # ⭐ 重要：这是商家成本
)
```

---

### 错误4: 数据未剔除耗材和咖啡

```python
# ❌ 错误示例
df_std = processor.standardize_sales_data(df_raw)
# 直接使用，未过滤

# ✅ 正确做法
df_std = processor.standardize_sales_data(df_raw)
df_clean = apply_business_rules(df_std)  # ⭐ 必须过滤
```

---

## 📋 各看板应用检查清单

### 销量下滑诊断看板 ✅

- [x] 使用`RealDataProcessor.standardize_sales_data()`
- [x] 应用业务规则过滤（耗材、咖啡）
- [x] 使用`ProblemDiagnosticEngine.diagnose_sales_decline()`
- [x] 周期对比逻辑正确
- [x] 计算收入/利润损失

### 客单价分析看板 ⏸️

- [ ] 使用统一的订单聚合逻辑
- [ ] 归因分解逻辑正确
- [ ] 商品数量效应、价格效应分离

### 订单分析看板 ⏸️

- [ ] 订单级聚合（避免重复）
- [ ] 利润计算公式正确
- [ ] 成本结构分析完整

---

## 🎯 数据一致性验证方法

```python
def verify_data_consistency(df1, df2):
    """验证两个看板的数据一致性"""
    
    # 验证1: 总销售额
    sales1 = df1['商品实售价'].sum()
    sales2 = df2['商品实售价'].sum()
    assert abs(sales1 - sales2) < 0.01, f"销售额不一致: {sales1} vs {sales2}"
    
    # 验证2: 总利润
    profit1 = df1['订单实际利润'].sum()
    profit2 = df2['订单实际利润'].sum()
    assert abs(profit1 - profit2) < 0.01, f"利润不一致: {profit1} vs {profit2}"
    
    # 验证3: 订单数
    orders1 = df1['订单ID'].nunique()
    orders2 = df2['订单ID'].nunique()
    assert orders1 == orders2, f"订单数不一致: {orders1} vs {orders2}"
    
    print("✅ 数据一致性验证通过")
```

---

## 📚 参考文档

1. **业务逻辑最终确认.md** - 业务规则定义
2. **统一计算标准.md** - Streamlit版本标准（已废弃，以本文档为准）
3. **数据处理逻辑一致性报告.md** - 历史问题记录

---

## 🔄 版本历史

### v2.0 (2025-10-24) - Dash版本统一标准
- ✅ 基于Dash版本重新梳理
- ✅ 明确5层计算架构
- ✅ 添加错误示例和避免方法
- ✅ 完善诊断引擎使用规范

### v1.0 (2025-10-18) - Streamlit版本标准
- 初始版本（已废弃）

---

**维护人**: GitHub Copilot  
**审核状态**: ✅ 已确认  
**下次更新**: 根据实际开发情况调整

---

## 🚀 快速开始模板

```python
# ===== Dash看板标准开发模板 =====

# Step 1: 导入标准模块
from 真实数据处理器 import RealDataProcessor
from 问题诊断引擎 import ProblemDiagnosticEngine
from scene_inference import add_scene_and_timeslot_fields

# Step 2: 数据加载与标准化
def load_data(df_raw):
    # 2.1 字段映射
    processor = RealDataProcessor()
    df_std = processor.standardize_sales_data(df_raw)
    
    # 2.2 业务规则过滤
    df_clean = apply_business_rules(df_std)
    
    # 2.3 场景时段推断
    df_final = add_scene_and_timeslot_fields(df_clean)
    
    return df_final

# Step 3: 初始化诊断引擎
GLOBAL_DATA = load_data(df_raw)
DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)

# Step 4: 使用诊断功能
result = DIAGNOSTIC_ENGINE.diagnose_sales_decline(
    current_period_idx=0,
    compare_period_idx=1,
    time_period='week',
    threshold=-100
)

# Step 5: 数据验证
verify_data_consistency(result, expected_result)
```

---

**本文档是所有Dash看板的数据计算基准，任何修改需同步更新！**

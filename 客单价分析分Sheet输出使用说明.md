# 客单价分析分Sheet输出功能说明

## 📋 功能概述

新增方法 `diagnose_customer_price_decline_by_sheets()` 可以将客单价分析结果按三个维度分别输出到不同的Sheet:

1. **客单价变化** - 客单价汇总信息
2. **下滑商品分析** - 只包含问题商品的TOP5
3. **上涨商品分析** - 只包含表现优秀商品的TOP5

---

## 🔧 使用方法

### 1. 导入和初始化

```python
from 问题诊断引擎 import ProblemDiagnosticEngine

# 初始化引擎
engine = ProblemDiagnosticEngine(df)
```

### 2. 调用分Sheet方法

```python
# 获取分Sheet的数据字典
sheets_data = engine.diagnose_customer_price_decline_by_sheets(
    time_period='day',    # 'day' 或 'week'
    threshold=-5.0        # 客单价下滑阈值（百分比）
)

# 返回值是一个字典
# {
#     '客单价变化': DataFrame,
#     '下滑商品分析': DataFrame,
#     '上涨商品分析': DataFrame
# }
```

### 3. 保存到Excel

```python
import pandas as pd

output_file = '客单价分析结果.xlsx'

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, df_sheet in sheets_data.items():
        if len(df_sheet) > 0:
            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✓ 写入sheet: {sheet_name}")
```

---

## 📊 数据结构说明

### Sheet 1: 客单价变化

包含客单价汇总信息：

| 字段名 | 说明 |
|--------|------|
| 对比周期 | 对比的时间范围 |
| 之前客单价 | 对比期的客单价 |
| 当前客单价 | 当前期的客单价 |
| 客单价变化 | 变化金额 |
| 变化幅度% | 变化百分比 |
| 商品角色分布 | 商品角色统计 |
| 问题等级 | 严重程度 |
| 建议操作 | 建议措施 |

### Sheet 2: 下滑商品分析

包含TOP5下滑商品的详细信息（每个商品7个字段）：

```
TOP1下滑商品-商品名称
TOP1下滑商品-分类
TOP1下滑商品-当前单价
TOP1下滑商品-之前单价
TOP1下滑商品-单价变化
TOP1下滑商品-销量变化
TOP1下滑商品-问题原因  ← 只包含问题原因

TOP2下滑商品-商品名称
TOP2下滑商品-分类
...
```

**问题原因包括**:
- 🔴售罄
- 💰涨价导致销量降
- 💸降价仍降量
- 📉销量大幅下滑
- 📦库存不足
- ⚠️滞销预警

### Sheet 3: 上涨商品分析

包含TOP5上涨商品的详细信息（每个商品7个字段）：

```
TOP1上涨商品-商品名称
TOP1上涨商品-分类
TOP1上涨商品-当前单价
TOP1上涨商品-之前单价
TOP1上涨商品-单价变化
TOP1上涨商品-销量变化
TOP1上涨商品-增长原因  ← 只包含优势原因

TOP2上涨商品-商品名称
TOP2上涨商品-分类
...
```

**增长原因包括**:
- 💰涨价(销量增)
- 💸降价促销成功
- 📈销量增长

---

## 💡 应用场景

### 场景1: 单独分析下滑商品

```python
# 获取分Sheet数据
sheets_data = engine.diagnose_customer_price_decline_by_sheets(
    time_period='day',
    threshold=-5.0
)

# 只使用下滑商品数据
declining_df = sheets_data['下滑商品分析']

if len(declining_df) > 0:
    print("需要关注的问题商品:")
    print(declining_df)
```

### 场景2: 对比下滑和上涨商品

```python
sheets_data = engine.diagnose_customer_price_decline_by_sheets()

declining_df = sheets_data['下滑商品分析']
rising_df = sheets_data['上涨商品分析']

print(f"下滑商品数量: {len(declining_df)}")
print(f"上涨商品数量: {len(rising_df)}")
```

### 场景3: 生成完整报告

```python
# 获取所有数据
sheets_data = engine.diagnose_customer_price_decline_by_sheets(
    time_period='week',
    threshold=-10.0
)

# 保存到Excel（自动分Sheet）
with pd.ExcelWriter('客单价分析报告.xlsx', engine='openpyxl') as writer:
    sheets_data['客单价变化'].to_excel(writer, sheet_name='客单价变化', index=False)
    sheets_data['下滑商品分析'].to_excel(writer, sheet_name='下滑商品分析', index=False)
    sheets_data['上涨商品分析'].to_excel(writer, sheet_name='上涨商品分析', index=False)
```

---

## 🔄 与原方法的对比

### 原方法: `diagnose_customer_price_decline()`

返回单个DataFrame，所有字段混合在一起：

```python
result = engine.diagnose_customer_price_decline()
# 返回: DataFrame包含所有字段（70+ 列）
```

### 新方法: `diagnose_customer_price_decline_by_sheets()`

返回字典，数据按维度分离：

```python
sheets_data = engine.diagnose_customer_price_decline_by_sheets()
# 返回: {
#     '客单价变化': DataFrame (8列),
#     '下滑商品分析': DataFrame (35列),
#     '上涨商品分析': DataFrame (35列)
# }
```

---

## 📝 完整示例

```python
from 问题诊断引擎 import ProblemDiagnosticEngine
import pandas as pd

# 1. 初始化
df = pd.read_excel('订单数据.xlsx')
engine = ProblemDiagnosticEngine(df)

# 2. 获取分Sheet数据
sheets_data = engine.diagnose_customer_price_decline_by_sheets(
    time_period='week',  # 按周分析
    threshold=-5.0       # 客单价下滑5%以上
)

# 3. 分析每个维度
print("\n=== 客单价变化 ===")
price_df = sheets_data['客单价变化']
if len(price_df) > 0:
    for _, row in price_df.iterrows():
        print(f"周期: {row['对比周期']}")
        print(f"客单价: {row['之前客单价']} → {row['当前客单价']}")
        print(f"变化: {row['客单价变化']} ({row['变化幅度%']})")

print("\n=== 下滑商品 ===")
declining_df = sheets_data['下滑商品分析']
if len(declining_df) > 0:
    for i in range(1, 6):
        name_col = f'TOP{i}下滑商品-商品名称'
        reason_col = f'TOP{i}下滑商品-问题原因'
        if name_col in declining_df.columns:
            name = declining_df[name_col].iloc[0]
            reason = declining_df[reason_col].iloc[0]
            if name:
                print(f"TOP{i}: {name} - {reason}")

print("\n=== 上涨商品 ===")
rising_df = sheets_data['上涨商品分析']
if len(rising_df) > 0:
    for i in range(1, 6):
        name_col = f'TOP{i}上涨商品-商品名称'
        reason_col = f'TOP{i}上涨商品-增长原因'
        if name_col in rising_df.columns:
            name = rising_df[name_col].iloc[0]
            reason = rising_df[reason_col].iloc[0]
            if name:
                print(f"TOP{i}: {name} - {reason}")

# 4. 保存到Excel
output_file = '客单价分析结果.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    for sheet_name, df_sheet in sheets_data.items():
        if len(df_sheet) > 0:
            df_sheet.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"\n✅ 分析完成！结果已保存到: {output_file}")
```

---

## ✅ 优势

1. **信息清晰**: 三个维度分离，便于快速定位
2. **决策高效**: 问题商品和优势商品分开展示
3. **格式友好**: 直接保存为多Sheet Excel，便于分享
4. **灵活使用**: 可以只使用需要的Sheet

---

## 📚 参考文档

- [展示逻辑重构完成报告.md](./展示逻辑重构完成报告.md) - 重构详情
- [判定类型快速参考.md](./判定类型快速参考.md) - 原因分类说明

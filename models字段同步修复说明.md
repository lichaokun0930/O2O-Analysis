# models.py字段同步修复说明

## 问题描述

B电脑克隆后发现一级分类销售趋势中的**滞销品统计**和**库存周转统计**没有数据。

## 根本原因

### 1. models.py与数据库字段不匹配

**数据库实际字段 (44个):**
```
stock, remaining_stock, delivery_distance, store_id, city (等44个字段)
```

**models.py原始定义 (40个):**
缺少以下4个字段:
- `stock` - 库存
- `delivery_distance` - 配送距离  
- `store_id` - 门店ID
- `city` - 城市

### 2. 数据源字段名不一致

**智能门店看板_Dash版.py 代码检查:**
```python
required_fields = {
    '库存': False,  # ❌ 检查中文字段名
    '月售': False
}

# 兼容性检查
elif field == '库存' and '剩余库存' in df.columns:
    required_fields[field] = True
```

**实际数据库字段名:**
```python
stock          # 英文字段名
remaining_stock # 英文字段名
```

**结果**: 字段检查失败 → `required_fields['库存'] = False` → 跳过滞销品和库存周转计算

## 修复方案

### ✅ 修复1: 同步models.py字段定义

**修改文件**: `database/models.py`

**添加字段**:
```python
class Order(Base):
    # 销量和金额
    quantity = Column(Integer, default=1, comment='销量')
    stock = Column(Integer, default=0, comment='库存')  # ✅ 新增
    remaining_stock = Column(Float, default=0, comment='剩余库存')
    
    # 配送信息
    delivery_platform = Column(String(100), index=True, comment='配送平台')
    delivery_distance = Column(Float, default=0, comment='配送距离(公里)')  # ✅ 新增
    
    # 门店信息
    store_id = Column(String(100), index=True, comment='门店ID')  # ✅ 新增
    store_franchise_type = Column(Integer, index=True, comment='门店加盟类型')
    city = Column(String(100), index=True, comment='城市')  # ✅ 新增
```

**验证**:
```bash
# 字段数对比
数据库: 44个字段
models.py (修复前): 40个字段 ❌
models.py (修复后): 44个字段 ✅
```

### ⚠️ 待修复2: 数据源字段名检查逻辑

**问题位置**: `智能门店看板_Dash版.py` Line 9602-9620

**当前逻辑**:
```python
required_fields = {
    '一级分类名': False,
    '日期': False,
    '库存': False,  # ❌ 检查中文字段名
    '月售': False
}

# 只检查了 '剩余库存',没有检查 'stock'
elif field == '库存' and '剩余库存' in df.columns:
    required_fields[field] = True
```

**建议修复**:
```python
# 方案1: 增强字段名兼容性
elif field == '库存' and ('剩余库存' in df.columns or 'stock' in df.columns or 'remaining_stock' in df.columns):
    required_fields[field] = True

# 方案2: 统一使用英文字段名
# 在数据标准化阶段将 stock → 库存
```

## 影响范围

### 受影响功能
1. ✅ **一级分类销售趋势** - 滞销品统计
2. ✅ **一级分类销售趋势** - 库存周转天数
3. ⚠️ **售罄品统计** - 依赖库存字段

### 不受影响功能
- 销售额统计 ✅
- 利润率计算 ✅  
- 销售量统计 ✅

## 测试验证

### 步骤1: 验证models.py字段
```python
from database.models import Order
from sqlalchemy import inspect

inspector = inspect(Order)
fields = [col.name for col in inspector.columns]

assert 'stock' in fields
assert 'remaining_stock' in fields
assert 'delivery_distance' in fields
assert 'store_id' in fields
assert 'city' in fields
```

### 步骤2: 重启看板验证数据
```powershell
.\启动看板.ps1
```

**预期结果**:
- 一级分类销售趋势表格中:
  - "售罄品"列显示数量 (如: ⚠️ 237个)
  - "滞销品统计"列显示分级 (如: 🟡轻度157 🟠中度80)
  - "库存周转"列显示天数 (如: 15.3天)

## 数据流程图

```
数据库 (stock, remaining_stock)
    ↓
models.py (Order.stock, Order.remaining_stock) ← ✅ 已修复
    ↓
DataSourceManager 查询
    ↓
智能门店看板_Dash版.py
    ↓
required_fields['库存'] 检查 ← ⚠️ 待修复 (字段名不匹配)
    ↓
滞销品/库存周转计算
```

## 相关文件

- ✅ `database/models.py` - 已修复
- ⚠️ `智能门店看板_Dash版.py` (Line 9602-9900) - 待修复
- ✅ `migrations/add_remaining_stock.sql` - 字段迁移脚本
- 📝 `【权威】业务逻辑与数据字典完整手册.md` - 字段定义文档

## 总结

**核心问题**: B电脑迭代了数据库字段,但A电脑的 `models.py` 没有同步更新

**修复状态**:
- ✅ models.py字段已同步 (44个字段完整)
- ⚠️ 代码字段名检查逻辑需要增强兼容性

**后续建议**:
1. 统一字段命名规范 (中文 vs 英文)
2. 添加字段映射配置文件
3. 数据导入时自动字段名标准化

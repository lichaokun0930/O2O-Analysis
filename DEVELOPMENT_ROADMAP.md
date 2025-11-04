# 🎯 智能门店看板 - 开发路线图

> **核心战略：数据库优先架构 (Database-First Architecture)**
> 
> ⚠️ **关键烙印：所有看板开发和优化必须结合数据库实现**

---

## 📌 核心原则

### 🔥 **烙印规则（CRITICAL）**
```
任何涉及以下内容的开发，必须使用数据库：
✓ 数据存储和读取
✓ 历史数据查询
✓ 多门店数据汇总
✓ 数据分析和统计
✓ 缓存和性能优化
✓ 数据上传和导入
```

---

## 🚀 高优行动项（按优先级）

### ⭐ **阶段1：数据库基础能力** [方案2]
**目标：建立稳定的数据持久化能力**

#### 🔴 P0 - 立即执行
- [ ] **修复订单导入重复ID问题**
  - 问题：order_id 重复导致导入失败
  - 方案：实现 UPSERT 逻辑（INSERT ... ON CONFLICT UPDATE）
  - 文件：`database/migrate_orders.py`（新建）
  - 预期：能成功导入所有订单数据

- [ ] **批量数据导入工具**
  - 功能：导入所有历史Excel文件到数据库
  - 支持：自动去重、增量更新
  - 文件：`database/batch_import.py`（新建）
  - 预期：一键导入所有门店历史数据

#### 🟠 P1 - 本周完成
- [ ] **数据库数据验证**
  - 验证导入数据完整性
  - 对比Excel和数据库数据一致性
  - 生成数据质量报告

- [ ] **数据备份和恢复机制**
  - 定期自动备份数据库
  - 提供一键恢复功能

---

### ⭐ **阶段2：前后端集成** [方案3]
**目标：看板直接使用数据库数据**

#### 🟡 P2 - 两周内完成
- [ ] **看板数据源切换功能**
  - 新增：数据源选择器（Excel / 数据库）
  - 位置：看板顶部工具栏
  - 文件：`智能门店看板_Dash版.py`
  - 逻辑：
    ```python
    # 伪代码
    if data_source == "数据库":
        df = load_from_database(filters)
    else:
        df = load_from_excel()
    ```

- [ ] **数据库数据加载器**
  - 文件：`database/data_loader.py`（新建）
  - 功能：
    - 按门店ID筛选
    - 按日期范围筛选
    - 按商品分类筛选
    - 支持分页加载（性能优化）

#### 🟢 P3 - 一个月内完成
- [ ] **前端调用后端API**
  - 不直接连接数据库，而是调用 FastAPI 接口
  - 示例：
    ```python
    # 前端 Dash 回调
    import requests
    response = requests.get("http://localhost:8000/api/orders", 
                           params={"store_id": "xxx", "start_date": "2025-09-01"})
    df = pd.DataFrame(response.json())
    ```

- [ ] **实时数据刷新**
  - WebSocket 推送新数据
  - 看板自动刷新图表

---

### ⭐ **阶段3：高级功能** [扩展]
**目标：充分发挥数据库优势**

#### 🔵 P4 - 长期规划
- [ ] **多门店数据对比**
  - 横向对比不同门店
  - 数据库聚合查询

- [ ] **历史趋势分析**
  - 跨月、跨季度分析
  - 同比、环比计算

- [ ] **智能缓存策略**
  - 使用 AnalysisCache 表
  - 避免重复计算

- [ ] **数据上传界面优化**
  - 拖拽上传Excel
  - 实时显示导入进度
  - 自动校验数据格式

---

## 📐 技术架构图

```
┌─────────────────────────────────────────────────────────┐
│                    智能门店看板系统                      │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                   ┌─────────▼────────┐
│  前端 (Dash)    │◄─────HTTP────────┤  后端 (FastAPI)  │
│  Port: 8050    │      REST API     │  Port: 8000      │
└────────────────┘                   └──────────────────┘
        │                                       │
        │ 临时方案：                             │ 推荐方案：
        │ 直接读Excel                            │ 调用API
        │                                       │
        └───────────────────┬───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  PostgreSQL DB │
                    │  Port: 5432    │
                    └────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    ┌───▼────┐      ┌───────▼─────┐      ┌─────▼──────┐
    │ orders │      │  products   │      │ scene_tags │
    │ 表      │      │  表          │      │  表         │
    └────────┘      └─────────────┘      └────────────┘
```

---

## 🔧 开发规范

### **数据库优先设计原则**

#### ✅ **正确做法（推荐）**
```python
# ✅ 方式1：通过API获取数据
import requests
df = pd.DataFrame(
    requests.get("http://localhost:8000/api/orders").json()
)

# ✅ 方式2：直接查询数据库
from database.connection import get_db
from database.models import Order

with get_db() as db:
    orders = db.query(Order).filter(Order.date >= '2025-09-01').all()
    df = pd.DataFrame([o.to_dict() for o in orders])
```

#### ❌ **错误做法（禁止）**
```python
# ❌ 不要：硬编码读取单个Excel
df = pd.read_excel("实际数据/订单.xlsx")

# ❌ 不要：分散的临时文件存储
df.to_csv("临时数据.csv")
```

---

## 📊 当前进度追踪

### ✅ 已完成
- [x] PostgreSQL 数据库创建 (o2o_dashboard)
- [x] 数据库表结构设计 (6张表)
- [x] FastAPI 后端搭建
- [x] 商品数据导入 (3,974条)
- [x] 前端 Dash 看板开发
- [x] 后端 API 健康检查

### 🔄 进行中
- [ ] 订单数据导入（受阻于重复ID问题）

### ⏳ 待开始
- [ ] 看板连接数据库
- [ ] 批量历史数据导入
- [ ] 前后端完全集成

---

## 🎓 代码示例模板

### 模板1：数据库数据加载器
```python
# database/data_loader.py

from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Order, Product
import pandas as pd
from datetime import datetime

class DatabaseDataLoader:
    """数据库数据加载器 - 为看板提供数据"""
    
    @staticmethod
    def load_orders(
        store_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        db: Session = None
    ) -> pd.DataFrame:
        """
        从数据库加载订单数据
        
        Args:
            store_id: 门店ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            db: 数据库会话（可选）
        
        Returns:
            订单数据 DataFrame
        """
        should_close = False
        if db is None:
            db = next(get_db())
            should_close = True
        
        try:
            query = db.query(Order)
            
            if store_id:
                query = query.filter(Order.store_id == store_id)
            if start_date:
                query = query.filter(Order.date >= start_date)
            if end_date:
                query = query.filter(Order.date <= end_date)
            
            orders = query.all()
            
            # 转换为 DataFrame
            data = [{
                '订单ID': o.order_id,
                '日期': o.date,
                '门店ID': o.store_id,
                '商品名称': o.product_name,
                '商品实售价': o.sale_price,
                '销售数量': o.quantity,
                # ... 其他字段
            } for o in orders]
            
            return pd.DataFrame(data)
        
        finally:
            if should_close:
                db.close()
    
    @staticmethod
    def load_products(category: str = None) -> pd.DataFrame:
        """加载商品数据"""
        # 实现逻辑...
        pass
```

### 模板2：看板数据源切换
```python
# 在智能门店看板_Dash版.py中添加

def load_data_unified(source: str = "database", **filters):
    """
    统一数据加载接口
    
    Args:
        source: "database" 或 "excel"
        **filters: 筛选条件
    
    Returns:
        DataFrame
    """
    if source == "database":
        from database.data_loader import DatabaseDataLoader
        loader = DatabaseDataLoader()
        return loader.load_orders(**filters)
    else:
        # 原有的Excel加载逻辑
        return load_real_business_data()
```

---

## 📝 开发检查清单

每次开发新功能前，必须检查：

- [ ] 是否需要存储数据？→ 使用数据库
- [ ] 是否需要历史数据？→ 使用数据库
- [ ] 是否需要跨文件汇总？→ 使用数据库
- [ ] 是否需要复杂查询？→ 使用数据库
- [ ] 数据是否会重复使用？→ 使用数据库
- [ ] 是否需要多用户访问？→ 使用数据库

**只有临时、单次性的数据分析才允许直接读取Excel！**

---

## 🚨 重要提醒

```
┌────────────────────────────────────────────────────┐
│  ⚠️  所有看板功能开发，必须考虑数据库集成！        │
│                                                    │
│  在编码前，先问自己三个问题：                        │
│  1. 这个功能能从数据库获取数据吗？                   │
│  2. 如果能，为什么不用数据库？                       │
│  3. 如果用Excel，是否只是临时方案？                 │
│                                                    │
│  数据库 = 未来的基石                                │
│  Excel  = 临时的拐杖                                │
└────────────────────────────────────────────────────┘
```

---

## 📅 更新日志

### 2025-11-04
- ✅ 创建开发路线图
- ✅ 确立"数据库优先"核心原则
- ✅ 定义方案2+方案3实施路径
- 🎯 设置高优行动项优先级

---

**下一步行动：立即修复订单导入问题，解锁数据库完整能力！**

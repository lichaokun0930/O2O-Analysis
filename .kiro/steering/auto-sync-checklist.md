---
inclusion: always
---

# AI 开发自动同步检查清单

本文档定义了开发过程中需要自动同步的规则。AI 在完成任何功能开发时，必须自动检查并完成相关的同步操作。

---

## 一、后端开发同步规则

### 1. 新增 API 端点

**触发条件**：在 `backend/app/api/v1/` 下新增 API 文件或端点

**AI 自动操作**：

```python
# 步骤1：创建 API 文件（如 backend/app/api/v1/new_feature.py）
from fastapi import APIRouter, Query
router = APIRouter()

@router.get("/endpoint")
async def get_data(store_name: Optional[str] = Query(None)):
    # 必须接受 store_name 参数
    pass

# 步骤2：在 backend/app/api/v1/__init__.py 注册路由
from .new_feature import router as new_feature_router
router.include_router(new_feature_router, prefix="/new-feature", tags=["新功能"])

# 步骤3：如果需要前端调用，在 frontend-react/src/api/orders.ts 添加方法
```

**同步文件清单**：
| 文件 | 操作 |
|------|------|
| `backend/app/api/v1/new_feature.py` | 创建 API 文件 |
| `backend/app/api/v1/__init__.py` | 注册路由 |
| `frontend-react/src/api/orders.ts` | 添加 API 调用方法 |
| `frontend-react/src/types/index.ts` | 添加类型定义（如需要） |

### 2. 新增数据库字段

**触发条件**：需要在订单表中新增字段

**AI 自动操作**：

```python
# 步骤1：在 database/models.py 的 Order 类中添加字段
class Order(Base):
    # ... 现有字段
    new_field = Column(Float, default=0, comment='新字段说明')

# 步骤2：在 database/batch_import_enhanced.py 添加字段映射
order = Order(
    # ... 现有映射
    new_field=safe_float(row.get('Excel列名', 0)),
)

# 步骤3：生成数据库迁移 SQL
ALTER TABLE orders ADD COLUMN new_field DECIMAL(12,2) DEFAULT 0;

# 步骤4：如果字段需要聚合，更新 aggregation_config.py
```

**同步文件清单**：
| 文件 | 操作 |
|------|------|
| `database/models.py` | 添加字段定义 |
| `database/batch_import_enhanced.py` | 添加字段映射 |
| `migrations/` | 生成迁移 SQL |
| `backend/app/services/aggregation_config.py` | 如需聚合则添加 |

### 3. 新增预聚合表

**触发条件**：需要新的数据聚合维度

**AI 自动操作**：

```python
# 步骤1：在 aggregation_config.py 添加配置
AGGREGATION_CONFIGS["new_summary"] = AggregationConfig(
    table_name="new_summary",
    description="新汇总表",
    group_by=["store_name", "DATE(date) as summary_date"],
    fields=[
        AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
        AggregationField("total_revenue", "actual_price * quantity", "SUM"),
    ],
    derived_fields=[
        DerivedField("avg_value", "CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END"),
    ],
)

# 步骤2：运行 python database/generate_table_sql.py new_summary 生成建表 SQL
# 步骤3：执行建表 SQL
```

**同步文件清单**：
| 文件 | 操作 |
|------|------|
| `backend/app/services/aggregation_config.py` | 添加表配置 |
| `database/generate_table_sql.py` | 运行生成 SQL |
| 数据库 | 执行建表 SQL |

### 4. 新增后端服务

**触发条件**：在 `backend/app/services/` 下新增服务

**AI 自动操作**：

```python
# 步骤1：创建服务文件 backend/app/services/new_service.py
class NewService:
    pass
new_service = NewService()

# 步骤2：如果需要在启动时初始化，在 backend/app/main.py 的 startup_event 中添加
@app.on_event("startup")
async def startup_event():
    # ... 现有初始化
    try:
        from .services.new_service import new_service
        new_service.initialize()
    except Exception as e:
        logging_service.warning(f"新服务初始化失败: {e}")
```

---

## 二、前端开发同步规则

### 5. 新增前端页面/TAB

**触发条件**：新增页面或 TAB 组件

**AI 自动操作**：

```typescript
// 步骤1：创建组件文件 frontend-react/src/views/NewPage.tsx
import { useGlobalContext } from '@/store/GlobalContext';

const NewPage: React.FC = () => {
  const { selectedStore, dateRange, selectedChannel } = useGlobalContext();
  // 使用全局状态，不要独立请求
};

// 步骤2：在 App.tsx 中添加路由（如果是独立页面）
const NewPage = React.lazy(() => import('./views/NewPage'));
<Route path="/new-page" element={<NewPage />} />

// 步骤3：如果需要新的全局状态，在 GlobalContext.tsx 中添加
```

**同步文件清单**：
| 文件 | 操作 |
|------|------|
| `frontend-react/src/views/NewPage.tsx` | 创建页面组件 |
| `frontend-react/src/App.tsx` | 添加路由/懒加载 |
| `frontend-react/src/store/GlobalContext.tsx` | 添加全局状态（如需要） |
| `frontend-react/src/api/orders.ts` | 添加 API 方法（如需要） |
| `frontend-react/src/types/index.ts` | 添加类型定义（如需要） |

### 6. 新增前端图表组件

**触发条件**：新增图表组件

**AI 自动操作**：

```typescript
// 步骤1：创建图表组件 frontend-react/src/components/charts/NewChart.tsx
interface NewChartProps {
  storeName?: string;
  channel?: string;
  selectedDate?: string | null;
  selectedDateRange?: { start: string; end: string };
  theme: 'dark' | 'light';
}

// 步骤2：在 App.tsx 中懒加载
const NewChart = React.lazy(() => import('./components/charts/NewChart'));

// 步骤3：在需要的位置使用
<Suspense fallback={<ChartLoading />}>
  <NewChart storeName={selectedStore} theme={theme} />
</Suspense>
```

### 7. 新增全局状态

**触发条件**：需要跨组件共享的状态

**AI 自动操作**：

```typescript
// 在 frontend-react/src/store/GlobalContext.tsx 中：

// 步骤1：在 GlobalContextType 接口添加类型
interface GlobalContextType {
  // ... 现有字段
  newState: NewStateType;
  setNewState: (state: NewStateType) => void;
}

// 步骤2：在 GlobalProvider 中添加状态
const [newState, setNewState] = useState<NewStateType>(initialValue);

// 步骤3：在 value 中导出
const value = { ...existing, newState, setNewState };
```

---

## 三、数据流同步规则

### 8. 数据变更后的自动同步链

**触发条件**：数据上传/删除/批量导入

**系统自动执行**（无需 AI 干预）：
```
数据变更 → schema_validator.validate_and_fix_all()  # 先验证表结构
         → aggregation_sync_service.sync_store_data()
         → 删除旧预聚合数据
         → 重建所有预聚合表（失败时抛出异常）
         → check_aggregation_tables(force=True)
         → _clear_all_caches() [FLUSHDB]
         → query_router_service.initialize()
```

### 8.1 预聚合表结构自动验证

**触发条件**：后端启动、数据导入前

**自动执行**：
- `schema_validator.py` 检查所有预聚合表字段是否完整
- 发现缺失字段自动添加（ALTER TABLE ADD COLUMN）
- 验证失败时记录日志并警告

**防护机制**：
- 后端启动时自动验证（`main.py` startup_event）
- 批量导入前自动验证（`batch_import_enhanced.py` __init__）
- 同步服务执行前自动验证（`aggregation_sync_service.py`）
- 同步失败时抛出异常而不是静默继续

### 8.2 预聚合表一致性自动检查与修复

**触发条件**：后端启动、数据导入完成后

**自动执行**（`aggregation_consistency_service.py`）：
- 检查订单表和预聚合表的门店是否一致
- 发现缺失门店自动同步预聚合数据
- 发现孤立门店（预聚合表有但订单表没有）自动清理
- 发现数据量不匹配（差异>5%）自动重建

**触发点**：
- 后端启动时：`main.py` startup_event 调用 `check_and_repair_on_startup()`
- 数据导入后：`batch_import_enhanced.py` 调用 `_run_consistency_check()`

**检查内容**：
| 检查项 | 说明 |
|--------|------|
| missing_stores | 订单表有但预聚合表没有的门店 |
| orphan_stores | 预聚合表有但订单表没有的门店 |
| mismatched_stores | 数据量差异超过5%的门店 |

**修复策略**：
- 缺失门店：调用 `AggregationEngine.sync_all_tables()` 同步
- 孤立门店：从5个预聚合表中删除相关数据
- 数据不匹配：重新同步该门店的预聚合数据

### 9. 删除数据时清理导入历史（已自动化）

**触发条件**：用户删除订单数据后想重新导入同一个文件

**已实现的自动化**：
- 批量导入工具在检查文件是否已导入时，会同时检查数据库是否为空
- 如果数据库为空但存在导入历史记录，会自动清理历史记录
- 用户无需手动运行清理脚本

**自动化逻辑**（`batch_import_enhanced.py` 的 `check_file_imported` 方法）：
```python
if existing_history and order_count == 0:
    # 数据库为空但有导入历史，自动清理
    session.query(DataUploadHistory).delete()
    return False  # 允许重新导入
```

**手动清理方式**（备用）：
```bash
# 运行清理脚本
python 清理导入历史记录.py --force

# 或通过 API
DELETE /api/v1/data/upload-history
```

### 10. 新增缓存键

**触发条件**：API 使用新的 Redis 缓存键

**无需手动操作**：系统使用 `FLUSHDB` 清除所有缓存，新增缓存键自动生效。

---

## 四、快速参考：AI 开发决策树

```
开发新功能
    │
    ├─ 后端 API？
    │   ├─ 创建 API 文件
    │   ├─ 注册路由 (__init__.py)
    │   └─ 前端 API 方法 (orders.ts)
    │
    ├─ 数据库字段？
    │   ├─ models.py 添加字段
    │   ├─ batch_import_enhanced.py 添加映射
    │   ├─ 生成迁移 SQL
    │   └─ aggregation_config.py（如需聚合）
    │
    ├─ 预聚合表？
    │   ├─ aggregation_config.py 添加配置
    │   └─ 执行建表 SQL
    │
    ├─ 前端页面？
    │   ├─ 创建组件文件
    │   ├─ App.tsx 添加路由
    │   └─ GlobalContext.tsx（如需全局状态）
    │
    ├─ 前端图表？
    │   ├─ 创建图表组件
    │   ├─ App.tsx 懒加载
    │   └─ 使用 useGlobalContext
    │
    └─ 其他 → 按正常开发流程
```

---

## 五、文件同步速查表

| 开发场景 | 需要同步的文件 |
|---------|---------------|
| 新增 API | `api/v1/xxx.py` + `api/v1/__init__.py` + `orders.ts` |
| 新增数据库字段 | `models.py` + `batch_import_enhanced.py` + 迁移SQL |
| 新增预聚合表 | `aggregation_config.py` + 建表SQL |
| 新增前端页面 | `views/xxx.tsx` + `App.tsx` |
| 新增前端图表 | `components/charts/xxx.tsx` + `App.tsx` |
| 新增全局状态 | `GlobalContext.tsx` |
| 新增类型定义 | `types/index.ts` (前端) 或 类型注解 (后端) |

---

## 六、示例：AI 自动完成完整功能开发

### 示例1：新增"按周统计"功能

用户需求："我需要按周统计订单数据"

**AI 自动执行**：

1. **判断**：需要新的聚合维度（周）+ 新 API + 前端展示

2. **后端：添加预聚合表配置**
```python
# aggregation_config.py
AGGREGATION_CONFIGS["store_weekly_summary"] = AggregationConfig(
    table_name="store_weekly_summary",
    description="门店周汇总",
    group_by=["store_name", "DATE_TRUNC('week', date)::DATE as week_start", "channel"],
    fields=[
        AggregationField("order_count", "order_id", "COUNT_DISTINCT"),
        AggregationField("total_revenue", "actual_price * quantity", "SUM"),
        AggregationField("total_profit", "profit", "SUM"),
    ],
    derived_fields=[
        DerivedField("avg_order_value", "CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END"),
    ],
)
```

3. **后端：生成并执行建表 SQL**
```sql
CREATE TABLE IF NOT EXISTS store_weekly_summary (
    id SERIAL PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    week_start DATE,
    channel VARCHAR(50),
    order_count INTEGER DEFAULT 0,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_profit DECIMAL(12,2) DEFAULT 0,
    avg_order_value DECIMAL(12,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_store_weekly_store ON store_weekly_summary(store_name);
CREATE INDEX idx_store_weekly_week ON store_weekly_summary(week_start);
```

4. **后端：创建 API 端点**
```python
# backend/app/api/v1/orders.py 添加
@router.get("/weekly-trend")
async def get_weekly_trend(store_name: Optional[str] = Query(None)):
    # 从 store_weekly_summary 查询
    pass
```

5. **前端：添加 API 方法**
```typescript
// frontend-react/src/api/orders.ts
getWeeklyTrend(params?: { store_name?: string }): Promise<{ success: boolean; data: WeeklyTrendData }> {
  return request.get('/orders/weekly-trend', { params });
}
```

6. **前端：创建图表组件**
```typescript
// frontend-react/src/components/charts/WeeklyTrendChart.tsx
const WeeklyTrendChart: React.FC<Props> = ({ theme }) => {
  const { selectedStore } = useGlobalContext();
  // 使用 ordersApi.getWeeklyTrend
};
```

7. **前端：在 App.tsx 中使用**
```typescript
const WeeklyTrendChart = React.lazy(() => import('./components/charts/WeeklyTrendChart'));
// 在合适位置添加
<Suspense fallback={<ChartLoading />}>
  <WeeklyTrendChart theme={theme} />
</Suspense>
```

### 示例2：新增数据库字段"会员等级"

用户需求："Excel 中有会员等级字段，需要导入并展示"

**AI 自动执行**：

1. **数据库模型**
```python
# database/models.py
class Order(Base):
    # ... 现有字段
    member_level = Column(String(50), index=True, comment='会员等级')
```

2. **数据导入映射**
```python
# database/batch_import_enhanced.py
order = Order(
    # ... 现有映射
    member_level=safe_str(row.get('会员等级', '')),
)
```

3. **数据库迁移**
```sql
ALTER TABLE orders ADD COLUMN member_level VARCHAR(50);
CREATE INDEX idx_orders_member_level ON orders(member_level);
```

4. **如需聚合分析，添加预聚合表配置**
```python
# aggregation_config.py
AGGREGATION_CONFIGS["member_daily_summary"] = AggregationConfig(...)
```

---

## 七、自动化保障机制

### 已实现的自动化

| 机制 | 说明 |
|------|------|
| 预聚合表列表 | 从 `aggregation_config.py` 自动读取 |
| 缓存清除 | 使用 `FLUSHDB` 清除所有缓存 |
| 可用性检查 | 每60秒自动检查 + 同步后强制刷新 |
| 数据同步链 | 数据变更自动触发完整同步 |

### AI 开发时的保障

1. **steering 文件自动加载**：本文件设置为 `inclusion: always`，AI 每次开发都会参考
2. **配置驱动**：预聚合表、缓存等通过配置管理，减少代码修改
3. **同步文件清单**：每个场景都列出需要同步的文件，防止遗漏

---
inclusion: always
---

# O2O 订单数据看板 - 开发规范

本文档定义了项目的开发规范，所有新增功能必须遵循这些规范以确保性能和一致性。

## 1. 前端开发规范

### 1.1 全局状态使用

新增图表或页面时，**必须**从 `GlobalContext` 获取共享数据，**禁止**重复请求：

```typescript
// ✅ 正确：使用全局状态
import { useGlobalContext } from '@/store/GlobalContext';

const MyNewChart: React.FC = () => {
  const { 
    selectedStore,      // 当前选中门店
    channelList,        // 渠道列表（已缓存）
    selectedChannel,    // 当前选中渠道
    dateRange,          // 日期范围
    storeDateRange,     // 门店数据日期范围
    setSelectedChannel  // 设置渠道（全局联动）
  } = useGlobalContext();
  
  // 直接使用，无需再调用 API
};

// ❌ 错误：组件内独立请求渠道列表
const [channels, setChannels] = useState([]);
useEffect(() => {
  ordersApi.getChannels().then(res => setChannels(res.data));
}, []);
```

### 1.2 GlobalContext 可用状态

| 状态 | 类型 | 说明 |
|------|------|------|
| `selectedStore` | `string` | 当前选中门店名称 |
| `stores` | `Store[]` | 门店列表 |
| `channelList` | `string[]` | 当前门店的渠道列表 |
| `selectedChannel` | `string` | 当前选中渠道（'all' 表示全部） |
| `dateRange` | `DateRange` | 日期范围 {type, start, end} |
| `storeDateRange` | `StoreDateRange` | 门店数据的日期范围（用于日历限制） |
| `orderOverview` | `OrderOverview` | 订单概览数据（六大卡片） |
| `orderComparison` | `OrderComparison` | 环比数据 |
| `systemStatus` | `SystemStatus` | 系统连接状态 |

### 1.3 新增全局共享数据

如果需要新增全局共享的数据（如新的筛选条件），应添加到 `GlobalContext.tsx`：

```typescript
// 1. 在 GlobalContextType 接口中添加类型
interface GlobalContextType {
  // ... 现有字段
  newSharedData: SomeType;
  setNewSharedData: (data: SomeType) => void;
}

// 2. 在 GlobalProvider 中添加状态和方法
const [newSharedData, setNewSharedData] = useState<SomeType>(initialValue);

// 3. 在 value 中导出
const value = { ...existing, newSharedData, setNewSharedData };
```

### 1.4 API 调用规范

```typescript
// ✅ 正确：传入门店参数
const res = await ordersApi.getSomeData({ store_name: selectedStore });

// ❌ 错误：不传门店参数（会加载全部数据，无法利用缓存）
const res = await ordersApi.getSomeData();
```

---

## 2. 后端开发规范

### 2.1 数据加载

新增 API 时，**必须**传入 `store_name` 参数以利用缓存：

```python
# ✅ 正确：传入门店参数
@router.get("/your-new-api")
async def your_new_api(
    store_name: Optional[str] = Depends(common_store_param),
):
    df = get_order_data(store_name)  # 自动利用按门店缓存
    # ...

# ❌ 错误：不传参数（每次加载全部数据）
df = get_order_data()
```

### 2.2 缓存机制

项目使用两级缓存 + 智能版本控制：
1. **Redis 缓存**（优先）：24小时 TTL + 数据版本号校验
2. **内存缓存**（备用）：24小时 TTL + 数据版本号校验

缓存按门店分片存储，key 格式：`order_data:{store_name}`

**智能缓存失效机制**（2026-01-20 新增）：
- 缓存时记录数据版本号（基于 `updated_at` 时间戳）
- 请求时先检查版本号，版本匹配才使用缓存
- 数据有更新时版本号变化，缓存自动失效
- 无需等待 TTL 过期，也无需手动清缓存

**手动清缓存**：
```bash
# 清除指定门店缓存
POST /api/v1/orders/clear-cache?store_name=xxx

# 清除全部缓存
POST /api/v1/orders/clear-cache
```

### 2.3 常用依赖注入

```python
from dependencies import (
    get_order_data,           # 获取订单数据（带缓存）
    common_store_param,       # 门店参数
    common_date_range_params, # 日期范围参数
    common_pagination_params, # 分页参数
    get_diagnosis_service,    # 诊断服务
    get_product_service,      # 商品服务
    # ...
)
```

### 2.4 API 响应格式

```python
# 标准成功响应
return {"success": True, "data": result}

# 带分页的响应
return {
    "success": True,
    "data": items,
    "total": total_count,
    "page": page,
    "page_size": page_size
}

# 错误响应
raise HTTPException(status_code=400, detail="错误信息")
```

---

## 3. 文件结构规范

### 3.1 前端

```
frontend-react/src/
├── api/              # API 定义
│   └── orders.ts     # 订单相关 API
├── components/
│   └── charts/       # 图表组件
├── store/
│   └── GlobalContext.tsx  # 全局状态
├── views/            # 页面组件
└── types/            # 类型定义
```

### 3.2 后端

```
backend/app/
├── api/v1/           # API 路由
│   ├── orders.py     # 订单 API
│   └── diagnosis.py  # 诊断 API
├── services/         # 业务逻辑
├── database/         # 数据库模型
└── dependencies.py   # 依赖注入
```

---

## 4. 性能优化清单

新增功能时检查：

- [ ] 前端是否使用 GlobalContext 的共享数据
- [ ] 后端 API 是否传入 store_name 参数
- [ ] 大数据量接口是否支持分页
- [ ] 是否有不必要的重复请求
- [ ] 日期范围是否有合理限制

---

## 5. 渠道筛选联动

渠道筛选是全局联动的，影响以下图表：
- 销售趋势图 (DailyTrendChart)
- 分时段诊断 (CostEfficiencyChart)
- 分距离诊断 (DistanceAnalysisChart)
- 配送溢价雷达 (DeliveryHeatmap)

使用方式：
```typescript
const { selectedChannel, setSelectedChannel, channelList } = useGlobalContext();
```


---

## 6. 滞销品计算逻辑（2025-01-16 优化）

### 6.1 滞销天数计算规则

滞销天数以**商品首次出现日期**为观察起点，而非简单的"最后销售日期"：

```
数据范围：1日-30日

商品A：1日有销售 → 从1日开始计算无销售天数
商品B：5日首次出现 → 从5日开始计算无销售天数
```

**计算公式**：
- 如果 `最后销售日期 == 首次出现日期`（只卖过一次）：
  - `滞销天数 = 当前日期 - 首次出现日期`
- 否则（有多次销售）：
  - `滞销天数 = 当前日期 - 最后销售日期`

### 6.2 滞销分级标准

| 等级 | 条件 | 建议操作 |
|------|------|----------|
| 关注 (watch) | 3天 ≤ 无销售天数 < 7天 | 持续关注 |
| 轻度 (light) | 7天 ≤ 无销售天数 < 15天 | 关注观察 |
| 中度 (medium) | 15天 ≤ 无销售天数 < 30天 | 促销推荐 |
| 重度 (heavy) | 无销售天数 ≥ 30天 | 降价清仓 |

### 6.3 售罄品定义

售罄品 = 库存为0 且 近7天有销量

### 6.4 相关文件

- `backend/app/api/v1/inventory_risk.py` - 库存风险 API
- `backend/app/api/v1/category_matrix.py` - 品类效益矩阵 API
- `frontend-react/src/components/charts/CategoryAnalysisChart.tsx` - 前端展示组件


---

## 7. 营销成本计算逻辑（2026-01-19 更新 v3.2）

### 7.1 营销成本公式

营销成本（商家活动成本）包含**7个**营销相关字段（**不含配送费减免**）：

```python
营销成本 = 满减金额 + 商品减免金额 + 商家代金券 
         + 商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额
```

> ⚠️ **重要更新（v3.2）**：配送费减免金额属于**配送成本**，不属于营销成本。

### 7.2 字段说明

| 字段 | 级别 | 聚合方式 | 说明 |
|------|------|----------|------|
| 满减金额 | 订单级 | `.first()` | 满减活动金额 |
| 商品减免金额 | 订单级 | `.first()` | 商家自营销折扣 |
| 商家代金券 | 订单级 | `.first()` | 商家发放的优惠券 |
| 商家承担部分券 | 订单级 | `.first()` | 商家承担的优惠金额 |
| 满赠金额 | 订单级 | `.first()` | 满赠活动金额 |
| 商家其他优惠 | 订单级 | `.first()` | 其他商家优惠 |
| 新客减免金额 | 订单级 | `.first()` | 新客户优惠 |

### 7.3 GMV（营业额）计算公式（v3.2新增）

GMV是营销成本率计算的分母：

```python
GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)
```

**数据清洗规则（关键！）**：
1. **剔除商品原价 <= 0 的整行数据**（包括该行的打包袋金额和用户支付配送费）
2. 商品原价是商品级字段（单价），需要乘以销量
3. 打包袋金额是订单级字段，用`first`聚合避免重复
4. 用户支付配送费是订单级字段，处理方式同打包袋金额

> ⚠️ **关键说明**：商品原价=0的订单没有实际商品销售（如纯配送费订单），其打包袋金额和用户支付配送费也不应计入GMV。

**验证数据**（惠宜选超市昆山淀山湖镇店 2026-01-18）：
- 预期GMV: 8440.66
- 预期营销成本: 1122
- 预期营销成本率: ~13.30%

### 7.4 营销成本率计算

```python
营销成本率 = 营销成本 / GMV × 100%
```

> ⚠️ **重要更新（v3.2）**：分母从"商品实收额"改为"GMV（营业额）"。

### 7.5 与配送成本的关系

营销成本和配送成本是**两个独立的分析维度**：

- **营销成本** → 回答"我花了多少钱做促销活动？"（7字段）
- **配送成本** → 回答"我实际承担了多少配送费？"（含配送费减免）

配送费减免金额**只属于配送成本**，不计入营销成本。

### 7.6 单均营销费用

```python
单均营销费用 = 营销成本 / 订单数
```

### 7.7 相关文件

- `backend/app/api/v1/orders.py` - 订单 API（`calculate_gmv` 函数）
- `backend/app/api/v1/store_comparison.py` - 门店对比 API
- `智能门店看板_Dash版.py` - Dash 版本看板
- `【权威】业务逻辑与数据字典完整手册.md` - 业务逻辑手册


---

## 8. 预聚合表性能优化规范（2025-01-19 新增）

### 8.1 预聚合表概述

项目采用预聚合表架构实现企业级性能优化，将原始订单表的实时聚合查询转换为预计算结果查询，查询性能提升 99.8%（从 539ms 降至 1.1ms）。

### 8.2 预聚合表清单

| 表名 | 用途 | 记录数 | 适用场景 |
|------|------|--------|----------|
| `store_daily_summary` | 门店日汇总 | ~1,550 | 经营总览、日趋势图 |
| `store_hourly_summary` | 门店小时汇总 | ~22,197 | 分时段诊断、高峰分析 |
| `category_daily_summary` | 品类日汇总 | ~111,777 | 品类分析、效益矩阵 |
| `delivery_summary` | 配送分析汇总 | ~22,444 | 配送溢价、距离分析 |
| `product_daily_summary` | 商品日汇总 | ~249,620 | 商品排行、滞销分析 |

### 8.3 何时使用预聚合表

```python
# ✅ 优先使用预聚合表（推荐）
from services.aggregation_service import aggregation_service

# 获取门店经营总览
overview = aggregation_service.get_store_overview(
    store_name="惠宜选-泰州泰兴店",
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 7),
    channel="美团"
)

# 获取日趋势数据
trend = aggregation_service.get_daily_trend(store_name, start_date, end_date)

# 获取分时段分析
hourly = aggregation_service.get_hourly_analysis(store_name, start_date, end_date)

# 获取品类分析
category = aggregation_service.get_category_analysis(store_name, start_date, end_date, level=1)

# 获取配送分析
delivery = aggregation_service.get_delivery_analysis(store_name, start_date, end_date)

# 获取商品排行
products = aggregation_service.get_top_products(store_name, start_date, end_date, limit=20)
```

```python
# ❌ 避免直接查询原始订单表（性能差）
df = get_order_data(store_name)
result = df.groupby('日期').agg({...})  # 实时聚合，慢！
```

### 8.4 何时需要更新预聚合表

预聚合表需要在以下情况下重新生成：

1. **导入新数据**：新订单数据导入后
2. **新增聚合字段**：业务需要新的统计维度
3. **修改计算逻辑**：如营销成本公式变更

**更新方式**：运行优化脚本

```bash
cd 订单数据看板/订单数据看板/O2O-Analysis
python 全看板性能优化实施.py
```

### 8.5 新增看板时的优化流程

为新看板添加预聚合支持：

1. **分析聚合需求**：确定需要哪些维度（门店/日期/渠道/品类等）
2. **设计聚合表结构**：参考现有表结构设计新表
3. **添加建表SQL**：在 `全看板性能优化实施.py` 中添加
4. **添加数据填充逻辑**：编写聚合查询填充数据
5. **扩展 aggregation_service**：添加新的查询方法
6. **更新 API 使用聚合服务**：修改后端 API 调用聚合服务

### 8.6 聚合服务可用方法

`aggregation_service` 提供以下方法：

| 方法 | 返回类型 | 说明 |
|------|----------|------|
| `get_store_overview()` | `Dict` | 门店经营总览（六大指标） |
| `get_daily_trend()` | `List[Dict]` | 日趋势数据 |
| `get_hourly_analysis()` | `List[Dict]` | 分时段分析 |
| `get_category_analysis()` | `List[Dict]` | 品类分析 |
| `get_delivery_analysis()` | `Dict` | 配送分析（按距离/小时） |
| `get_top_products()` | `List[Dict]` | 商品销量排行 |

所有方法支持参数：`store_name`, `start_date`, `end_date`, `channel`

### 8.7 相关文件

| 文件 | 说明 |
|------|------|
| `全看板性能优化实施.py` | 预聚合表创建和数据填充脚本 |
| `backend/app/services/aggregation_service.py` | 聚合查询服务 |
| `backend/app/services/__init__.py` | 服务模块导出 |
| `企业级性能优化完成报告.md` | 优化实施报告 |

### 8.8 性能基准

优化后的性能指标：

- 数据库查询：< 10ms（原 500ms+）
- API 响应：< 50ms
- 前端渲染：< 100ms

如果发现性能下降，检查：
1. 是否使用了预聚合表
2. 预聚合表数据是否最新
3. 是否有未优化的原始表查询

---

## 9. 规范落地检查清单（2025-01-19 更新）

### 9.1 已完成的规范落地

| 模块 | 规范项 | 状态 |
|------|--------|------|
| `marketing.py` | 4个接口添加 `store_name` 参数 | ✅ |
| `scenes.py` | 5个接口添加 `store_name` 参数 | ✅ |
| `products.py` | 8个接口添加 `store_name` 参数 | ✅ |
| `customers.py` | 4个接口添加 `store_name` 参数 | ✅ |
| `reports.py` | 5个接口添加 `store_name` 参数 | ✅ |
| `orders.py /overview` | 使用 `aggregation_service` | ✅ |
| `orders.py /trend` | 使用 `aggregation_service` | ✅ |

### 9.2 例外情况（无需修改）

| 文件 | 接口 | 原因 |
|------|------|------|
| `monitoring.py` | `/metrics`, `/ready` | 系统监控需要全量数据 |
| `orders.py` | `/stores` 备用方案 | 门店列表需要全量数据 |


---

## 10. 核心开发规范（2025-01-19 新增）

### 10.1 错误处理规范

#### 后端错误处理

```python
# ✅ 正确：统一错误响应格式
from fastapi import HTTPException
from typing import Optional

class APIError(Exception):
    """自定义API错误"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

# 错误码定义
ERROR_CODES = {
    "STORE_NOT_FOUND": "门店不存在",
    "INVALID_DATE_RANGE": "日期范围无效",
    "DATA_NOT_AVAILABLE": "数据不可用",
    "AGGREGATION_FAILED": "聚合查询失败",
}

# 使用示例
@router.get("/some-api")
async def some_api(store_name: str):
    if not store_name:
        raise HTTPException(status_code=400, detail={
            "code": "STORE_NOT_FOUND",
            "message": "门店名称不能为空"
        })
    
    try:
        result = aggregation_service.get_store_overview(store_name)
        return {"success": True, "data": result}
    except Exception as e:
        # 记录错误日志
        print(f"❌ API错误: {e}")
        raise HTTPException(status_code=500, detail={
            "code": "INTERNAL_ERROR",
            "message": str(e)
        })
```

#### 前端错误处理

```typescript
// ✅ 正确：统一错误处理
import { message } from 'antd';

interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

// API调用封装
async function apiCall<T>(fn: () => Promise<APIResponse<T>>): Promise<T | null> {
  try {
    const res = await fn();
    if (!res.success) {
      message.error(res.error?.message || '请求失败');
      return null;
    }
    return res.data ?? null;
  } catch (error) {
    console.error('API调用失败:', error);
    message.error('网络请求失败，请稍后重试');
    return null;
  }
}

// 使用示例
const data = await apiCall(() => ordersApi.getOverview({ store_name: selectedStore }));
```

### 10.2 日志规范

#### 后端日志

```python
import logging
from datetime import datetime

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# 日志级别使用规范
logger.debug("调试信息：变量值、中间状态")      # 开发调试
logger.info("✅ 操作成功：用户操作、API调用")    # 正常流程
logger.warning("⚠️ 警告：降级处理、性能问题")   # 需要关注
logger.error("❌ 错误：异常捕获、业务错误")      # 需要处理

# API请求日志示例
@router.get("/overview")
async def get_overview(store_name: str):
    start_time = datetime.now()
    logger.info(f"📥 请求: /overview store={store_name}")
    
    try:
        result = aggregation_service.get_store_overview(store_name)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"📤 响应: /overview {elapsed:.1f}ms")
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"❌ /overview 失败: {e}")
        raise
```

#### 前端日志

```typescript
// 开发环境日志
const isDev = import.meta.env.DEV;

const logger = {
  debug: (...args: any[]) => isDev && console.log('[DEBUG]', ...args),
  info: (...args: any[]) => isDev && console.info('[INFO]', ...args),
  warn: (...args: any[]) => console.warn('[WARN]', ...args),
  error: (...args: any[]) => console.error('[ERROR]', ...args),
};

// 使用示例
logger.info('组件挂载', { store: selectedStore });
logger.error('API调用失败', error);
```

### 10.3 类型安全规范

#### TypeScript 严格模式

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

#### 类型定义规范

```typescript
// ✅ 正确：明确定义接口类型
interface OrderOverview {
  total_orders: number;
  total_actual_sales: number;
  total_profit: number;
  avg_order_value: number;
  profit_rate: number;
  active_products: number;
}

// ✅ 正确：API响应类型
interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

// ✅ 正确：使用泛型
async function fetchData<T>(url: string): Promise<APIResponse<T>> {
  const res = await fetch(url);
  return res.json();
}

// ❌ 错误：使用any
const data: any = await fetchData('/api/overview');
```

#### Python 类型注解

```python
from typing import Optional, List, Dict, Any
from datetime import date

# ✅ 正确：函数参数和返回值类型注解
def get_store_overview(
    store_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """获取门店经营总览"""
    pass

# ✅ 正确：Pydantic模型
from pydantic import BaseModel

class StoreOverviewResponse(BaseModel):
    total_orders: int
    total_actual_sales: float
    total_profit: float
    avg_order_value: float
    profit_rate: float
    active_products: int
```

### 10.4 数据验证规范

#### 后端参数验证

```python
from fastapi import Query, Path
from pydantic import BaseModel, validator
from datetime import date

# ✅ 正确：使用Query参数验证
@router.get("/trend")
async def get_trend(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    store_name: Optional[str] = Query(None, min_length=1, max_length=100),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
):
    # 自定义验证
    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "开始日期不能大于结束日期")
    pass

# ✅ 正确：使用Pydantic模型验证
class DateRangeRequest(BaseModel):
    start_date: date
    end_date: date
    
    @validator('end_date')
    def end_after_start(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('结束日期必须大于开始日期')
        return v
```

#### 前端数据验证

```typescript
// ✅ 正确：使用zod进行运行时验证
import { z } from 'zod';

const OrderOverviewSchema = z.object({
  total_orders: z.number().int().nonnegative(),
  total_actual_sales: z.number().nonnegative(),
  total_profit: z.number(),
  avg_order_value: z.number().nonnegative(),
  profit_rate: z.number(),
  active_products: z.number().int().nonnegative(),
});

// 验证API响应
const validateResponse = (data: unknown) => {
  const result = OrderOverviewSchema.safeParse(data);
  if (!result.success) {
    console.error('数据验证失败:', result.error);
    return null;
  }
  return result.data;
};
```

---

## 11. 必要开发规范（2025-01-19 新增）

### 11.1 命名规范

#### 文件命名

| 类型 | 规范 | 示例 |
| ---- | ---- | ---- |
| React组件 | PascalCase | `StoreRankingChart.tsx` |
| TypeScript工具 | camelCase | `dataSampling.ts` |
| Python模块 | snake_case | `aggregation_service.py` |
| API路由 | snake_case | `store_comparison.py` |
| 测试文件 | `*.test.ts` / `test_*.py` | `ProfitChart.test.ts` |

#### 变量命名

```typescript
// TypeScript
const selectedStore = 'xxx';           // camelCase
const CACHE_TTL = 300;                 // UPPER_SNAKE_CASE (常量)
interface OrderOverview { }            // PascalCase (类型)
type DateRange = { start: Date };      // PascalCase (类型)

// Python
selected_store = 'xxx'                 # snake_case
CACHE_TTL = 300                        # UPPER_SNAKE_CASE (常量)
class AggregationService:              # PascalCase (类)
def get_store_overview():              # snake_case (函数)
```

#### API端点命名

```python
# ✅ 正确：RESTful风格，使用连字符
GET  /api/v1/orders/overview           # 获取概览
GET  /api/v1/orders/trend              # 获取趋势
GET  /api/v1/store-comparison/ranking  # 门店排名
POST /api/v1/orders/clear-cache        # 清除缓存

# ❌ 错误：驼峰或下划线
GET  /api/v1/orders/getOverview
GET  /api/v1/store_comparison/ranking
```

### 11.2 注释规范

#### Python文档字符串

```python
def get_store_overview(
    store_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """
    从预聚合表获取门店经营总览数据
    
    Args:
        store_name: 门店名称，None表示全部门店
        start_date: 开始日期
        end_date: 结束日期
        channel: 渠道筛选，支持 '美团'、'饿了么'、'京东'
    
    Returns:
        包含六大核心指标的字典:
        - total_orders: 订单总数
        - total_actual_sales: 商品实收额
        - total_profit: 总利润
        - avg_order_value: 平均客单价
        - profit_rate: 总利润率
        - active_products: 动销商品数
    
    Raises:
        HTTPException: 当数据库查询失败时
    
    Example:
        >>> result = get_store_overview("惠宜选-泰州泰兴店")
        >>> print(result['total_orders'])
        1234
    """
    pass
```

#### TypeScript JSDoc

```typescript
/**
 * 门店排名图表组件
 * 
 * @description 展示门店销售额、订单数、利润的排名对比
 * @param {StoreRankingChartProps} props - 组件属性
 * @returns {JSX.Element} 图表组件
 * 
 * @example
 * <StoreRankingChart 
 *   data={rankingData} 
 *   metric="revenue" 
 *   onStoreClick={handleClick} 
 * />
 */
const StoreRankingChart: React.FC<StoreRankingChartProps> = (props) => {
  // ...
};
```

### 11.3 Git提交规范

#### Commit Message格式

```text
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type类型

| Type | 说明 | 示例 |
| ---- | ---- | ---- |
| feat | 新功能 | `feat(charts): 添加门店排名图表` |
| fix | 修复Bug | `fix(api): 修复渠道筛选逻辑` |
| perf | 性能优化 | `perf(db): 添加预聚合表优化查询` |
| refactor | 重构 | `refactor(store): 重构全局状态管理` |
| docs | 文档 | `docs: 更新开发规范文档` |
| style | 代码格式 | `style: 格式化代码` |
| test | 测试 | `test(api): 添加订单API单元测试` |
| chore | 构建/工具 | `chore: 更新依赖版本` |

#### 示例

```text
feat(store-comparison): 添加全量门店对比功能

- 新增门店排名图表组件
- 新增门店效率散点图组件
- 添加渠道筛选支持（基于order_number前缀）

Closes #123
```

### 11.4 代码审查清单

#### 提交前自查

- [ ] 代码是否通过TypeScript/Python类型检查
- [ ] 是否添加了必要的错误处理
- [ ] API是否传入了store_name参数
- [ ] 是否使用了预聚合表（如适用）
- [ ] 是否有console.log/print调试代码残留
- [ ] 是否更新了相关文档

#### 审查重点

- [ ] 业务逻辑是否与Dash版本一致
- [ ] 性能是否满足要求（API < 50ms）
- [ ] 是否有安全隐患（SQL注入、XSS等）
- [ ] 代码是否可维护、可读

---

## 12. 性能开发规范（2025-01-19 新增）

### 12.1 React性能优化

#### 组件优化

```typescript
// ✅ 正确：使用React.memo避免不必要的重渲染
const StoreRankingChart = React.memo<StoreRankingChartProps>(({ data, metric }) => {
  // 组件实现
});

// ✅ 正确：使用useMemo缓存计算结果
const processedData = useMemo(() => {
  return data.map(item => ({
    ...item,
    profitRate: item.profit / item.revenue * 100
  }));
}, [data]);

// ✅ 正确：使用useCallback缓存回调函数
const handleClick = useCallback((store: string) => {
  setSelectedStore(store);
}, []);

// ❌ 错误：在渲染中创建新对象/函数
<Chart options={{ title: '销售趋势' }} />  // 每次渲染创建新对象
<Button onClick={() => handleClick(store)} />  // 每次渲染创建新函数
```

#### 状态管理优化

```typescript
// ✅ 正确：拆分状态，避免不必要的更新
const [selectedStore, setSelectedStore] = useState('');
const [dateRange, setDateRange] = useState<DateRange>(null);

// ❌ 错误：将所有状态放在一个对象中
const [state, setState] = useState({
  selectedStore: '',
  dateRange: null,
  data: [],
  loading: false,
});
```

### 12.2 ECharts大数据渲染优化

#### 数据采样

```typescript
// 大数据量时进行采样
const MAX_POINTS = 1000;

function sampleData<T>(data: T[], maxPoints: number = MAX_POINTS): T[] {
  if (data.length <= maxPoints) return data;
  
  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
}

// 使用示例
const chartData = sampleData(rawData, 500);
```

#### 渲染优化

```typescript
// ✅ 正确：使用large模式和渐进渲染
const option: EChartsOption = {
  series: [{
    type: 'line',
    large: true,           // 开启大数据优化
    largeThreshold: 2000,  // 数据量阈值
    progressive: 400,      // 渐进渲染
    progressiveThreshold: 3000,
    data: chartData,
  }],
  // 关闭动画提升性能
  animation: chartData.length > 1000 ? false : true,
};
```

### 12.3 数据库查询优化

#### 索引使用

```sql
-- 已创建的复合索引（按查询模式优化）
CREATE INDEX idx_orders_store_date ON orders(store_name, date);
CREATE INDEX idx_orders_store_channel_date ON orders(store_name, channel, date);
CREATE INDEX idx_orders_store_category ON orders(store_name, category_level1);
```

#### 查询优化

```python
# ✅ 正确：使用预聚合表
result = aggregation_service.get_store_overview(store_name, start_date, end_date)

# ✅ 正确：限制查询范围
df = get_order_data(store_name)  # 按门店加载，利用缓存

# ❌ 错误：加载全部数据后过滤
df = get_order_data()  # 加载全部数据
df = df[df['门店名称'] == store_name]  # 内存过滤
```

### 12.4 内存管理

#### 前端内存管理

```typescript
// ✅ 正确：组件卸载时清理
useEffect(() => {
  const chart = echarts.init(chartRef.current);
  
  return () => {
    chart.dispose();  // 清理ECharts实例
  };
}, []);

// ✅ 正确：避免内存泄漏
useEffect(() => {
  let isMounted = true;
  
  fetchData().then(data => {
    if (isMounted) {
      setData(data);
    }
  });
  
  return () => {
    isMounted = false;
  };
}, []);
```

#### 后端内存管理

```python
# ✅ 正确：使用生成器处理大数据
def process_large_data(df: pd.DataFrame):
    for chunk in np.array_split(df, 100):
        yield process_chunk(chunk)

# ✅ 正确：及时释放大对象
def get_report():
    df = get_order_data(store_name)
    result = calculate_metrics(df)
    del df  # 显式释放
    return result
```

---

## 13. 项目特定规范（2025-01-19 新增）

### 13.1 渠道筛选映射规则

渠道筛选基于 `order_number` 字段前缀，而非 `渠道` 字段：

| 前缀 | 渠道 | 说明 |
| ---- | ---- | ---- |
| SG | 美团 | 美团共橙、美团闪购等 |
| ELE | 饿了么 | 饿了么平台 |
| JD | 京东 | 京东到家、京东秒送等 |

#### 后端实现

```python
def filter_by_channel(df: pd.DataFrame, channel: str) -> pd.DataFrame:
    """根据order_number前缀筛选渠道"""
    if channel == 'all' or not channel:
        return df
    
    prefix_map = {
        '美团': 'SG',
        '饿了么': 'ELE',
        '京东': 'JD',
    }
    
    prefix = prefix_map.get(channel)
    if prefix and 'order_number' in df.columns:
        return df[df['order_number'].str.startswith(prefix, na=False)]
    
    return df
```

#### 前端实现

```typescript
// 渠道选项
const CHANNEL_OPTIONS = [
  { value: 'all', label: '全部渠道' },
  { value: '美团', label: '美团' },
  { value: '饿了么', label: '饿了么' },
  { value: '京东', label: '京东' },
];
```

### 13.2 Dash与React数据一致性

#### 参考值对照（惠宜选-泰州泰兴店，最近7天）

| 指标 | 美团共橙 | 饿了么 |
| ---- | -------- | ------ |
| 单均配送 | ¥3.89 | ¥1.61 |
| 单均营销 | ¥5.19 | ¥5.58 |

#### 验证方法

```python
# 运行验证脚本
python 验证成本结构数据一致性_v2.py

# 对比Dash和React计算结果
python 对比Dash和React单均营销计算.py
```

### 13.3 图表组件规范

#### 统一的图表容器

```typescript
// ✅ 正确：使用visibility控制显示，保持容器存在
return (
  <div 
    ref={chartRef} 
    style={{ 
      width: '100%', 
      height: 400,
      visibility: loading ? 'hidden' : 'visible'
    }} 
  />
);

// ❌ 错误：条件渲染导致容器消失
return loading ? <Spin /> : <div ref={chartRef} />;
```

#### 图表初始化

```typescript
const { bindChart, bindChartWithCleanup } = useChart();

useEffect(() => {
  if (!chartRef.current || !data?.length) return;
  
  const cleanup = bindChartWithCleanup(chartRef.current, {
    // ECharts配置
  });
  
  return cleanup;
}, [data, bindChartWithCleanup]);
```

### 13.4 配送成本计算规则

```python
# 配送净成本公式
配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返

# 单均配送成本
单均配送成本 = 配送净成本 / 订单数

# 高配送费订单判定
高配送费订单 = 配送净成本 > 5元
```

### 13.5 营销成本计算规则

```python
# 营销成本公式（7个字段，不含配送费减免）
营销成本 = 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 
         + 满赠金额 + 商家其他优惠 + 新客减免金额

# 单均营销成本
单均营销成本 = 营销成本 / 订单数

# GMV（营业额）计算
GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)
# 注意：需要剔除商品原价 <= 0 的整行数据

# 营销成本率
营销成本率 = 营销成本 / GMV × 100%
```

---

## 14. 环境与部署规范（2025-01-19 新增）

### 14.1 开发环境配置

#### 后端

```bash
# 端口配置
后端服务端口: 8080
数据库: PostgreSQL (pg8000驱动)

# 启动命令
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 注意：代码修改后需要重启后端服务
```

#### 前端

```bash
# 端口配置
前端开发服务器: 5173
API代理: /api -> http://localhost:8080

# 启动命令
cd frontend-react
npm run dev
```

### 14.2 数据库配置

```python
# database/connection.py
DATABASE_URL = "postgresql+pg8000://user:password@localhost:5432/o2o_analysis"

# 连接池配置
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### 14.3 缓存配置

```python
# Redis缓存（可选）
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 86400  # 24小时（数据每天更新一次）

# 数据版本号（智能缓存失效）
DATA_VERSION_KEY = "order_data_version"  # 基于updated_at时间戳

# 内存缓存（备用）
_memory_cache = {
    "order_data": None,
    "timestamp": 0,
    "store_cache": {},
    "data_version": None  # 数据版本号
}
```

### 14.4 预聚合表更新

```bash
# 何时需要更新
1. 导入新订单数据后
2. 新增聚合字段/维度后
3. 修改计算逻辑后

# 更新命令
cd 订单数据看板/订单数据看板/O2O-Analysis
python 全看板性能优化实施.py
```

---

## 15. 版本控制与升级规范（2025-01-19 新增）

### 15.1 API版本控制

```python
# 当前版本: v1
# 路由前缀: /api/v1/

# 版本升级策略
# 1. 新版本使用新前缀: /api/v2/
# 2. 旧版本保持兼容至少3个月
# 3. 废弃API添加Deprecation响应头

@router.get("/overview")
async def get_overview():
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2025-06-01"
    return {"success": True, "data": result}
```

### 15.2 数据库迁移

```python
# 使用Alembic进行数据库迁移
# 1. 创建迁移脚本
alembic revision --autogenerate -m "add new column"

# 2. 执行迁移
alembic upgrade head

# 3. 回滚迁移
alembic downgrade -1
```

### 15.3 向后兼容

```python
# ✅ 正确：新增字段使用默认值
class Order(Base):
    new_field = Column(String, default='', nullable=True)

# ✅ 正确：API响应保持兼容
return {
    "success": True,
    "data": result,
    "meta": {  # 新增字段放在meta中
        "version": "v1.1",
        "deprecated_fields": []
    }
}
```



---

## 16. 安全开发规范（2025-01-19 新增）

### 16.1 SQL注入防护

```python
# ✅ 正确：使用参数化查询
from sqlalchemy import text

sql = "SELECT * FROM orders WHERE store_name = :store_name"
result = session.execute(text(sql), {"store_name": store_name})

# ✅ 正确：使用ORM查询
orders = session.query(Order).filter(Order.store_name == store_name).all()

# ❌ 错误：字符串拼接SQL
sql = f"SELECT * FROM orders WHERE store_name = '{store_name}'"  # 危险！
```

### 16.2 XSS防护

```typescript
// ✅ 正确：React自动转义
<div>{userInput}</div>

// ✅ 正确：需要渲染HTML时使用DOMPurify
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(htmlContent) }} />

// ❌ 错误：直接渲染未经处理的HTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />  // 危险！
```

### 16.3 敏感数据处理

```python
# ✅ 正确：敏感配置使用环境变量
import os
DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")

# ✅ 正确：日志脱敏
logger.info(f"用户登录: {user_id[:4]}****")

# ❌ 错误：硬编码敏感信息
DATABASE_URL = "postgresql://user:password@localhost/db"  # 危险！
```

### 16.4 API安全

```python
# ✅ 正确：限制请求频率
from fastapi import Request
from slowapi import Limiter
limiter = Limiter(key_func=lambda request: request.client.host)

@router.get("/overview")
@limiter.limit("100/minute")
async def get_overview(request: Request):
    pass

# ✅ 正确：验证Content-Type
@router.post("/data")
async def post_data(request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(400, "Invalid content type")

# ✅ 正确：CORS配置
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 明确指定允许的源
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 16.5 安全检查清单

| 检查项 | 说明 | 状态 |
| ------ | ---- | ---- |
| SQL注入 | 所有数据库查询使用参数化 | 待检查 |
| XSS | 用户输入已转义 | 待检查 |
| CSRF | POST请求有token验证 | 待检查 |
| 敏感数据 | 无硬编码密码/密钥 | 待检查 |
| 日志脱敏 | 敏感信息已脱敏 | 待检查 |
| HTTPS | 生产环境强制HTTPS | 待检查 |

---

## 17. 测试开发规范（2025-01-19 新增）

### 17.1 测试分类

| 类型 | 覆盖范围 | 工具 | 目标覆盖率 |
| ---- | -------- | ---- | ---------- |
| 单元测试 | 函数/组件 | Jest/Pytest | ≥ 80% |
| 集成测试 | API端点 | Pytest | ≥ 70% |
| E2E测试 | 用户流程 | Playwright | 核心流程100% |

### 17.2 前端测试规范

```typescript
// 组件测试示例
import { render, screen, fireEvent } from '@testing-library/react';
import { StoreRankingChart } from './StoreRankingChart';

describe('StoreRankingChart', () => {
  const mockData = [
    { store_name: '门店A', revenue: 10000, orders: 100 },
    { store_name: '门店B', revenue: 8000, orders: 80 },
  ];

  it('应该正确渲染图表', () => {
    render(<StoreRankingChart data={mockData} metric="revenue" />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('空数据时应显示空状态', () => {
    render(<StoreRankingChart data={[]} metric="revenue" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('切换指标时应更新图表', () => {
    const { rerender } = render(<StoreRankingChart data={mockData} metric="revenue" />);
    rerender(<StoreRankingChart data={mockData} metric="orders" />);
    // 验证图表更新
  });
});
```

### 17.3 后端测试规范

```python
# API测试示例
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestOrdersAPI:
    """订单API测试"""
    
    def test_get_overview_success(self):
        """测试获取概览成功"""
        response = client.get("/api/v1/orders/overview", params={
            "store_name": "惠宜选-泰州泰兴店"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_orders" in data["data"]
    
    def test_get_overview_invalid_store(self):
        """测试无效门店"""
        response = client.get("/api/v1/orders/overview", params={
            "store_name": "不存在的门店"
        })
        assert response.status_code == 200
        assert response.json()["data"]["total_orders"] == 0
    
    def test_get_trend_date_range(self):
        """测试日期范围筛选"""
        response = client.get("/api/v1/orders/trend", params={
            "store_name": "惠宜选-泰州泰兴店",
            "start_date": "2025-01-01",
            "end_date": "2025-01-07"
        })
        assert response.status_code == 200
        dates = response.json()["data"]["dates"]
        assert len(dates) <= 7


# 数据一致性测试
class TestDataConsistency:
    """Dash与React数据一致性测试"""
    
    def test_marketing_cost_calculation(self):
        """测试营销成本计算一致性"""
        # 获取React版本数据
        response = client.get("/api/v1/orders/overview", params={
            "store_name": "惠宜选-泰州泰兴店"
        })
        react_data = response.json()["data"]
        
        # 与Dash版本参考值对比（允许1%误差）
        dash_reference = {"total_orders": 1234, "total_profit": 5678.90}
        
        assert abs(react_data["total_orders"] - dash_reference["total_orders"]) / dash_reference["total_orders"] < 0.01
```

### 17.4 测试命名规范

```python
# 测试文件命名
test_orders.py          # 后端测试
OrdersAPI.test.ts       # 前端测试

# 测试函数命名
def test_功能_场景_预期结果():
    pass

# 示例
def test_get_overview_with_valid_store_returns_data():
    pass

def test_get_overview_with_invalid_date_raises_error():
    pass
```

### 17.5 测试运行命令

```bash
# 后端测试
cd backend
pytest -v --cov=app --cov-report=html

# 前端测试
cd frontend-react
npm run test
npm run test:coverage

# 单个文件测试
pytest tests/test_orders.py -v
npm run test -- StoreRankingChart.test.ts
```

---

## 18. CI/CD部署规范（2025-01-19 新增）

### 18.1 CI流水线配置

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-fail-under=70

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend-react
          npm ci
      - name: Run tests
        run: |
          cd frontend-react
          npm run test:coverage
      - name: Build
        run: |
          cd frontend-react
          npm run build
```

### 18.2 部署流程

```text
开发环境 (dev)
    ↓ PR合并到develop
预发布环境 (staging)
    ↓ 测试通过 + 审批
生产环境 (prod)
```

### 18.3 部署检查清单

| 阶段 | 检查项 | 说明 |
| ---- | ------ | ---- |
| 部署前 | 代码审查通过 | PR已合并 |
| 部署前 | 测试全部通过 | CI绿色 |
| 部署前 | 数据库迁移准备 | 迁移脚本已测试 |
| 部署中 | 健康检查 | /health端点正常 |
| 部署中 | 回滚方案 | 可快速回滚 |
| 部署后 | 功能验证 | 核心功能正常 |
| 部署后 | 性能监控 | 响应时间正常 |

### 18.4 回滚策略

```bash
# 后端回滚
git revert HEAD
uvicorn app.main:app --reload

# 前端回滚
git revert HEAD
npm run build
# 重新部署静态文件

# 数据库回滚
alembic downgrade -1
```

---

## 19. 监控告警规范（2025-01-19 新增）

### 19.1 监控指标

| 指标类型 | 指标名称 | 阈值 | 告警级别 |
| -------- | -------- | ---- | -------- |
| 可用性 | API成功率 | < 99% | 🔴 严重 |
| 性能 | API响应时间P95 | > 500ms | 🟡 警告 |
| 性能 | 数据库查询时间 | > 100ms | 🟡 警告 |
| 资源 | CPU使用率 | > 80% | 🟡 警告 |
| 资源 | 内存使用率 | > 85% | 🟡 警告 |
| 业务 | 订单数据延迟 | > 5分钟 | 🟡 警告 |

### 19.2 健康检查端点

```python
# backend/app/api/v1/monitoring.py
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """基础健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/ready")
async def readiness_check():
    """就绪检查（含依赖服务）"""
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "aggregation_tables": check_aggregation_tables(),
    }
    
    all_healthy = all(c["status"] == "ok" for c in checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }

def check_database():
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_redis():
    if not REDIS_AVAILABLE:
        return {"status": "unavailable", "message": "Redis not configured"}
    try:
        redis_client.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_aggregation_tables():
    from services.aggregation_service import AVAILABLE_TABLES
    return {
        "status": "ok" if len(AVAILABLE_TABLES) >= 5 else "degraded",
        "tables": list(AVAILABLE_TABLES)
    }
```

### 19.3 性能日志

```python
# 请求耗时日志中间件
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000
    
    # 记录慢请求
    if duration > 200:
        logger.warning(f"🐢 慢请求: {request.method} {request.url.path} {duration:.1f}ms")
    else:
        logger.info(f"📊 {request.method} {request.url.path} {duration:.1f}ms")
    
    return response
```

### 19.4 SLA定义

| 服务 | 可用性目标 | 响应时间目标 |
| ---- | ---------- | ------------ |
| 订单概览API | 99.9% | P95 < 100ms |
| 趋势分析API | 99.5% | P95 < 200ms |
| 门店对比API | 99.5% | P95 < 300ms |
| 报表导出API | 99.0% | P95 < 5s |

---

## 20. 功能废弃规范（2025-01-19 新增）

### 20.1 废弃流程

```text
1. 标记废弃 (Deprecation)
   ↓ 至少保留3个月
2. 发布警告 (Warning)
   ↓ 通知所有使用方
3. 移除功能 (Removal)
```

### 20.2 API废弃标记

```python
# 后端：添加废弃响应头
from fastapi import Response

@router.get("/old-endpoint")
async def old_endpoint(response: Response):
    """
    @deprecated 此接口将在 v2.0 移除，请使用 /new-endpoint
    """
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2025-06-01"
    response.headers["Link"] = '</api/v1/new-endpoint>; rel="successor-version"'
    
    # 记录废弃API使用
    logger.warning(f"⚠️ 废弃API被调用: /old-endpoint")
    
    return {"success": True, "data": result}
```

```typescript
// 前端：废弃函数标记
/**
 * @deprecated 此函数将在 v2.0 移除，请使用 newFunction
 * @see newFunction
 */
function oldFunction() {
  console.warn('oldFunction is deprecated, use newFunction instead');
  return newFunction();
}
```

### 20.3 废弃通知模板

```markdown
## 功能废弃通知

**废弃功能**: `/api/v1/orders/old-endpoint`
**废弃日期**: 2025-01-19
**移除日期**: 2025-06-01
**替代方案**: `/api/v1/orders/new-endpoint`

### 迁移指南

旧接口:
```
GET /api/v1/orders/old-endpoint?store=xxx
```

新接口:
```
GET /api/v1/orders/new-endpoint?store_name=xxx
```

### 变更说明
- 参数名从 `store` 改为 `store_name`
- 响应格式增加 `meta` 字段
```

### 20.4 废弃追踪表

| 功能 | 废弃日期 | 计划移除日期 | 替代方案 | 状态 |
| ---- | -------- | ------------ | -------- | ---- |
| - | - | - | - | - |

---

## 附录A：规范检查清单汇总

### A.1 新功能开发检查

- [ ] 前端使用GlobalContext共享数据
- [ ] 后端API传入store_name参数
- [ ] 使用预聚合表（如适用）
- [ ] 添加错误处理和日志
- [ ] 类型定义完整
- [ ] 参数验证完整
- [ ] 遵循命名规范
- [ ] 添加必要注释
- [ ] 编写单元测试
- [ ] 性能满足要求

### A.2 代码提交检查

- [ ] 通过类型检查
- [ ] 通过lint检查
- [ ] 测试全部通过
- [ ] 无调试代码残留
- [ ] Commit message规范
- [ ] 更新相关文档

### A.3 部署前检查

- [ ] 代码审查通过
- [ ] CI流水线绿色
- [ ] 数据库迁移已测试
- [ ] 回滚方案准备
- [ ] 监控告警配置



---

## 21. 预聚合表数据一致性验证规范（2026-01-19 新增）

### 18.1 问题背景

预聚合表是性能优化的关键，但如果生成逻辑与原始计算不一致，会导致数据错误。

**历史教训**（2026-01-19）：
- 预聚合表生成时遗漏了渠道过滤逻辑（收费渠道且平台服务费=0要剔除）
- 利润公式使用错误（直接用profit字段，而非 利润额-平台服务费-物流配送费+企客后返）
- 动销商品数重复计算（按日期分组后SUM，而非跨日期去重）
- 导致订单数多120单，利润差22000元

### 18.2 强制验证流程

**每次生成或修改预聚合表后，必须运行验证脚本**：

```bash
cd 订单数据看板/订单数据看板/O2O-Analysis
python 验证预聚合表一致性.py
```

验证脚本会对比以下指标：
- 订单总数（必须完全一致）
- 商品实收额（允许0.01误差）
- 总利润（允许0.01误差）
- 动销商品数（必须完全一致）
- GMV（允许0.01误差）
- 营销成本（允许0.01误差）

### 18.3 预聚合表生成检查清单

生成预聚合表前，确认以下逻辑：

- [ ] **渠道过滤**：是否剔除了收费渠道且平台服务费=0的异常订单？
- [ ] **利润公式**：是否使用 `利润额 - 平台服务费 - 物流配送费 + 企客后返`？
- [ ] **字段聚合方式**：商品级字段用SUM，订单级字段用FIRST/MAX？
- [ ] **动销商品数**：是否从原始订单表查询（跨日期去重）？
- [ ] **GMV计算**：是否剔除商品原价<=0的行？是否不受渠道过滤影响？
- [ ] **营销成本**：是否使用7字段（不含配送费减免）？是否不受渠道过滤影响？

### 18.4 核心计算公式参考

```python
# 订单实际利润（核心公式）
订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返

# 渠道过滤规则
收费渠道 = ['饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店']
异常订单 = 收费渠道 且 平台服务费 <= 0
有效订单 = 全部订单 - 异常订单

# GMV计算（不受渠道过滤影响）
GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)
# 前提：剔除商品原价 <= 0 的行

# 营销成本（7字段，不受渠道过滤影响）
营销成本 = 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额

# 动销商品数（跨日期去重）
动销商品数 = COUNT(DISTINCT product_name) WHERE quantity > 0
```

### 18.5 相关文件

| 文件 | 说明 |
|------|------|
| `验证预聚合表一致性.py` | 数据一致性验证脚本（必须运行） |
| `全看板性能优化实施.py` | 预聚合表生成脚本（已集成验证） |
| `修复预聚合表.py` | 预聚合表修复脚本（紧急修复用） |
| `Tab1订单数据概览_卡片计算公式汇总.md` | 计算公式权威文档 |

### 18.6 验证失败处理

如果验证失败：

1. **不要部署**：验证失败的预聚合表会导致前端数据错误
2. **检查生成逻辑**：对照 `Tab1订单数据概览_卡片计算公式汇总.md` 检查SQL
3. **运行修复脚本**：`python 修复预聚合表.py`
4. **重新验证**：`python 验证预聚合表一致性.py`
5. **更新生成脚本**：将修复后的逻辑同步到 `全看板性能优化实施.py`



---

## 22. 智能查询路由引擎（2026-01-20 新增）

### 22.1 概述

智能查询路由引擎（`QueryRouterService`）根据数据量自动选择最优查询引擎：

| 数据量 | 推荐引擎 | 说明 |
|--------|---------|------|
| < 100万条 | PostgreSQL + 预聚合表 | 低延迟，适合中小数据量 |
| ≥ 100万条 | DuckDB + Parquet | 高吞吐，适合大数据量 |

### 22.2 核心特性

- **自动检测数据量**：启动时检测订单总数
- **智能引擎切换**：根据阈值自动选择最优引擎
- **优雅降级**：DuckDB 不可用时自动降级到 PostgreSQL
- **统一查询接口**：业务层无需关心底层引擎
- **查询性能监控**：记录各引擎查询次数和耗时

### 22.3 数据量级别

| 级别 | 数据量范围 | 推荐引擎 |
|------|-----------|---------|
| small（小型） | 0 - 10万 | PostgreSQL |
| medium（中型） | 10万 - 100万 | PostgreSQL |
| large（大型） | 100万 - 1000万 | DuckDB |
| huge（超大型） | > 1000万 | DuckDB |

### 22.4 使用方式

#### 方式一：直接使用路由服务（推荐）

```python
from services.query_router_service import query_router_service

# 获取订单概览（自动选择引擎）
result = query_router_service.query_overview(
    store_name="惠宜选-泰州泰兴店",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 20),
    channel="美团"
)

# 返回 QueryResult 对象
print(result.data)           # 查询结果
print(result.engine)         # 使用的引擎（POSTGRESQL/DUCKDB）
print(result.query_time_ms)  # 查询耗时（毫秒）
print(result.source)         # 数据来源描述
```

#### 方式二：判断后手动调用

```python
from services.query_router_service import query_router_service

# 判断是否应该使用 DuckDB
if query_router_service.should_use_duckdb():
    from services.duckdb_service import duckdb_service
    data = duckdb_service.query_kpi(store_name, start_date, end_date)
else:
    from services.aggregation_service import aggregation_service
    data = aggregation_service.get_store_overview(store_name, start_date, end_date)
```

### 22.5 可用查询方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `query_overview()` | 订单概览（六大卡片） | store_name, start_date, end_date, channel |
| `query_trend()` | 订单趋势 | days, store_name, channel, start_date, end_date, granularity |
| `query_channels()` | 渠道分析 | store_name, start_date, end_date |
| `query_categories()` | 品类分析 | store_name, start_date, end_date, top_n |

### 22.6 状态查询

```python
# 获取路由状态
status = query_router_service.get_status()
print(status)
# {
#     "current_engine": "postgresql",
#     "record_count": 429855,
#     "data_level": "medium",
#     "data_level_desc": "中型",
#     "recommended_engine": "postgresql",
#     "switch_threshold": 1000000,
#     "will_switch_at": "1,000,000 条",
#     "engines": {
#         "postgresql": True,
#         "duckdb": True
#     },
#     "stats": {
#         "postgresql_queries": 150,
#         "duckdb_queries": 0,
#         "auto_switches": 0
#     }
# }
```

### 22.7 启动时状态报告

服务启动时会自动打印路由状态：

```
============================================================
  🧠 智能查询路由引擎
============================================================

  📊 数据量: 429,855 条 (中型数据)
  📈 切换阈值: 1,000,000 条

  🔧 查询引擎状态:
     ✅ PostgreSQL: 连接正常
     ✅ DuckDB: 就绪 (30 个Parquet文件)

  🎯 当前引擎: POSTGRESQL (最优选择)

  💡 智能切换: 数据量达到 1,000,000 条后
              将自动切换到 DuckDB 引擎
              (还需 570,145 条)

============================================================
```

### 22.8 强制切换引擎（测试用）

```python
# 强制切换到 DuckDB（仅用于测试）
result = query_router_service.force_engine("duckdb")
print(result)  # {"success": True, "message": "已切换到 DuckDB", "engine": "duckdb"}

# 切换回 PostgreSQL
result = query_router_service.force_engine("postgresql")
```

### 22.9 相关文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/query_router_service.py` | 智能查询路由服务 |
| `backend/app/services/duckdb_service.py` | DuckDB 查询服务 |
| `backend/app/services/aggregation_service.py` | PostgreSQL 预聚合查询服务 |
| `验证智能路由.py` | 路由功能验证脚本 |

---

## 23. 千万级数据优化架构（2026-01-20 完整实施）

### 23.1 概述

为应对未来数据量增长（当前43万，目标支撑1000万+），已完成千万级优化的准备工作。当前系统使用预聚合表架构，性能已足够支撑现有数据量。

### 23.2 已安装依赖

```bash
# requirements.txt 已添加
duckdb>=0.9.0        # OLAP查询引擎
pyarrow>=14.0.0      # Parquet文件支持
apscheduler>=3.10.0  # 定时任务调度
```

### 23.3 目录结构

```
data/
├── raw/           # 原始订单Parquet（按日期分区）
├── aggregated/    # 预聚合Parquet
└── metadata/      # 元数据（分区信息、同步时间）
```

### 23.4 预备服务

| 服务 | 文件 | 状态 | 启用条件 |
|------|------|------|----------|
| DuckDB查询 | `services/duckdb_service.py` | ✅ 已启用 | 数据量>100万自动切换 |
| Parquet同步 | `services/parquet_sync_service.py` | ✅ 已启用 | - |
| 数据监控 | `services/data_monitor_service.py` | ✅ 已启用 | - |
| 智能路由 | `services/query_router_service.py` | ✅ 已启用 | - |

### 23.5 数据量监控API

```bash
# 获取数据量统计和优化建议
GET /api/v1/data-monitor/stats

# 检查是否需要告警
GET /api/v1/data-monitor/alert

# 获取服务状态
GET /api/v1/data-monitor/services-status
```

### 23.6 阈值配置

| 阈值 | 数据量 | 建议操作 |
|------|--------|----------|
| warning | 100万 | 开始Parquet归档 |
| critical | 300万 | 启用DuckDB查询 |
| urgent | 500万 | 完整实施千万级方案 |

### 23.7 实施状态

**已完整实施（2026-01-20）**：

1. **历史数据已迁移**：429,855条记录 → 30个Parquet文件（18.52MB）
2. **DuckDB服务已启用**：查询性能20-30ms
3. **智能路由已启用**：自动选择最优引擎
4. **定时同步已配置**：
   - 每天02:00同步昨日数据
   - 每小时整点刷新今日数据
5. **API v2已上线**：`/api/v2/orders/*`

### 23.8 API v2 接口

```bash
# v2接口（DuckDB加速）
GET /api/v2/orders/overview    # KPI概览
GET /api/v2/orders/trend       # 趋势分析
GET /api/v2/orders/channels    # 渠道分析
GET /api/v2/orders/categories  # 品类分析
GET /api/v2/orders/status      # DuckDB状态
```

### 23.9 性能对比

| 查询类型 | v1 (预聚合表) | v2 (DuckDB) | 数据量 |
|---------|--------------|-------------|--------|
| 全量KPI | ~2ms | ~28ms | 96,676订单 |
| 趋势查询 | ~5ms | ~18ms | 30天 |
| 渠道分析 | ~3ms | ~20ms | 9渠道 |

> 注：v1使用PostgreSQL预聚合表，v2直接从Parquet实时计算。
> v2虽然稍慢，但支持更灵活的查询，且在千万级数据时优势明显。

### 23.10 相关文件

| 文件 | 说明 |
|------|------|
| `订单数据看板_千万级数据优化方案_v2.0.md` | 完整优化方案文档 |
| `迁移历史数据到Parquet.py` | 历史数据迁移脚本 |
| `测试DuckDB查询.py` | DuckDB查询测试脚本 |
| `测试千万级优化准备.py` | 准备工作验证脚本 |
| `backend/app/services/query_router_service.py` | 智能查询路由服务 |
| `backend/app/services/duckdb_service.py` | DuckDB查询服务 |
| `backend/app/services/parquet_sync_service.py` | Parquet同步服务 |
| `backend/app/services/data_monitor_service.py` | 数据量监控服务 |
| `backend/app/api/v1/data_monitor.py` | 监控API |
| `backend/app/api/v2/orders.py` | v2订单API（DuckDB） |
| `backend/app/tasks/sync_scheduler.py` | 定时同步任务 |
| `data/raw/` | 原始Parquet文件目录 |
| `data/aggregated/` | 聚合Parquet文件目录 |


---

## 24. Redis 缓存配置规范（2026-01-20 新增）

### 24.1 内存配置

Redis 用于缓存聚合结果（非原始数据），内存占用较小：

| 数据规模 | 门店数 | 预估缓存大小 |
|---------|--------|-------------|
| 50万条 | ~10家 | ~100KB |
| 500万条 | ~50家 | ~500KB |
| 1000万条 | ~100家 | ~1MB |
| 5000万条 | ~500家 | ~5MB |

**推荐配置**（已应用）：

```bash
maxmemory 4gb
maxmemory-policy allkeys-lru
```

- `maxmemory 4gb`：最大内存限制4GB（足够支撑千万级数据）
- `allkeys-lru`：内存满时自动淘汰最久未使用的key，不会报错

### 24.2 配置方式

**方式一：运行配置脚本**（推荐）

```bash
python 配置Redis内存.py
```

**方式二：手动配置**

```bash
# 临时配置（重启后失效）
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# 永久配置：编辑 redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
```

### 24.3 缓存策略

| 配置项 | 值 | 说明 |
|--------|-----|------|
| TTL | 24小时 | 缓存过期时间 |
| 版本校验 | 启用 | 基于 `updated_at` 时间戳 |
| 淘汰策略 | allkeys-lru | 内存满时淘汰最久未用 |

### 24.4 常见问题

**Q: 出现 "command not allowed when used memory > 'maxmemory'" 错误**

A: Redis 内存已满，解决方案：
1. 运行 `python 配置Redis内存.py` 增加内存限制
2. 或手动清理：`redis-cli FLUSHDB`

**Q: 缓存数据不更新**

A: 检查数据版本号机制是否正常工作，或手动清缓存：
```bash
POST /api/v1/orders/clear-cache
```

### 24.5 相关文件

| 文件 | 说明 |
|------|------|
| `配置Redis内存.py` | Redis 内存配置脚本 |
| `redis_cache_manager.py` | Redis 缓存管理工具 |
| `backend/app/config.py` | 缓存配置参数 |
| `backend/app/api/v1/orders.py` | 缓存使用示例 |


---

## 25. 启动脚本使用规范（2026-01-20 新增）

### 25.1 一键启动脚本

项目提供 `一键启动React.ps1` 脚本，支持多种启动模式：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 1 - 开发模式 | 前后端热重载 | 日常开发 |
| 2 - 生产模式 | 构建+Hypercorn多进程 | 部署/演示 |
| 3 - 仅后端 | 只启动 FastAPI | 后端调试 |
| 4 - 仅前端 | 只启动 React | 前端调试 |

### 25.2 端口配置

| 服务 | 开发端口 | 生产端口 |
|------|---------|---------|
| React 前端 | 6001 | 4001 |
| FastAPI 后端 | 8080 | 8080 |

### 25.3 生产模式特性

生产模式使用 **Hypercorn** 替代 uvicorn（解决 Windows 多进程问题）：

```powershell
# 自动计算 workers 数量（最多16个）
$workers = [Math]::Min([Environment]::ProcessorCount, 16)

# 启动命令
python -m hypercorn app.main:app --bind 0.0.0.0:8080 --workers $workers
```

**为什么用 Hypercorn？**
- uvicorn 的 `--workers` 参数在 Windows 上会报 `WinError 10022`
- Hypercorn 原生支持 Windows 多进程
- 性能相当，API 兼容

### 25.4 启动前自动检查

脚本会自动检查：
- Redis/Memurai 服务状态
- PostgreSQL 数据库连接
- Node.js 版本
- 端口占用情况

### 25.5 局域网访问

启动后会显示局域网访问地址：
```
本机访问: http://localhost:6001
局域网访问: http://192.168.x.x:6001
```

---

## 26. 利润计算核心公式（2026-01-20 新增）

### 26.1 订单实际利润公式（全局唯一）

```python
订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
```

**字段聚合方式**：

| 字段 | 级别 | 聚合方式 | 说明 |
|------|------|----------|------|
| 利润额 | 商品级 | `sum` | Excel原始利润额 |
| 平台服务费 | 商品级 | `sum` | 平台收取的服务费 |
| 物流配送费 | 订单级 | `first` | 整个订单的配送费 |
| 企客后返 | 商品级 | `sum` | 企业客户返现 |

### 26.2 渠道过滤规则（关键！）

在计算利润前，必须先过滤异常订单：

```python
# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]

# 过滤规则：剔除【收费渠道 且 平台服务费=0】的订单
is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
is_zero_fee = order_agg['平台服务费'] <= 0
invalid_orders = is_fee_channel & is_zero_fee
filtered = order_agg[~invalid_orders]
```

**业务规则**：
- 收费渠道 + 平台服务费>0 → ✅ 保留（正常订单）
- 收费渠道 + 平台服务费=0 → ❌ 剔除（异常订单）
- 不收费渠道 + 平台服务费=0 → ✅ 保留（正常状态）

### 26.3 六大核心卡片公式

| 卡片 | 公式 | 数据源 |
|------|------|--------|
| 订单总数 | `len(order_agg)` | order_agg |
| 商品实收额 | `sum(实收价格)` | order_agg |
| 总利润 | `sum(订单实际利润)` | order_agg |
| 平均客单价 | `sum(商品实售价) / count(订单)` | order_agg |
| 总利润率 | `总利润 / sum(商品实售价) * 100` | order_agg |
| 动销商品数 | `nunique(商品名称) where 月售>0` | df（原始） |

### 26.4 相关文件

| 文件 | 说明 |
|------|------|
| `Tab1订单数据概览_卡片计算公式汇总.md` | 完整公式文档 |
| `【权威】业务逻辑与数据字典完整手册.md` | 业务逻辑手册 |
| `智能门店看板_Dash版.py` | Dash版实现（参考） |
| `backend/app/api/v1/orders.py` | React版后端实现 |

---

## 27. 数据导入规范（2026-01-20 新增）

### 27.1 Excel 数据导入

使用 `智能导入门店数据.py` 脚本导入订单数据：

```bash
python 智能导入门店数据.py
```

### 27.2 必需字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 订单ID | string | 唯一标识 |
| 门店名称 | string | 门店标识 |
| 日期 | date | 订单日期 |
| 渠道 | string | 销售渠道 |
| 商品名称 | string | 商品标识 |
| 月售 | int | 销量 |
| 实收价格 | float | 实际收款 |
| 利润额 | float | 商品利润 |
| 平台服务费 | float | 平台费用 |
| 物流配送费 | float | 配送费用 |

### 27.3 导入后操作

1. **更新预聚合表**：
   ```bash
   python 全看板性能优化实施.py
   ```

2. **验证数据一致性**：
   ```bash
   python 验证预聚合表一致性.py
   ```

3. **同步到 Parquet**（可选，千万级数据时）：
   ```bash
   python 迁移历史数据到Parquet.py
   ```

4. **清理缓存**：
   ```bash
   POST /api/v1/orders/clear-cache
   ```

---

## 附录：开发规范章节索引

| 章节 | 内容 | 更新日期 |
|------|------|----------|
| 1-4 | 前后端基础规范 | 2025-01-16 |
| 5 | 渠道筛选联动 | 2025-01-16 |
| 6 | 滞销品计算逻辑 | 2025-01-16 |
| 7 | 营销成本计算逻辑 | 2026-01-19 |
| 8 | 预聚合表性能优化 | 2025-01-19 |
| 9 | 规范落地检查清单 | 2025-01-19 |
| 10-16 | 核心开发规范 | 2025-01-19 |
| 17-20 | 测试/CI/监控/废弃规范 | 2025-01-19 |
| 21 | 预聚合表一致性验证 | 2026-01-19 |
| 22 | 智能查询路由引擎 | 2026-01-20 |
| 23 | 千万级数据优化架构 | 2026-01-20 |
| 24 | Redis缓存配置 | 2026-01-20 |
| 25 | 启动脚本使用 | 2026-01-20 |
| 26 | 利润计算核心公式 | 2026-01-20 |
| 27 | 数据导入规范 | 2026-01-20 |
| 28 | 系统架构与软硬件配置 | 2026-01-20 |
| 29 | Nginx 生产部署规范 | 2026-01-20 |
| 30 | 可观测性（日志/监控/错误追踪） | 2026-01-20 |


---

## 30. 可观测性规范（2026-01-20 新增）

### 30.1 概述

系统已集成企业级可观测性功能：

| 功能 | 服务 | 状态 |
|------|------|------|
| 日志聚合 | LoggingService | ✅ 已实现 |
| 健康监控 | HealthService | ✅ 已实现 |
| 错误追踪 | ErrorTrackingService | ✅ 已实现 |
| 请求追踪 | ObservabilityMiddleware | ✅ 已实现 |

### 30.2 日志服务

**日志文件位置**: `logs/`

| 文件 | 内容 | 保留时间 |
|------|------|----------|
| `app_YYYY-MM-DD.log` | 应用日志（JSON） | 30天 |
| `error_YYYY-MM-DD.log` | 错误日志 | 90天 |
| `slow_requests_YYYY-MM-DD.log` | 慢请求（>500ms） | 30天 |
| `access_YYYY-MM-DD.log` | API访问日志 | 7天 |

**使用方式**:

```python
from services.logging_service import logging_service

# 记录日志
logging_service.info("操作成功")
logging_service.warning("警告信息")
logging_service.error("错误信息")

# 记录带上下文的错误
logging_service.log_error(exception, context={"user_id": 123})
```

### 30.3 健康监控

**告警阈值**:

| 指标 | 阈值 | 级别 |
|------|------|------|
| CPU | >80% | warning |
| 内存 | >85% | warning |
| 磁盘 | >90% | warning |
| API延迟 | >500ms | warning |
| 数据库延迟 | >100ms | warning |
| 错误率 | >5% | critical |

**API 接口**:

```bash
# 完整健康检查
GET /api/v1/observability/health/full

# 性能指标
GET /api/v1/observability/metrics

# 当前告警
GET /api/v1/observability/alerts
```

### 30.4 错误追踪

**功能**:
- 自动捕获所有未处理异常
- 错误去重（相同错误只记录一次）
- 完整堆栈和请求上下文
- 错误趋势分析

**API 接口**:

```bash
# 错误列表
GET /api/v1/observability/errors

# 错误详情
GET /api/v1/observability/errors/{error_id}

# 错误统计
GET /api/v1/observability/errors/summary

# 高频错误
GET /api/v1/observability/errors/top
```

### 30.5 请求追踪

每个请求自动生成 `trace_id`，用于关联日志：

- 响应头: `X-Trace-ID: abc12345`
- 日志中: `trace_id: abc12345`
- 错误中: `trace_id: abc12345`

### 30.6 监控仪表板

一次性获取所有监控数据：

```bash
GET /api/v1/observability/dashboard
```

返回:
- 健康状态
- 性能指标
- 当前告警
- 错误统计
- 最近错误
- 慢请求列表

### 30.7 相关文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/logging_service.py` | 日志服务 |
| `backend/app/services/health_service.py` | 健康监控服务 |
| `backend/app/services/error_tracking_service.py` | 错误追踪服务 |
| `backend/app/middleware/observability.py` | 可观测性中间件 |
| `backend/app/api/v1/observability.py` | 可观测性 API |
| `企业级监控升级规划.md` | 后续升级规划 |


---

## 28. 系统架构与软硬件配置（2026-01-20 新增）

### 28.1 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户浏览器                                   │
│                    (Chrome/Edge/Firefox)                            │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Nginx (端口 80)                                 │
│              静态资源服务 + API 反向代理                              │
│                    Gzip 压缩 + 缓存                                  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────────┐
│   React 前端静态文件       │   │      FastAPI 后端 (端口 8080)      │
│   (nginx/html/)           │   │      Hypercorn 16 workers         │
└───────────────────────────┘   └───────────────────────────────────┘
                                                │
                ┌───────────────┬───────────────┼───────────────┐
                ▼               ▼               ▼               ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
│   PostgreSQL 16   │ │  Redis/Memurai  │ │   DuckDB    │ │  Parquet    │
│   (端口 5432)     │ │  (端口 6379)    │ │  (内存)     │ │  (文件)     │
│   主数据库        │ │  缓存 4GB       │ │  OLAP查询   │ │  历史归档   │
└───────────────────┘ └─────────────────┘ └─────────────┘ └─────────────┘
```

### 28.2 硬件配置（当前服务器）

| 配置项 | 规格 | 说明 |
|--------|------|------|
| CPU | AMD Ryzen 9 (16核) | 支持 16 workers 并发 |
| 内存 | 62GB DDR4 | 充足，支持大数据处理 |
| 存储 | SSD | 数据库和 Parquet 文件 |
| 网络 | 局域网 | 192.168.x.x 内网分发 |
| 操作系统 | Windows 10/11 | 生产环境 |

### 28.3 运行环境要求

| 环境 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Node.js | 18.0.0 | 20.x LTS | 前端构建和运行 |
| npm | 9.0.0 | 10.x | 包管理器 |
| Python | 3.10 | 3.11+ | 后端运行环境 |
| PostgreSQL | 14 | 16 | 主数据库 |
| Redis | 6.0 | 7.x | 缓存服务 |

**Windows 特殊说明**：
- Redis 在 Windows 上使用 **Memurai**（Redis 兼容实现）
- 生产模式使用 **Hypercorn** 替代 Uvicorn（解决 Windows 多进程问题）

### 28.4 前端技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| React | 18.2.0 | UI 框架 |
| TypeScript | 5.4.5 | 类型安全 |
| Vite | 5.2.0 | 构建工具 |
| TailwindCSS | 3.4.3 | CSS 框架 |
| ECharts | 5.5.0 | 图表库（主要） |
| Recharts | 2.12.0 | 图表库（辅助） |
| Axios | 1.13.2 | HTTP 客户端 |
| React Router | 7.11.0 | 路由管理 |
| date-fns | 4.1.0 | 日期处理 |
| react-day-picker | 9.13.0 | 日期选择器 |
| Lucide React | 0.263.1 | 图标库 |
| clsx | 2.1.0 | 类名合并工具 |
| tailwind-merge | 2.2.1 | Tailwind 类名合并 |
| Vitest | 1.6.0 | 单元测试框架 |
| fast-check | 3.15.0 | 属性测试库 |

**前端 package.json 完整依赖**：

```json
{
  "dependencies": {
    "axios": "^1.13.2",
    "clsx": "^2.1.0",
    "date-fns": "^4.1.0",
    "echarts": "^5.5.0",
    "lucide-react": "^0.263.1",
    "react": "^18.2.0",
    "react-day-picker": "^9.13.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^7.11.0",
    "recharts": "^2.12.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "fast-check": "^3.15.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5",
    "vite": "^5.2.0",
    "vitest": "^1.6.0"
  }
}
```

### 28.5 前端构建配置

**TypeScript 配置**（tsconfig.json）：

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "strict": true,
    "moduleResolution": "bundler",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

**构建产物分包策略**（vite.config.ts）：

```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: (id) => {
        if (id.includes('node_modules')) {
          if (id.includes('react') || id.includes('react-dom')) {
            return 'react-vendor';    // React 核心 ~140KB
          }
          if (id.includes('recharts')) {
            return 'charts-vendor';   // 图表库 ~200KB
          }
          if (id.includes('lucide-react')) {
            return 'icons-vendor';    // 图标库 ~50KB
          }
          if (id.includes('date-fns') || id.includes('dayjs')) {
            return 'date-vendor';     // 日期库 ~30KB
          }
          return 'vendor';            // 其他依赖
        }
      },
    },
  },
  chunkSizeWarningLimit: 1000,  // 单文件警告阈值 1MB
}
```

**分包效果**：
| 文件 | 大小 | 内容 |
|------|------|------|
| react-vendor.js | ~140KB | React 核心 |
| charts-vendor.js | ~200KB | Recharts |
| icons-vendor.js | ~50KB | Lucide 图标 |
| date-vendor.js | ~30KB | date-fns |
| vendor.js | ~100KB | 其他依赖 |
| index.js | ~150KB | 业务代码 |

### 28.6 前端测试配置

**Vitest 配置**（vite.config.ts）：

```typescript
test: {
  globals: true,
  environment: 'node',
  include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
}
```

**测试命令**：

```bash
# 运行所有测试（单次）
npm run test

# 监听模式
npm run test:watch

# 运行单个测试文件
npx vitest run src/components/charts/ProfitChart.test.ts
```

**测试示例**（属性测试）：

```typescript
import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';

describe('ProfitChart 数据处理', () => {
  it('应正确计算利润率', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0, max: 1000000 }),  // 利润
        fc.float({ min: 1, max: 1000000 }),  // 销售额
        (profit, sales) => {
          const rate = (profit / sales) * 100;
          return rate >= -100 && rate <= 100;
        }
      )
    );
  });
});
```

### 28.7 后端技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11+ | 运行环境 |
| FastAPI | 0.104.0+ | Web 框架 |
| Uvicorn | 0.24.0+ | 开发服务器（ASGI） |
| Hypercorn | 0.16.0+ | 生产服务器（支持 Windows 多进程） |
| Gunicorn | 21.0.0+ | Linux 生产服务器（备用） |
| SQLAlchemy | 2.0.0+ | ORM 框架 |
| pg8000 | - | PostgreSQL 纯 Python 驱动 |
| psycopg2-binary | 2.9.9+ | PostgreSQL C 驱动（备用） |
| asyncpg | 0.29.0+ | PostgreSQL 异步驱动 |
| Pydantic | 2.0.0+ | 数据验证 |
| pydantic-settings | 2.0.0+ | 配置管理 |
| Pandas | 2.0.0+ | 数据处理 |
| NumPy | 1.24.0+ | 数值计算 |
| DuckDB | 0.9.0+ | OLAP 查询引擎 |
| PyArrow | 14.0.0+ | Parquet 文件支持 |
| APScheduler | 3.10.0+ | 定时任务调度 |
| Redis | 5.0.0+ | Redis 客户端 |
| openpyxl | 3.1.0+ | Excel 文件处理 |
| httpx | 0.25.0+ | 异步 HTTP 客户端 |
| orjson | 3.9.0+ | 高性能 JSON 序列化 |
| Loguru | 0.7.0+ | 日志框架 |
| python-dotenv | 1.0.0+ | 环境变量加载 |
| tenacity | 8.2.0+ | 重试机制 |
| python-jose | 3.3.0+ | JWT 处理 |
| passlib | 1.7.4+ | 密码哈希 |
| bcrypt | 4.0.1 | 密码加密 |
| email-validator | 2.1.0+ | 邮箱验证 |

**后端 requirements.txt 完整依赖**：

```text
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
hypercorn>=0.16.0
gunicorn>=21.0.0

# Database
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
asyncpg>=0.29.0

# Cache
redis>=5.0.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# 千万级数据优化
duckdb>=0.9.0
pyarrow>=14.0.0
apscheduler>=3.10.0

# Auth
python-jose[cryptography]>=3.3.0
passlib>=1.7.4
bcrypt==4.0.1
python-multipart>=0.0.6

# Validation
pydantic>=2.0.0
pydantic-settings>=2.0.0
email-validator>=2.1.0

# File Processing
openpyxl>=3.1.0

# DateTime
python-dateutil>=2.8.2

# Utils
httpx>=0.25.0
tenacity>=8.2.0
orjson>=3.9.0

# Logging
loguru>=0.7.0

# Environment
python-dotenv>=1.0.0
```

### 28.8 后端服务器对比

| 服务器 | 适用场景 | Workers | Windows 支持 |
|--------|---------|---------|-------------|
| Uvicorn | 开发环境 | 单进程 | ✅ |
| Uvicorn --workers | 生产环境 | 多进程 | ❌ (WinError 10022) |
| Hypercorn | 生产环境 | 多进程 | ✅ |
| Gunicorn | 生产环境 | 多进程 | ❌ (仅 Linux) |

**为什么选择 Hypercorn**：
- 原生支持 Windows 多进程
- ASGI 兼容，与 FastAPI 完美配合
- 性能与 Uvicorn 相当
- 支持 HTTP/2

**启动命令对比**：

```bash
# 开发模式（Uvicorn，支持热重载）
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 生产模式（Hypercorn，16 workers）
hypercorn app.main:app --bind 0.0.0.0:8080 --workers 16 --access-log -
```

### 28.9 数据库配置

#### PostgreSQL 16

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 端口 | 5432 | 默认端口 |
| 数据库名 | order_dashboard | 主数据库 |
| 用户名 | postgres | 默认用户 |
| 连接池大小 | 32 | 常驻连接数 |
| 最大溢出 | 64 | 峰值额外连接 |
| 总最大连接 | 96 | pool_size + max_overflow |
| 连接回收 | 1800秒 | 30分钟回收 |
| 驱动 | pg8000 | 避免 UTF-8 编码问题 |

**连接池配置**（database/connection.py）：

```python
engine = create_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://'),
    pool_size=32,             # 常驻连接数
    max_overflow=64,          # 峰值溢出连接
    pool_timeout=30,          # 获取连接超时（秒）
    pool_recycle=1800,        # 连接回收时间（30分钟）
    pool_pre_ping=True,       # 连接前健康检查
)
```

**预聚合表清单**：

| 表名 | 用途 | 记录数 |
|------|------|--------|
| orders | 原始订单表 | ~430,000 |
| store_daily_summary | 门店日汇总 | ~1,550 |
| store_hourly_summary | 门店小时汇总 | ~22,197 |
| category_daily_summary | 品类日汇总 | ~111,777 |
| delivery_summary | 配送分析汇总 | ~22,444 |
| product_daily_summary | 商品日汇总 | ~249,620 |

**数据库索引**：

```sql
-- 复合索引（按查询模式优化）
CREATE INDEX idx_orders_store_date ON orders(store_name, date);
CREATE INDEX idx_orders_store_channel_date ON orders(store_name, channel, date);
CREATE INDEX idx_orders_store_category ON orders(store_name, category_level1);
```

#### Redis/Memurai

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 端口 | 6379 | 默认端口 |
| 数据库 | DB 1 | 与其他项目隔离 |
| 最大内存 | 4GB | 足够支撑千万级数据 |
| 淘汰策略 | allkeys-lru | 内存满时淘汰最久未用 |
| 缓存 TTL | 24小时 | 数据每天更新一次 |

**Redis 配置**：

```bash
maxmemory 4gb
maxmemory-policy allkeys-lru
```

**缓存 Key 格式**：

| Key 模式 | 说明 | TTL |
|----------|------|-----|
| `order_data:{store_name}` | 门店订单数据 | 24h |
| `order_data_version:{store_name}` | 数据版本号 | 24h |
| `aggregation:{type}:{store}:{date}` | 聚合结果 | 24h |

#### DuckDB（OLAP 引擎）

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 存储模式 | 内存 + 文件 | 按需加载 Parquet |
| 线程数 | auto | 自动匹配 CPU |
| 内存限制 | 无 | 使用系统可用内存 |

**Parquet 文件结构**：

```
data/
├── raw/                          # 原始订单（按日期分区）
│   ├── orders_2025-12-01.parquet
│   ├── orders_2025-12-02.parquet
│   └── ...（共30个文件，18.52MB）
└── aggregated/                   # 预聚合数据
    ├── daily_summary.parquet
    └── hourly_summary.parquet
```

### 27.10 端口配置汇总

| 服务 | 开发端口 | 生产端口 | 说明 |
|------|---------|---------|------|
| React 前端 | 6001 | 80 (Nginx) | Vite 开发 / Nginx 生产 |
| FastAPI 后端 | 8080 | 8080 | Uvicorn / Hypercorn |
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |

### 27.11 Vite 配置

```typescript
// frontend-react/vite.config.ts
export default defineConfig({
  server: {
    port: 6001,
    strictPort: true,
    host: true,  // 允许局域网访问
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'charts-vendor': ['recharts'],
          'icons-vendor': ['lucide-react'],
        },
      },
    },
  },
})
```

### 27.12 后端配置参数

```python
# backend/app/config.py
class Settings(BaseSettings):
    # 应用信息
    APP_NAME: str = "订单数据看板 API"
    APP_VERSION: str = "2.0.0"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    API_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "order_dashboard"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    
    # 缓存TTL
    CACHE_TTL_SHORT: int = 3600      # 1小时
    CACHE_TTL_MEDIUM: int = 21600    # 6小时
    CACHE_TTL_LONG: int = 86400      # 24小时
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500
```

### 27.13 目录结构

```
O2O-Analysis/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/            # API v1 路由
│   │   │   └── v2/            # API v2 路由（DuckDB）
│   │   ├── services/          # 业务服务
│   │   ├── tasks/             # 定时任务
│   │   ├── config.py          # 配置
│   │   ├── dependencies.py    # 依赖注入
│   │   └── main.py            # 入口
│   └── requirements.txt       # Python 依赖
├── frontend-react/            # 前端代码
│   ├── src/
│   │   ├── api/               # API 调用
│   │   ├── components/        # 组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── store/             # 全局状态
│   │   ├── types/             # 类型定义
│   │   ├── utils/             # 工具函数
│   │   └── views/             # 页面视图
│   ├── package.json           # Node 依赖
│   ├── vite.config.ts         # Vite 配置
│   └── tsconfig.json          # TypeScript 配置
├── database/                  # 数据库模型
│   ├── connection.py          # 连接配置
│   └── models.py              # ORM 模型
├── data/                      # 数据文件
│   ├── raw/                   # 原始 Parquet
│   └── aggregated/            # 聚合 Parquet
├── nginx/                     # Nginx 配置
│   └── nginx.conf             # 配置模板
├── nginx-server/              # Nginx 安装目录
│   └── nginx-1.28.1/          # Nginx 程序
├── .kiro/                     # Kiro 配置
│   ├── steering/              # 开发规范
│   └── specs/                 # 功能规格
├── 一键启动React.ps1          # 启动脚本
├── 一键启动Nginx生产版.ps1    # Nginx 启动
├── 部署Nginx服务器.ps1        # Nginx 部署
└── 停止Nginx服务.ps1          # Nginx 停止
```

### 27.14 启动模式对比

| 模式 | 前端 | 后端 | 适用场景 |
|------|------|------|----------|
| 开发模式 | Vite (6001) | Uvicorn (8080) | 日常开发，支持热重载 |
| 生产模式 | Vite Preview (4001) | Hypercorn 16w (8080) | 演示测试 |
| Nginx 模式 | Nginx (80) | Hypercorn 16w (8080) | 正式部署 |

### 27.15 性能配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Hypercorn Workers | 16 | 匹配 CPU 核心数 |
| PostgreSQL 连接池 | 32+64 | 支持高并发 |
| Redis 内存 | 4GB | 缓存聚合结果 |
| Nginx Workers | auto | 自动匹配 CPU |
| Gzip 压缩 | 开启 | 减少传输大小 |
| 静态资源缓存 | 7天 | 减少重复请求 |

### 27.16 环境变量

可通过 `.env` 文件配置：

```bash
# 数据库
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=order_dashboard
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# 应用
DEBUG=false
ENVIRONMENT=production
API_PORT=8080
```

### 27.17 快速搭建指南

**1. 安装依赖**

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend-react
npm install
```

**2. 配置数据库**

```bash
# 创建数据库
createdb order_dashboard

# 初始化表结构
python -c "from database.connection import init_database; init_database()"
```

**3. 启动服务**

```powershell
# 开发模式
.\一键启动React.ps1  # 选择 1

# 生产模式（Nginx）
.\一键启动Nginx生产版.ps1
```

**4. 访问地址**

- 开发：http://localhost:6001
- 生产：http://localhost（Nginx）
- API 文档：http://localhost:8080/docs

### 27.18 API 接口清单

#### API v1（PostgreSQL + 预聚合表）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/orders/overview` | GET | 订单概览（六大卡片） |
| `/api/v1/orders/trend` | GET | 销售趋势 |
| `/api/v1/orders/stores` | GET | 门店列表 |
| `/api/v1/orders/channels` | GET | 渠道列表 |
| `/api/v1/orders/clear-cache` | POST | 清除缓存 |
| `/api/v1/diagnosis/hourly` | GET | 分时段诊断 |
| `/api/v1/diagnosis/distance` | GET | 分距离诊断 |
| `/api/v1/delivery/heatmap` | GET | 配送热力图 |
| `/api/v1/inventory-risk/list` | GET | 库存风险列表 |
| `/api/v1/category-health/analysis` | GET | 品类健康分析 |
| `/api/v1/store-comparison/ranking` | GET | 门店排名 |
| `/api/v1/store-comparison/efficiency` | GET | 门店效率散点 |
| `/api/v1/marketing/cost-structure` | GET | 营销成本结构 |
| `/api/v1/marketing/trend` | GET | 营销趋势 |
| `/api/v1/data-monitor/stats` | GET | 数据量统计 |
| `/api/health` | GET | 健康检查 |

#### API v2（DuckDB + Parquet）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v2/orders/overview` | GET | KPI 概览（DuckDB） |
| `/api/v2/orders/trend` | GET | 趋势分析（DuckDB） |
| `/api/v2/orders/channels` | GET | 渠道分析（DuckDB） |
| `/api/v2/orders/categories` | GET | 品类分析（DuckDB） |
| `/api/v2/orders/status` | GET | DuckDB 状态 |

### 27.19 定时任务配置

| 任务 | 执行时间 | 说明 |
|------|---------|------|
| 同步昨日数据 | 每天 02:00 | PostgreSQL → Parquet |
| 刷新今日数据 | 每小时整点 | 增量同步当天数据 |

**APScheduler 配置**（backend/app/tasks/sync_scheduler.py）：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# 每天凌晨2点同步昨日数据
scheduler.add_job(sync_yesterday_data, 'cron', hour=2, minute=0)

# 每小时整点刷新今日数据
scheduler.add_job(refresh_today_data, 'cron', minute=0)
```

### 28.20 Nginx 配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 版本 | 1.28.1 | Windows 版 |
| 监听端口 | 80 | HTTP |
| Worker 进程 | auto | 自动匹配 CPU |
| Gzip 压缩 | 开启 | text/css/js/json |
| 静态缓存 | 7天 | js/css/图片/字体 |
| API 代理 | /api/ → :8080 | 反向代理 |
| Keepalive | 32 | 后端连接复用 |

### 28.21 外部服务依赖

| 服务 | 用途 | 必需 |
|------|------|------|
| PostgreSQL | 主数据库 | ✅ 必需 |
| Redis/Memurai | 缓存 | ⚠️ 可选（降级到内存缓存） |
| Nginx | Web 服务器 | ⚠️ 可选（可用 Vite Preview） |

### 28.22 脚本清单

| 脚本 | 说明 |
|------|------|
| `一键启动React.ps1` | 启动开发/生产环境 |
| `一键启动Nginx生产版.ps1` | Nginx + Hypercorn 启动 |
| `部署Nginx服务器.ps1` | 首次部署 Nginx |
| `停止Nginx服务.ps1` | 停止 Nginx 服务 |
| `配置防火墙.ps1` | 开放局域网访问端口 |
| `重启PostgreSQL服务.ps1` | 重启数据库 |
| `配置Redis内存.py` | 配置 Redis 内存限制 |
| `全看板性能优化实施.py` | 生成预聚合表 |
| `验证预聚合表一致性.py` | 验证数据一致性 |
| `迁移历史数据到Parquet.py` | 迁移到 Parquet |
| `智能导入门店数据.py` | 导入 Excel 数据 |

---

## 29. Nginx 生产部署规范（2026-01-20 新增）

### 29.1 概述

项目支持使用 Nginx 作为生产环境的 Web 服务器，相比 `npm run preview`：

| 对比项 | npm run preview | Nginx |
|--------|-----------------|-------|
| 并发能力 | 低（单进程） | 高（多 worker） |
| 静态资源 | 无优化 | Gzip + 缓存 |
| 反向代理 | 无 | 支持 |
| 适用场景 | 本地预览 | 生产部署 |

### 29.2 目录结构

```
O2O-Analysis/
├── nginx/
│   └── nginx.conf              # 自定义配置模板
├── nginx-server/
│   └── nginx-1.28.1/           # Nginx 安装目录（手动下载）
│       ├── conf/
│       │   └── nginx.conf      # 实际使用的配置
│       ├── html/               # 前端静态文件
│       ├── logs/               # 访问日志和错误日志
│       └── nginx.exe           # Nginx 可执行文件
├── 部署Nginx服务器.ps1          # 部署脚本
├── 一键启动Nginx生产版.ps1      # 启动脚本
└── 停止Nginx服务.ps1            # 停止脚本
```

### 29.3 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 前端静态资源 + API 代理 |
| Hypercorn | 8080 | 后端 API 服务 |

### 29.4 Nginx 配置要点

```nginx
# nginx/nginx.conf 核心配置

worker_processes auto;  # 自动匹配 CPU 核心数

http {
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;

    # 上游后端
    upstream backend {
        server 127.0.0.1:8080;
        keepalive 32;
    }

    server {
        listen 80;
        root html;  # 前端静态文件目录

        # 静态资源缓存（7天）
        location ~* \.(js|css|png|jpg|ico|svg|woff|woff2)$ {
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # SPA 路由支持
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

### 29.5 部署脚本使用

**首次部署**：

```powershell
# 1. 手动下载 Nginx（Windows 版）
#    https://nginx.org/en/download.html
#    解压到 nginx-server/ 目录

# 2. 运行部署脚本
.\部署Nginx服务器.ps1
```

部署脚本会自动：
- 构建 React 前端（`npm run build`）
- 复制静态文件到 `nginx-server/nginx-1.28.1/html/`
- 应用自定义 Nginx 配置
- 启动 Nginx 服务

**日常启动**：

```powershell
# 一键启动（Nginx + Hypercorn 后端）
.\一键启动Nginx生产版.ps1
```

启动脚本会自动：
- 检查 Redis、PostgreSQL 服务状态
- 清理旧进程
- 启动 Hypercorn 后端（16 workers）
- 启动 Nginx 前端
- 显示访问地址

**停止服务**：

```powershell
.\停止Nginx服务.ps1
```

### 29.6 访问地址

| 访问方式 | 地址 |
|---------|------|
| 本机 | http://localhost |
| 局域网 | http://192.168.x.x |
| 后端 API | http://localhost:8080 |
| API 文档 | http://localhost:8080/docs |

### 29.7 Nginx 管理命令

```powershell
# 进入 Nginx 目录
cd nginx-server\nginx-1.28.1

# 启动
.\nginx.exe

# 停止
.\nginx.exe -s stop

# 重载配置（不中断服务）
.\nginx.exe -s reload

# 检查配置语法
.\nginx.exe -t

# 查看日志
Get-Content logs\access.log -Tail 50
Get-Content logs\error.log -Tail 50
```

### 29.8 常见问题

**Q: 端口 80 被占用**

A: 脚本会自动尝试释放端口，如果失败：
```powershell
# 查看占用进程
netstat -ano | findstr ":80 "

# 手动停止（替换 PID）
taskkill /PID <PID> /F
```

**Q: Nginx 启动失败**

A: 检查错误日志：
```powershell
Get-Content nginx-server\nginx-1.28.1\logs\error.log
```

**Q: API 请求 502 错误**

A: 后端服务未启动，确保 Hypercorn 在 8080 端口运行：
```powershell
# 检查后端状态
curl http://localhost:8080/api/health
```

### 29.9 与开发模式对比

| 场景 | 推荐方式 | 命令 |
|------|---------|------|
| 日常开发 | 开发模式 | `.\一键启动React.ps1` → 选择 1 |
| 演示/测试 | 生产模式 | `.\一键启动React.ps1` → 选择 2 |
| 正式部署 | Nginx | `.\一键启动Nginx生产版.ps1` |

### 27.10 相关文件

| 文件 | 说明 |
|------|------|
| `nginx/nginx.conf` | 自定义配置模板 |
| `部署Nginx服务器.ps1` | 首次部署脚本 |
| `一键启动Nginx生产版.ps1` | 日常启动脚本 |
| `停止Nginx服务.ps1` | 停止服务脚本 |
| `配置防火墙.ps1` | 防火墙配置（局域网访问） |



---

## 30. 后端内核优化规范（2026-01-20 新增）

### 30.1 概述

本章节描述后端内核的企业级优化，包括：
- 请求限流（防止 API 被刷爆）
- 缓存预热（首次访问秒开）
- 缓存保护（防穿透/雪崩/击穿）
- 慢查询监控（性能问题定位）

### 30.2 请求限流

#### 30.2.1 限流策略

| 限流组 | 每分钟限制 | 每秒限制 | 适用路径 |
|--------|-----------|---------|----------|
| high_freq | 120 | 20 | /api/v1/orders/kpi, /api/v1/diagnosis |
| normal | 60 | 10 | 大部分 API |
| heavy | 10 | 2 | /api/v1/reports/export, /api/v1/data/upload |
| auth | 10 | 2 | /api/v1/auth（防暴力破解） |

#### 30.2.2 限流响应

超过限制时返回 HTTP 429：

```json
{
  "success": false,
  "error": "rate_limit_exceeded",
  "message": "请求过于频繁",
  "retry_after": 60
}
```

响应头包含限流信息：
- `X-RateLimit-Limit`: 限制数
- `X-RateLimit-Remaining`: 剩余数
- `X-RateLimit-Reset`: 重置时间（秒）

#### 30.2.3 相关文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/rate_limiter_service.py` | 限流服务 |
| `backend/app/middleware/rate_limit.py` | 限流中间件 |

### 30.3 缓存预热

#### 30.3.1 预热任务

应用启动时自动预热以下数据：

| 任务名 | 缓存键 | TTL | 优先级 |
|--------|--------|-----|--------|
| stores_list | warmup:stores:list | 1小时 | 1 |
| channels_list | warmup:channels:list | 1小时 | 1 |
| date_range | warmup:date:range | 1小时 | 1 |

#### 30.3.2 手动预热

```bash
# 触发预热
POST /api/v1/observability/cache/warmup/trigger

# 查看预热状态
GET /api/v1/observability/cache/warmup/status
```

#### 30.3.3 注册自定义预热任务

```python
from backend.app.services.cache_warmup_service import cache_warmup_service

cache_warmup_service.register_task(
    name="my_data",
    loader=lambda: load_my_data(),
    cache_key="warmup:my:data",
    ttl=3600,
    priority=2
)
```

### 30.4 缓存保护

#### 30.4.1 防护机制

| 问题 | 防护措施 | 说明 |
|------|---------|------|
| 缓存穿透 | 布隆过滤器 + 空值缓存 | 不存在的数据也缓存（60秒） |
| 缓存雪崩 | 随机 TTL | 基础 TTL ± 300秒随机 |
| 缓存击穿 | 互斥锁 | 同一 key 只有一个请求查库 |

#### 30.4.2 使用装饰器

```python
from backend.app.services.cache_protection_service import cache_protection_service

@cache_protection_service.cached(
    key_prefix="orders:kpi",
    ttl=1800,
    protect_penetration=True,
    protect_stampede=True
)
def get_kpi_data(store_id: str):
    return expensive_query()
```

#### 30.4.3 查看统计

```bash
GET /api/v1/observability/cache/protection/stats
```

返回：
- 缓存命中率
- 穿透拦截数
- 空值缓存命中数
- 锁等待次数

### 30.5 慢查询监控

#### 30.5.1 阈值配置

| 级别 | 阈值 | 处理 |
|------|------|------|
| 慢查询 | ≥100ms | 记录日志 |
| 非常慢 | ≥500ms | 记录 + 告警 |

#### 30.5.2 使用装饰器

```python
from backend.app.services.slow_query_service import slow_query_service

@slow_query_service.monitor("get_orders")
def get_orders(store_id: str):
    return db.query(...)
```

#### 30.5.3 使用上下文管理器

```python
with slow_query_service.track("complex_aggregation"):
    result = db.execute(complex_sql)
```

#### 30.5.4 查看慢查询

```bash
# 慢查询列表
GET /api/v1/observability/slow-queries

# 查询统计（按平均耗时排序）
GET /api/v1/observability/slow-queries/stats?order_by=avg_duration_ms

# 汇总信息
GET /api/v1/observability/slow-queries/summary
```

### 30.6 监控 API 汇总

| 端点 | 说明 |
|------|------|
| `/api/v1/observability/rate-limit/stats` | 限流统计 |
| `/api/v1/observability/cache/warmup/status` | 预热状态 |
| `/api/v1/observability/cache/warmup/trigger` | 触发预热 |
| `/api/v1/observability/cache/protection/stats` | 缓存保护统计 |
| `/api/v1/observability/slow-queries` | 慢查询列表 |
| `/api/v1/observability/slow-queries/stats` | 查询统计 |
| `/api/v1/observability/slow-queries/summary` | 慢查询汇总 |
| `/api/v1/observability/database/pool` | 连接池状态 |
| `/api/v1/observability/backend/status` | 后端状态汇总 |

### 30.7 相关文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/rate_limiter_service.py` | 请求限流服务 |
| `backend/app/services/cache_warmup_service.py` | 缓存预热服务 |
| `backend/app/services/cache_protection_service.py` | 缓存保护服务 |
| `backend/app/services/slow_query_service.py` | 慢查询监控服务 |
| `backend/app/middleware/rate_limit.py` | 限流中间件 |
| `backend/app/api/v1/observability.py` | 监控 API |

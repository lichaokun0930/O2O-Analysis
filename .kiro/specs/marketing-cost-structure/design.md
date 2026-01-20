# Design Document: 营销成本结构桑基图

## Overview

将现有的"成本结构"桑基图改造为"营销成本结构"桑基图，展示各渠道在8个营销字段上的费用分布。通过桑基图直观呈现营销资金从渠道流向各营销类型的全景视图。

### 改造范围
- **后端**：新增 `/api/v1/orders/marketing-structure` API
- **前端**：重构 `ProfitChart.tsx` 组件
- **数据流**：渠道 → 8个营销类型

### 8个营销字段（来自【权威】业务逻辑与数据字典完整手册）
| 字段名 | 数据库字段 | 聚合方式 | 说明 |
|--------|-----------|---------|------|
| 配送费减免金额 | delivery_discount | first | 订单级 |
| 满减金额 | full_reduction | first | 订单级 |
| 商品减免金额 | product_discount | first | 订单级 |
| 商家代金券 | merchant_voucher | first | 订单级 |
| 商家承担部分券 | merchant_share | first | 订单级 |
| 满赠金额 | gift_amount | first | 订单级 |
| 商家其他优惠 | other_merchant_discount | first | 订单级 |
| 新客减免金额 | new_customer_discount | first | 订单级 |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MarketingStructureChart.tsx                 │    │
│  │  ┌─────────────┐    ┌─────────────────────────────────┐ │    │
│  │  │   渠道节点   │───▶│        营销类型节点              │ │    │
│  │  │  (左侧)     │    │         (右侧)                  │ │    │
│  │  │ - 美团闪购  │    │ - 配送费减免金额                │ │    │
│  │  │ - 饿了么    │    │ - 满减金额                      │ │    │
│  │  │ - 京东到家  │    │ - 商品减免金额                  │ │    │
│  │  │ - ...      │    │ - 商家代金券                    │ │    │
│  │  └─────────────┘    │ - 商家承担部分券                │ │    │
│  │                     │ - 满赠金额                      │ │    │
│  │                     │ - 商家其他优惠                  │ │    │
│  │                     │ - 新客减免金额                  │ │    │
│  │                     └─────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ordersApi.ts                          │    │
│  │         getMarketingStructure(params)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           /api/v1/orders/marketing-structure             │    │
│  │                                                          │    │
│  │  1. 加载订单数据 (get_order_data)                        │    │
│  │  2. 日期/门店过滤                                        │    │
│  │  3. 订单级聚合 (calculate_order_metrics)                 │    │
│  │  4. 按渠道聚合8个营销字段                                │    │
│  │  5. 计算汇总指标                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Backend API

#### Endpoint: `GET /api/v1/orders/marketing-structure`

**Request Parameters:**
```typescript
interface MarketingStructureParams {
  store_name?: string;    // 门店名称筛选
  start_date?: string;    // 开始日期 (YYYY-MM-DD)
  end_date?: string;      // 结束日期 (YYYY-MM-DD)
}
```

**Response:**
```typescript
interface MarketingStructureResponse {
  success: boolean;
  data: {
    channels: ChannelMarketingData[];
    summary: MarketingSummary;
  };
}

interface ChannelMarketingData {
  channel: string;                    // 渠道名称
  order_count: number;                // 订单数
  revenue: number;                    // 销售额
  marketing_costs: {
    delivery_discount: number;        // 配送费减免金额
    full_reduction: number;           // 满减金额
    product_discount: number;         // 商品减免金额
    merchant_voucher: number;         // 商家代金券
    merchant_share: number;           // 商家承担部分券
    gift_amount: number;              // 满赠金额
    other_discount: number;           // 商家其他优惠
    new_customer_discount: number;    // 新客减免金额
  };
  total_marketing_cost: number;       // 该渠道总营销成本
}

interface MarketingSummary {
  total_marketing_cost: number;       // 总营销成本
  avg_marketing_per_order: number;    // 单均营销费用
  marketing_cost_ratio: number;       // 营销成本率 (%)
  total_orders: number;               // 总订单数
  total_revenue: number;              // 总销售额
}
```

### 2. Frontend API Client

**File:** `frontend-react/src/api/orders.ts`

```typescript
// 新增接口
export interface MarketingStructureData {
  channels: ChannelMarketingData[];
  summary: MarketingSummary;
}

export const ordersApi = {
  // ... 现有方法
  
  getMarketingStructure: async (params: {
    store_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<MarketingStructureData>> => {
    const response = await api.get('/orders/marketing-structure', { params });
    return response.data;
  },
};
```

### 3. Frontend Component

**File:** `frontend-react/src/components/charts/ProfitChart.tsx` (重构)

```typescript
interface Props {
  data: ChannelMarketingData[];
  theme: 'dark' | 'light';
}

// 8个营销类型的颜色配置
const MARKETING_TYPE_COLORS = {
  '配送费减免': '#f43f5e',      // 玫红
  '满减金额': '#f59e0b',        // 橙色
  '商品减免': '#eab308',        // 黄色
  '商家代金券': '#22c55e',      // 绿色
  '商家承担券': '#14b8a6',      // 青色
  '满赠金额': '#3b82f6',        // 蓝色
  '商家其他优惠': '#8b5cf6',    // 紫色
  '新客减免': '#ec4899',        // 粉色
};
```

## Data Models

### 桑基图数据结构

```typescript
// ECharts Sankey 数据格式
interface SankeyNode {
  name: string;
  itemStyle?: {
    color: string;
    borderColor?: string;
    shadowBlur?: number;
    shadowColor?: string;
  };
  label?: {
    position: 'left' | 'right';
  };
}

interface SankeyLink {
  source: string;      // 渠道名称
  target: string;      // 营销类型名称
  value: number;       // 金额
  lineStyle?: {
    color: echarts.graphic.LinearGradient;
    opacity: number;
    curveness: number;
  };
}
```

### 数据转换逻辑

```typescript
function transformToSankeyData(channels: ChannelMarketingData[]): {
  nodes: SankeyNode[];
  links: SankeyLink[];
} {
  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];
  
  // 1. 添加渠道节点（左侧）
  channels.forEach(ch => {
    nodes.push({
      name: ch.channel,
      itemStyle: { color: '#6366f1' },
      label: { position: 'left' }
    });
  });
  
  // 2. 添加营销类型节点（右侧）
  Object.entries(MARKETING_TYPE_COLORS).forEach(([name, color]) => {
    nodes.push({
      name,
      itemStyle: { color },
      label: { position: 'right' }
    });
  });
  
  // 3. 添加连线（过滤零值）
  channels.forEach(ch => {
    const costs = ch.marketing_costs;
    const mappings = [
      ['配送费减免', costs.delivery_discount],
      ['满减金额', costs.full_reduction],
      ['商品减免', costs.product_discount],
      ['商家代金券', costs.merchant_voucher],
      ['商家承担券', costs.merchant_share],
      ['满赠金额', costs.gift_amount],
      ['商家其他优惠', costs.other_discount],
      ['新客减免', costs.new_customer_discount],
    ];
    
    mappings.forEach(([target, value]) => {
      if (value > 0) {
        links.push({
          source: ch.channel,
          target: target as string,
          value: value as number
        });
      }
    });
  });
  
  return { nodes, links };
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 营销字段数据完整性
*For any* API请求，返回的每个渠道数据 SHALL 包含全部8个营销字段，即使某些字段值为0
**Validates: Requirements 1.1, 1.3, 1.4**

### Property 2: 订单级字段聚合正确性
*For any* 包含重复订单ID的数据集，聚合后的营销字段金额 SHALL 等于去重后的订单级字段之和（不会因重复行而翻倍）
**Validates: Requirements 1.2**

### Property 3: 总营销成本计算正确性
*For any* 渠道数据，`total_marketing_cost` SHALL 等于该渠道8个营销字段之和
**Validates: Requirements 3.1, 3.2**

### Property 4: 单均营销费用计算正确性
*For any* 有效数据集，`avg_marketing_per_order` SHALL 等于 `total_marketing_cost / total_orders`
**Validates: Requirements 3.3**

### Property 5: 营销成本率计算正确性
*For any* 有效数据集，`marketing_cost_ratio` SHALL 等于 `total_marketing_cost / total_revenue * 100`
**Validates: Requirements 3.4**

### Property 6: 桑基图连线过滤零值
*For any* 生成的桑基图links数据，不 SHALL 包含value为0的连线
**Validates: Requirements 2.6**

### Property 7: 日期过滤正确性
*For any* 指定日期范围的请求，返回的数据 SHALL 只包含该日期范围内的订单
**Validates: Requirements 1.5, 4.1**

## Error Handling

### Backend Error Handling

```python
@router.get("/marketing-structure")
async def get_marketing_structure(...):
    try:
        # 数据加载和处理
        ...
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "channels": [],
                "summary": {
                    "total_marketing_cost": 0,
                    "avg_marketing_per_order": 0,
                    "marketing_cost_ratio": 0,
                    "total_orders": 0,
                    "total_revenue": 0
                }
            }
        }
```

### Frontend Error Handling

```typescript
// 在组件中处理错误状态
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  const fetchData = async () => {
    try {
      const res = await ordersApi.getMarketingStructure(params);
      if (res.success) {
        setData(res.data);
      } else {
        setError(res.error || '数据加载失败');
      }
    } catch (err) {
      setError('网络请求失败');
    }
  };
  fetchData();
}, [params]);
```

## Testing Strategy

### Unit Tests
- 验证API返回数据结构的完整性
- 验证计算公式的正确性（总营销成本、单均营销费用、营销成本率）
- 验证桑基图数据转换逻辑

### Property-Based Tests
- 使用随机生成的订单数据验证聚合逻辑
- 验证零值过滤逻辑
- 验证日期过滤逻辑

### Integration Tests
- 验证前后端数据流
- 验证全局日期筛选联动
- 验证门店切换联动

### Testing Framework
- Backend: pytest
- Frontend: vitest + @testing-library/react
- Property-based testing: hypothesis (Python) / fast-check (TypeScript)

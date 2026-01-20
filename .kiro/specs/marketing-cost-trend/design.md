# Design Document: 营销成本趋势图表

## Overview

新增营销成本趋势图表，与现有的营销成本结构桑基图形成互补。通过百分比堆叠面积图展示各营销类型占比随时间的变化趋势，帮助运营人员分析营销策略的动态变化。

### 设计目标

- **互补性**：桑基图看"渠道→类型"的资金流向，趋势图看"时间→类型占比"的变化
- **一致性**：与桑基图使用相同的颜色配置和营销类型定义
- **灵活性**：支持绝对值/百分比视图切换

### 8个营销字段（与桑基图一致）

| 字段名 | API字段 | 颜色 |
|--------|---------|------|
| 配送费减免 | delivery_discount | #f43f5e |
| 满减金额 | full_reduction | #f59e0b |
| 商品减免 | product_discount | #eab308 |
| 商家代金券 | merchant_voucher | #22c55e |
| 商家承担券 | merchant_share | #14b8a6 |
| 满赠金额 | gift_amount | #3b82f6 |
| 商家其他优惠 | other_discount | #8b5cf6 |
| 新客减免 | new_customer_discount | #ec4899 |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              MarketingTrendChart.tsx                     │    │
│  │  ┌─────────────────────────────────────────────────────┐│    │
│  │  │         百分比堆叠面积图 (ECharts)                   ││    │
│  │  │  X轴: 日期                                          ││    │
│  │  │  Y轴: 0-100% (百分比) 或 金额 (绝对值)              ││    │
│  │  │  面积: 8个营销类型堆叠                              ││    │
│  │  └─────────────────────────────────────────────────────┘│    │
│  │  [绝对值] [百分比] ← 视图切换按钮                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    ordersApi.ts                          │    │
│  │         getMarketingTrend(params)                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           /api/v1/orders/marketing-trend                 │    │
│  │                                                          │    │
│  │  1. 加载订单数据 (get_order_data)                        │    │
│  │  2. 日期/门店过滤                                        │    │
│  │  3. 订单级聚合 (calculate_order_metrics)                 │    │
│  │  4. 按日期分组聚合8个营销字段                            │    │
│  │  5. 返回时间序列数据                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Backend API

#### Endpoint: `GET /api/v1/orders/marketing-trend`

**Request Parameters:**

```typescript
interface MarketingTrendParams {
  store_name?: string;    // 门店名称筛选
  start_date?: string;    // 开始日期 (YYYY-MM-DD)
  end_date?: string;      // 结束日期 (YYYY-MM-DD)
}
```

**Response:**

```typescript
interface MarketingTrendResponse {
  success: boolean;
  data: {
    dates: string[];                    // 日期数组 ["2024-01-01", "2024-01-02", ...]
    series: {
      delivery_discount: number[];      // 配送费减免金额数组
      full_reduction: number[];         // 满减金额数组
      product_discount: number[];       // 商品减免金额数组
      merchant_voucher: number[];       // 商家代金券数组
      merchant_share: number[];         // 商家承担部分券数组
      gift_amount: number[];            // 满赠金额数组
      other_discount: number[];         // 商家其他优惠数组
      new_customer_discount: number[];  // 新客减免金额数组
    };
    totals: number[];                   // 每日总营销成本数组
  };
}
```

### 2. Frontend API Client

**File:** `frontend-react/src/api/orders.ts`

```typescript
export interface MarketingTrendData {
  dates: string[];
  series: {
    delivery_discount: number[];
    full_reduction: number[];
    product_discount: number[];
    merchant_voucher: number[];
    merchant_share: number[];
    gift_amount: number[];
    other_discount: number[];
    new_customer_discount: number[];
  };
  totals: number[];
}

export const ordersApi = {
  // ... 现有方法
  
  getMarketingTrend: async (params: {
    store_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<MarketingTrendData>> => {
    const response = await api.get('/orders/marketing-trend', { params });
    return response.data;
  },
};
```

### 3. Frontend Component

**File:** `frontend-react/src/components/charts/MarketingTrendChart.tsx`

```typescript
interface Props {
  data: MarketingTrendData;
  theme: 'dark' | 'light';
}

// 复用桑基图的颜色配置
const MARKETING_TYPE_COLORS = {
  '配送费减免': '#f43f5e',
  '满减金额': '#f59e0b',
  '商品减免': '#eab308',
  '商家代金券': '#22c55e',
  '商家承担券': '#14b8a6',
  '满赠金额': '#3b82f6',
  '商家其他优惠': '#8b5cf6',
  '新客减免': '#ec4899',
};

// 视图模式
type ViewMode = 'percentage' | 'absolute';
```

## Data Models

### 数据转换逻辑

```typescript
/**
 * 将API数据转换为ECharts堆叠面积图配置
 */
function transformToStackedAreaData(
  data: MarketingTrendData,
  viewMode: ViewMode
): echarts.EChartsOption {
  const { dates, series, totals } = data;
  
  // 计算每个营销类型的总金额，过滤掉全为0的类型
  const activeTypes = MARKETING_FIELD_MAPPING.filter(([field]) => {
    const values = series[field];
    return values.some(v => v > 0);
  });
  
  // 构建ECharts series
  const echartsSeries = activeTypes.map(([field, displayName]) => {
    const values = series[field];
    
    // 百分比模式：计算每日占比
    const displayValues = viewMode === 'percentage'
      ? values.map((v, i) => totals[i] > 0 ? (v / totals[i]) * 100 : 0)
      : values;
    
    return {
      name: displayName,
      type: 'line',
      stack: 'total',
      areaStyle: { opacity: 0.6 },
      emphasis: { focus: 'series' },
      data: displayValues,
      itemStyle: { color: MARKETING_TYPE_COLORS[displayName] },
    };
  });
  
  return {
    xAxis: { type: 'category', data: dates },
    yAxis: {
      type: 'value',
      max: viewMode === 'percentage' ? 100 : undefined,
      axisLabel: {
        formatter: viewMode === 'percentage' ? '{value}%' : '¥{value}',
      },
    },
    series: echartsSeries,
  };
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do.*



### Property 1: API返回数据结构完整性

*For any* 有效的API请求，返回的数据 SHALL 包含dates数组、series对象（含8个营销字段数组）和totals数组，且三者长度相等

**Validates: Requirements 1.1, 1.3**

### Property 2: 订单级字段聚合正确性

*For any* 包含重复订单ID的数据集，按日期聚合后的营销字段金额 SHALL 等于去重后的订单级字段之和（不会因重复行而翻倍）

**Validates: Requirements 1.2**

### Property 3: 日期过滤正确性

*For any* 指定日期范围的请求，返回的dates数组 SHALL 只包含该日期范围内的日期

**Validates: Requirements 1.4**

### Property 4: 零值类型过滤

*For any* 生成的图表series数据，不 SHALL 包含在整个时间范围内金额都为0的营销类型

**Validates: Requirements 2.6**

### Property 5: 百分比计算正确性

*For any* 百分比视图下的每一天，各营销类型的占比之和 SHALL 等于100%（或当总金额为0时全为0）

**Validates: Requirements 3.3**

### Property 6: 绝对值视图数据一致性

*For any* 绝对值视图下的数据，各营销类型的值 SHALL 等于API返回的原始金额（不做百分比转换）

**Validates: Requirements 3.2**

## Error Handling

### Backend Error Handling

```python
@router.get("/marketing-trend")
async def get_marketing_trend(...):
    try:
        # 数据加载和处理
        ...
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {
                "dates": [],
                "series": {
                    "delivery_discount": [],
                    "full_reduction": [],
                    "product_discount": [],
                    "merchant_voucher": [],
                    "merchant_share": [],
                    "gift_amount": [],
                    "other_discount": [],
                    "new_customer_discount": []
                },
                "totals": []
            }
        }
```

### Frontend Error Handling

```typescript
const [error, setError] = useState<string | null>(null);
const [loading, setLoading] = useState(false);

useEffect(() => {
  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await ordersApi.getMarketingTrend(params);
      if (res.success) {
        setData(res.data);
        setError(null);
      } else {
        setError(res.error || '数据加载失败');
      }
    } catch (err) {
      setError('网络请求失败');
    } finally {
      setLoading(false);
    }
  };
  fetchData();
}, [params]);
```

## Testing Strategy

### Unit Tests

- 验证API返回数据结构的完整性
- 验证日期过滤逻辑
- 验证数据转换函数（百分比计算、零值过滤）

### Property-Based Tests

- 使用随机生成的订单数据验证聚合逻辑
- 验证百分比之和为100%的不变量
- 验证零值类型过滤逻辑

### Testing Framework

- Backend: pytest + hypothesis
- Frontend: vitest + fast-check


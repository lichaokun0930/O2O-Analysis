# Design Document - 全局门店洞察分析引擎

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React)                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              StoreComparisonView.tsx                     │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │         GlobalInsightsPanel.tsx                  │    │    │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐           │    │    │
│  │  │  │ 整体概况 │ │ 门店分群 │ │ 异常检测 │ ...       │    │    │
│  │  │  └─────────┘ └─────────┘ └─────────┘           │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         /api/v1/store-comparison/global-insights         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              InsightsEngine (核心分析引擎)                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ StatAnalyzer │  │ ClusterEngine│  │ AnomalyDetect│   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ TrendAnalyzer│  │ Attribution  │  │ ReportGen    │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| StatAnalyzer | 描述性统计分析 | 门店指标数据 | 均值/中位数/标准差/分位数 |
| ClusterEngine | 门店分群 | 门店利润率数据 | 高/中/低绩效分群 |
| AnomalyDetect | 异常检测 | 门店全量指标 | 异常门店列表及原因 |
| TrendAnalyzer | 趋势分析 | 环比数据 | 增长/下滑门店列表 |
| Attribution | 归因分析 | 门店指标+相关系数 | 影响因素排序 |
| ReportGen | 报告生成 | 各模块分析结果 | 结构化文字报告 |

## 2. 数据模型

### 2.1 API 响应数据结构

```typescript
interface GlobalInsightsResponse {
  success: boolean;
  data: {
    // 整体概况
    overview: {
      total_stores: number;
      total_orders: number;
      total_revenue: number;
      total_profit: number;
      weighted_profit_margin: number;
      statistics: {
        profit_margin: {
          mean: number;
          median: number;
          std: number;
          p25: number;
          p50: number;
          p75: number;
          p90: number;
        };
        aov: { mean: number; median: number; std: number };
        order_count: { mean: number; median: number; std: number };
      };
      summary_text: string;  // 生成的总结文字
    };
    
    // 门店分群
    clustering: {
      high_performance: {
        count: number;
        percentage: number;
        avg_metrics: { revenue: number; profit: number; profit_margin: number; aov: number };
        top_stores: string[];  // 前3名门店
        characteristics: string;  // 特征描述
      };
      medium_performance: { /* 同上 */ };
      low_performance: { /* 同上 */ };
      summary_text: string;
    };
    
    // 异常检测
    anomalies: {
      total_anomaly_stores: number;
      by_type: {
        low_profit_margin: AnomalyStore[];
        low_order_count: AnomalyStore[];
        high_marketing_cost: AnomalyStore[];
        high_delivery_cost: AnomalyStore[];
      };
      summary_text: string;
    };
    
    // 头尾对比
    head_tail_comparison: {
      top_stores: StoreMetrics[];
      bottom_stores: StoreMetrics[];
      differences: {
        profit_margin_gap: number;
        aov_gap: number;
        marketing_cost_rate_gap: number;
        delivery_cost_rate_gap: number;
      };
      top_characteristics: string;
      bottom_issues: string;
      summary_text: string;
    };
    
    // 利润率归因
    attribution: {
      correlations: {
        aov_correlation: number;
        marketing_cost_correlation: number;
        delivery_cost_correlation: number;
      };
      primary_factor: string;
      summary_text: string;
    };
    
    // 趋势分析
    trends: {
      growing_stores: { count: number; percentage: number; top3: TrendStore[] };
      declining_stores: { count: number; percentage: number; top3: TrendStore[] };
      summary_text: string;
    };
    
    // 策略建议
    recommendations: {
      urgent: Recommendation[];
      important: Recommendation[];
      general: Recommendation[];
      summary_text: string;
    };
    
    // 生成时间
    generated_at: string;
  };
}

interface AnomalyStore {
  store_name: string;
  value: number;
  threshold: number;
  severity: 'high' | 'medium' | 'low';
  message: string;
}

interface TrendStore {
  store_name: string;
  change_rate: number;
  current_value: number;
  previous_value: number;
}

interface Recommendation {
  priority: 'urgent' | 'important' | 'general';
  category: string;
  title: string;
  description: string;
  action_items: string[];
  affected_stores: string[];
}
```

### 2.2 前端类型定义

```typescript
// types/index.ts 新增
export interface GlobalInsightsData {
  overview: OverviewInsight;
  clustering: ClusteringInsight;
  anomalies: AnomalyInsight;
  head_tail_comparison: HeadTailInsight;
  attribution: AttributionInsight;
  trends: TrendInsight;
  recommendations: RecommendationInsight;
  generated_at: string;
}
```

## 3. 算法设计

### 3.1 门店分群算法

基于利润率分位数的简单分群：

```python
def cluster_stores(stores: List[StoreMetrics]) -> Dict:
    profit_margins = [s.profit_margin for s in stores]
    p25 = np.percentile(profit_margins, 25)
    p75 = np.percentile(profit_margins, 75)
    
    high = [s for s in stores if s.profit_margin >= p75]
    medium = [s for s in stores if p25 <= s.profit_margin < p75]
    low = [s for s in stores if s.profit_margin < p25]
    
    return {
        'high_performance': high,
        'medium_performance': medium,
        'low_performance': low
    }
```

### 3.2 异常检测算法

#### Z-Score 方法（利润率）
```python
def detect_zscore_anomalies(values: List[float], threshold: float = 2.0):
    mean = np.mean(values)
    std = np.std(values)
    anomalies = []
    for i, v in enumerate(values):
        z = (v - mean) / std if std > 0 else 0
        if abs(z) > threshold:
            anomalies.append({
                'index': i,
                'value': v,
                'z_score': z,
                'severity': 'high' if abs(z) > 3 else 'medium'
            })
    return anomalies
```

#### IQR 方法（订单量）
```python
def detect_iqr_anomalies(values: List[float]):
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    anomalies = []
    for i, v in enumerate(values):
        if v < lower_bound or v > upper_bound:
            anomalies.append({
                'index': i,
                'value': v,
                'bound': lower_bound if v < lower_bound else upper_bound
            })
    return anomalies
```

#### 阈值方法（成本率）
```python
def detect_threshold_anomalies(stores, field, threshold, direction='above'):
    anomalies = []
    for s in stores:
        value = getattr(s, field)
        if direction == 'above' and value > threshold:
            anomalies.append(s)
        elif direction == 'below' and value < threshold:
            anomalies.append(s)
    return anomalies
```

### 3.3 相关性分析

```python
def calculate_correlations(stores: List[StoreMetrics]) -> Dict:
    profit_margins = [s.profit_margin for s in stores]
    aovs = [s.aov for s in stores]
    marketing_rates = [s.marketing_cost_rate for s in stores]
    delivery_rates = [s.delivery_cost_rate for s in stores]
    
    return {
        'aov_correlation': np.corrcoef(profit_margins, aovs)[0, 1],
        'marketing_cost_correlation': np.corrcoef(profit_margins, marketing_rates)[0, 1],
        'delivery_cost_correlation': np.corrcoef(profit_margins, delivery_rates)[0, 1]
    }
```

### 3.4 文字报告生成

使用模板 + 数据填充的方式生成报告：

```python
def generate_overview_text(overview: Dict) -> str:
    template = """
📊 整体经营概况

当前共有 {total_stores} 家门店参与分析，累计完成 {total_orders:,} 笔订单，
实现销售额 ¥{total_revenue:,.0f}，总利润 ¥{total_profit:,.0f}。

加权平均利润率为 {weighted_profit_margin:.1f}%，
其中利润率中位数为 {median:.1f}%，标准差为 {std:.1f}%。

利润率分布：
- P25（低于75%门店）: {p25:.1f}%
- P50（中位数）: {p50:.1f}%
- P75（高于75%门店）: {p75:.1f}%
- P90（头部10%门店）: {p90:.1f}%

{health_assessment}
"""
    # 健康度评估
    if overview['weighted_profit_margin'] >= 25:
        health = "✅ 整体经营状况良好，利润率处于健康水平。"
    elif overview['weighted_profit_margin'] >= 15:
        health = "⚠️ 整体经营状况一般，建议关注成本控制。"
    else:
        health = "🔴 整体利润率偏低，需要重点优化运营策略。"
    
    return template.format(
        health_assessment=health,
        **overview,
        **overview['statistics']['profit_margin']
    )
```

## 4. 接口设计

### 4.1 后端 API

```python
@router.get("/comparison/global-insights")
async def get_global_insights(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    channel: Optional[str] = Query(None),
    include_trends: bool = Query(True, description="是否包含趋势分析（需要环比数据）")
) -> Dict[str, Any]:
    """
    全局门店洞察分析
    
    返回完整的洞察报告，包含：
    - 整体概况分析
    - 门店分群分析
    - 异常门店检测
    - 头尾对比分析
    - 利润率归因分析
    - 趋势变化分析
    - 策略建议
    """
```

### 4.2 前端 API 调用

```typescript
// api/storeComparison.ts 新增
export const storeComparisonApi = {
  // ... 现有方法
  
  getGlobalInsights: async (params: {
    start_date?: string;
    end_date?: string;
    channel?: string;
    include_trends?: boolean;
  }): Promise<ApiResponse<GlobalInsightsData>> => {
    const response = await api.get('/store-comparison/global-insights', { params });
    return response.data;
  }
};
```

## 5. 前端组件设计

### 5.1 组件结构

```
GlobalInsightsPanel/
├── index.tsx                 # 主组件
├── sections/
│   ├── OverviewSection.tsx   # 整体概况
│   ├── ClusteringSection.tsx # 门店分群
│   ├── AnomalySection.tsx    # 异常检测
│   ├── ComparisonSection.tsx # 头尾对比
│   ├── AttributionSection.tsx# 归因分析
│   ├── TrendSection.tsx      # 趋势分析
│   └── RecommendSection.tsx  # 策略建议
└── styles.ts                 # 样式
```

### 5.2 主组件设计

```tsx
const GlobalInsightsPanel: React.FC<Props> = ({ 
  startDate, 
  endDate, 
  channel,
  theme = 'dark'
}) => {
  const [insights, setInsights] = useState<GlobalInsightsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['overview', 'anomalies', 'recommendations'])
  );
  
  // 加载洞察数据
  useEffect(() => {
    loadInsights();
  }, [startDate, endDate, channel]);
  
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Brain size={24} className="text-purple-400" />
          全局门店洞察分析
        </h2>
        <span className="text-xs text-slate-500">
          生成时间: {insights?.generated_at}
        </span>
      </div>
      
      {/* 可折叠的分析模块 */}
      <div className="space-y-4">
        <CollapsibleSection title="📊 整体概况" id="overview" />
        <CollapsibleSection title="🎯 门店分群" id="clustering" />
        <CollapsibleSection title="⚠️ 异常检测" id="anomalies" />
        <CollapsibleSection title="🔄 头尾对比" id="comparison" />
        <CollapsibleSection title="📈 归因分析" id="attribution" />
        <CollapsibleSection title="📉 趋势分析" id="trends" />
        <CollapsibleSection title="💡 策略建议" id="recommendations" />
      </div>
    </div>
  );
};
```

### 5.3 文字报告样式

```tsx
// 报告文字样式
const ReportText: React.FC<{ text: string }> = ({ text }) => {
  // 解析并高亮关键数据
  const highlightedText = text
    .replace(/(\d+\.?\d*%)/g, '<span class="text-cyan-400 font-semibold">$1</span>')
    .replace(/(¥[\d,]+)/g, '<span class="text-emerald-400 font-semibold">$1</span>')
    .replace(/(✅|⚠️|🔴|💡)/g, '<span class="text-lg">$1</span>');
  
  return (
    <div 
      className="text-slate-300 leading-relaxed whitespace-pre-line"
      dangerouslySetInnerHTML={{ __html: highlightedText }}
    />
  );
};
```

## 6. 性能考虑

### 6.1 缓存策略

- 洞察报告缓存 5 分钟（与门店对比数据同步）
- 缓存 key: `global_insights:{start_date}:{end_date}:{channel}`

### 6.2 计算优化

- 复用现有的 `get_stores_comparison` 数据
- 复用现有的 `get_stores_week_over_week` 数据
- 避免重复查询数据库

### 6.3 响应时间目标

- 目标: < 5 秒
- 预期: 2-3 秒（基于现有 API 性能）

## 7. 集成方案

### 7.1 在 StoreComparisonView 中集成

```tsx
// StoreComparisonView.tsx
const StoreComparisonView = () => {
  const [showInsights, setShowInsights] = useState(false);
  
  return (
    <div>
      {/* 现有内容 */}
      
      {/* 全局洞察按钮 */}
      <button onClick={() => setShowInsights(!showInsights)}>
        {showInsights ? '收起洞察' : '🔍 全局洞察分析'}
      </button>
      
      {/* 洞察面板 */}
      {showInsights && (
        <GlobalInsightsPanel
          startDate={currentPeriodStart}
          endDate={currentPeriodEnd}
          channel={selectedChannel}
        />
      )}
      
      {/* 现有图表和表格 */}
    </div>
  );
};
```

## 8. 测试策略

### 8.1 单元测试

- 统计计算函数测试
- 异常检测算法测试
- 文字生成模板测试

### 8.2 集成测试

- API 端到端测试
- 前端组件渲染测试

### 8.3 性能测试

- 大数据量（100+ 门店）响应时间测试

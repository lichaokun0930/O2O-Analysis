export enum ChannelType {
  MEITUAN = '美团外卖',
  ELEME = '饿了么',
  DOUYIN = '抖音团购',
  OFFLINE = '线下门店',
  PRIVATE_DOMAIN = '私域小程序'
}

export interface HourlyMetric {
  hour: string;
  revenue: number;
  orders: number;
  deliveryCost: number;
}

export interface DistanceMetric {
  range: string;
  orders: number;
  avgDeliveryCost: number;
}

export interface DailyMetric {
  date: string;
  revenue: number;
  profit: number;
  orders: number;
}

export interface MarketingCostBreakdown {
  itemDiscount: number;
  thresholdDiscount: number;
  vouchers: number;
  other: number;
}

export interface MarketingDailyBreakdown {
  date: string;
  itemDiscount: number;
  thresholdDiscount: number;
  vouchers: number;
  other: number;
}

export interface CategoryMetric {
  name: string;
  revenue: number;
  cost: number;
  profit: number;
  grossMargin: number;
  // 库存与供应链指标
  orderCount?: number;        // 销量
  soldOutCount?: number;      // 售罄品数
  slowMovingCount?: number;   // 滞销品数
  inventoryTurnover?: number; // 库存周转天数
}

// 售罄品/滞销品风险详情
export interface SkuRiskMetric {
  id: string;
  skuName: string;           // 商品名称
  spec: string;              // 规格
  issueType: 'OUT_OF_STOCK' | 'SLOW_MOVING';
  reason: string;            // 原因
  impactValue: number;       // 影响金额
  duration: string;          // 持续时间
  action: string;            // 建议操作
  severity?: 'light' | 'medium' | 'heavy' | 'critical'; // 滞销等级
}

export interface AOVBucket {
  range: string;
  count: number;
}

export interface CostBreakdown {
  cogs: number;
  marketing: number;
  delivery: number;
  commission: number;
}

export interface ChannelMetrics {
  id: string;
  name: ChannelType;
  revenue: number;
  
  costs: CostBreakdown;
  marketingDetails: MarketingCostBreakdown;
  marketingTrend: MarketingDailyBreakdown[];
  
  totalCost: number;
  profit: number;
  
  marketingRate: number;
  profitMargin: number;

  orderCount: number;
  avgOrderValue: number;
  avgDeliveryCost: number;

  hourlyData: HourlyMetric[];
  distanceData: DistanceMetric[];
  dailyTrend: DailyMetric[];
  
  categoryPerformance: CategoryMetric[];
  aovDistribution: AOVBucket[];
}

export interface DashboardData {
  totalRevenue: number;
  totalProfit: number;
  totalOrders: number;
  channels: ChannelMetrics[];
  lastUpdated: string;
}

export interface AIInsight {
  summary: string;
  costProblem: string;
  timeOpportunity: string;
  actionSuggestion: string;
}

export type FocusArea = 'cost' | 'efficiency' | 'trend' | 'profit' | null;

// ==================== 图表联动类型 ====================

/** 分时段品类走势数据项 */
export interface CategoryTrendMetric {
  dateOrHour: string;
  category: string;
  revenue: number;
}

/** 商品销量数据项 */
export interface ProductSalesMetric {
  name: string;
  category: string;
  quantity: number;
  revenue: number;
  profit: number;
  growth: number;
}


// ==================== 分距离订单诊断类型 ====================

/** 距离区间指标 - Requirements 2.1 */
export interface DistanceBandMetric {
  band_label: string;           // 区间标签，如 "0-1km", "1-2km" 等
  min_distance: number;         // 区间最小距离 (km)
  max_distance: number;         // 区间最大距离 (km)，6km+ 时为 Infinity
  order_count: number;          // 订单数
  revenue: number;              // 销售额
  profit: number;               // 利润
  profit_rate: number;          // 利润率 (%)
  delivery_cost: number;        // 配送成本
  delivery_cost_rate: number;   // 配送成本率 (%)
  avg_order_value: number;      // 平均客单价
}


/** 距离分析汇总数据 - Requirements 2.2 */
export interface DistanceAnalysisSummary {
  total_orders: number;         // 总订单数
  avg_distance: number;         // 平均配送距离 (km)
  optimal_distance: string;     // 最优距离区间标签（利润率最高的区间）
  total_revenue: number;        // 总销售额
  total_profit: number;         // 总利润
}

/** 距离分析数据 - Requirements 2.2, 2.3 */
export interface DistanceAnalysisData {
  date?: string;                         // 🆕 分析日期（YYYY-MM-DD格式）
  distance_bands: DistanceBandMetric[];  // 7个距离区间的指标数组
  summary: DistanceAnalysisSummary;      // 汇总统计
}


// ==================== 营销成本结构类型 ====================

/** 渠道营销成本明细 - Requirements 1.3 */
export interface MarketingCosts {
  delivery_discount: number;        // 配送费减免金额
  full_reduction: number;           // 满减金额
  product_discount: number;         // 商品减免金额
  merchant_voucher: number;         // 商家代金券
  merchant_share: number;           // 商家承担部分券
  gift_amount: number;              // 满赠金额
  other_discount: number;           // 商家其他优惠
  new_customer_discount: number;    // 新客减免金额
}

/** 渠道营销数据 - Requirements 1.1, 1.3 */
export interface ChannelMarketingData {
  channel: string;                  // 渠道名称
  order_count: number;              // 订单数
  revenue: number;                  // 销售额
  marketing_costs: MarketingCosts;  // 8个营销字段明细
  total_marketing_cost: number;     // 该渠道总营销成本
}

/** 营销成本汇总 - Requirements 3.1, 3.2, 3.3, 3.4 */
export interface MarketingSummary {
  total_marketing_cost: number;       // 总营销成本
  avg_marketing_per_order: number;    // 单均营销费用
  marketing_cost_ratio: number;       // 营销成本率 (%)
  total_orders: number;               // 总订单数
  total_revenue: number;              // 总销售额
}

/** 营销成本结构数据 - Requirements 1.1 */
export interface MarketingStructureData {
  channels: ChannelMarketingData[];   // 各渠道营销数据
  summary: MarketingSummary;          // 汇总指标
}


// ==================== 营销成本趋势类型 ====================

/** 营销成本趋势系列数据 - Requirements 1.3 */
/** 7个营销字段，不含配送费减免金额（配送费减免属于配送成本） */
export interface MarketingTrendSeries {
  full_reduction: number[];         // 满减金额数组
  product_discount: number[];       // 商品减免金额数组
  merchant_voucher: number[];       // 商家代金券数组
  merchant_share: number[];         // 商家承担部分券数组
  gift_amount: number[];            // 满赠金额数组
  other_discount: number[];         // 商家其他优惠数组
  new_customer_discount: number[];  // 新客减免金额数组
  delivery_discount?: number[];     // 配送费减免金额（已废弃，保留兼容性）
}

/** 营销成本趋势数据 - Requirements 1.1, 1.3 */
export interface MarketingTrendData {
  dates: string[];                  // 日期数组 ["2024-01-01", "2024-01-02", ...]
  series: MarketingTrendSeries;     // 各营销类型的每日金额数组
  totals: number[];                 // 每日总营销成本数组
}


// ==================== 全量门店对比分析 ====================

/** 门店对比数据 */
export interface StoreComparisonData {
  store_name: string;
  order_count: number;
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  aov: number;  // 客单价
  avg_delivery_fee: number;
  avg_marketing_cost: number;
  delivery_cost_rate: number;
  marketing_cost_rate: number;
  ranks: {
    revenue_rank: number;
    profit_rank: number;
    profit_margin_rank: number;
  };
  anomalies?: StoreAnomaly[];  // 异常检测
}

/** 门店异常信息 */
export interface StoreAnomaly {
  type: 'low_profit_margin' | 'low_order_count' | 'high_marketing_cost' | 'high_delivery_cost';
  message: string;
  severity: 'high' | 'medium' | 'low';
}

/** 门店对比汇总数据 */
export interface StoreComparisonSummary {
  total_stores: number;
  total_orders: number;
  total_revenue: number;
  total_profit: number;
  avg_profit_margin: number;
  weighted_profit_margin?: number;  // 加权平均利润率
}

/** 门店对比响应 */
export interface StoreComparisonResponse {
  stores: StoreComparisonData[];
  summary: StoreComparisonSummary;
}

/** 门店环比数据 */
export interface StoreWeekOverWeekData {
  store_name: string;
  current: {
    order_count: number;
    total_revenue: number;
    total_profit: number;
    profit_margin: number;
    aov: number;
    avg_delivery_fee: number;
    avg_marketing_cost: number;
    delivery_cost_rate: number;
    marketing_cost_rate: number;
  };
  changes: {
    order_count: number;  // 百分比
    revenue: number;      // 百分比
    profit: number;       // 百分比
    profit_margin: number; // 百分点
    aov: number;          // 百分比
    avg_delivery_fee: number;  // 百分比
    avg_marketing_cost: number; // 百分比
    delivery_cost_rate: number; // 百分点
    marketing_cost_rate: number; // 百分点
  };
}

/** 门店环比响应 */
export interface StoreWeekOverWeekResponse {
  stores: StoreWeekOverWeekData[];
  period: {
    current: { start: string; end: string };
    previous: { start: string; end: string };
  };
}

/** 门店排行榜数据 */
export interface StoreRankingData {
  rank: number;
  store_name: string;
  value: number;
  order_count: number;
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
}


// ==================== 全局门店洞察分析 ====================

/** 统计指标 */
export interface StatisticsMetric {
  mean: number;
  median: number;
  std: number;
  p25?: number;
  p50?: number;
  p75?: number;
  p90?: number;
}

/** 整体概况洞察 */
export interface OverviewInsight {
  total_stores: number;
  total_orders: number;
  total_revenue: number;
  total_profit: number;
  weighted_profit_margin: number;
  statistics: {
    profit_margin: StatisticsMetric;
    aov: StatisticsMetric;
    order_count: StatisticsMetric;
  };
  summary_text: string;
}

/** 门店分群数据 */
export interface ClusterGroup {
  count: number;
  percentage: number;
  avg_metrics: {
    revenue: number;
    profit: number;
    profit_margin: number;
    aov: number;
  };
  top_stores: string[];
  characteristics: string;
}

/** 门店分群洞察 */
export interface ClusteringInsight {
  high_performance: ClusterGroup;
  medium_performance: ClusterGroup;
  low_performance: ClusterGroup;
  summary_text: string;
}

/** 异常门店信息 */
export interface AnomalyStoreInfo {
  store_name: string;
  value: number;
  threshold: number;
  severity: 'high' | 'medium' | 'low';
  message: string;
}

/** 异常检测洞察 */
export interface AnomalyInsight {
  total_anomaly_stores: number;
  by_type: {
    low_profit_margin: AnomalyStoreInfo[];
    low_order_count: AnomalyStoreInfo[];
    high_marketing_cost: AnomalyStoreInfo[];
    high_delivery_cost: AnomalyStoreInfo[];
  };
  summary_text: string;
}

/** 门店指标（用于头尾对比） */
export interface StoreMetricsForComparison {
  store_name: string;
  order_count: number;
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  aov: number;
  marketing_cost_rate: number;
  delivery_cost_rate: number;
}

/** 头尾对比洞察 */
export interface HeadTailInsight {
  top_stores: StoreMetricsForComparison[];
  bottom_stores: StoreMetricsForComparison[];
  differences: {
    profit_margin_gap: number;
    aov_gap: number;
    marketing_cost_rate_gap: number;
    delivery_cost_rate_gap: number;
  };
  top_characteristics: string;
  bottom_issues: string;
  summary_text: string;
}

/** 归因分析洞察 */
export interface AttributionInsight {
  correlations: {
    aov_correlation: number;
    marketing_cost_correlation: number;
    delivery_cost_correlation: number;
  };
  primary_factor: string;
  summary_text: string;
}

/** 趋势门店信息 */
export interface TrendStoreInfo {
  store_name: string;
  change_rate: number;
  current_value: number;
  previous_value: number;
}

/** 趋势分析洞察 */
export interface TrendInsight {
  growing_stores: {
    count: number;
    percentage: number;
    top3: TrendStoreInfo[];
  };
  declining_stores: {
    count: number;
    percentage: number;
    top3: TrendStoreInfo[];
  };
  summary_text: string;
}

/** 策略建议 */
export interface Recommendation {
  priority: 'urgent' | 'important' | 'general';
  category: string;
  title: string;
  description: string;
  action_items: string[];
  affected_stores: string[];
}

/** 策略建议洞察 */
export interface RecommendationInsight {
  urgent: Recommendation[];
  important: Recommendation[];
  general: Recommendation[];
  summary_text: string;
}

/** 门店健康度评分 */
export interface StoreHealthScore {
  store_name: string;
  health_score: number;
  pm_score: number;
  oc_score: number;
  mc_score: number;
  dc_score: number;
}

/** 健康度分布 */
export interface HealthDistribution {
  excellent: { count: number; percentage: number };
  good: { count: number; percentage: number };
  average: { count: number; percentage: number };
  poor: { count: number; percentage: number };
}

/** 健康度评分洞察 */
export interface HealthScoresInsight {
  scores: StoreHealthScore[];
  distribution: HealthDistribution;
  top_stores: StoreHealthScore[];
  bottom_stores: StoreHealthScore[];
  avg_score: number;
  summary_text: string;
}

/** 成本率统计 */
export interface CostRateStats {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
}

/** 成本结构洞察 */
export interface CostStructureInsight {
  totals: {
    marketing_cost: number;
    delivery_cost: number;
    marketing_ratio: number;
    delivery_ratio: number;
  };
  marketing_rate_stats: CostRateStats;
  delivery_rate_stats: CostRateStats;
  anomaly_stores: {
    high_marketing: string[];
    high_delivery: string[];
  };
  performance_comparison: {
    high_performance: { avg_marketing_rate: number; avg_delivery_rate: number };
    low_performance: { avg_marketing_rate: number; avg_delivery_rate: number };
  };
  summary_text: string;
}

/** 全局门店洞察数据 */
export interface GlobalInsightsData {
  overview: OverviewInsight;
  clustering: ClusteringInsight;
  anomalies: AnomalyInsight;
  head_tail_comparison: HeadTailInsight;
  attribution: AttributionInsight;
  trends: TrendInsight;
  health_scores: HealthScoresInsight;
  cost_structure: CostStructureInsight;
  recommendations: RecommendationInsight;
  generated_at: string;
}

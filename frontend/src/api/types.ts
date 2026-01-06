/**
 * API 类型定义
 * 与后端 Pydantic Schema 保持一致
 */

// ==========================================
// 通用类型
// ==========================================
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface DateRange {
  start_date: string
  end_date: string
}

// ==========================================
// 订单相关
// ==========================================
export interface Order {
  order_id: string
  order_date: string
  store_name: string
  platform: string
  product_name: string
  quantity: number
  unit_price: number
  total_amount: number
  cost: number
  profit: number
  profit_rate: number
  delivery_fee: number
  platform_fee: number
  customer_id?: string
}

export interface OrderSummary {
  total_orders: number
  total_amount: number
  total_profit: number
  avg_order_value: number
  profit_rate: number
  order_trend: TrendData[]
}

export interface TrendData {
  date: string
  value: number
  label?: string
}

// ==========================================
// 诊断分析（今日必做）
// ==========================================
export interface DiagnosisSummary {
  urgent_count: number
  watch_count: number
  highlight_count: number
  total_loss: number
  check_time: string
  urgent_issues: UrgentIssue[]
  watch_issues: WatchIssue[]
  highlights: Highlight[]
}

export interface UrgentIssue {
  id: string
  type: 'overflow' | 'high_delivery' | 'stockout' | 'abnormal_loss'
  title: string
  description: string
  loss_amount: number
  affected_count: number
  severity: 'critical' | 'high' | 'medium'
  suggestions: string[]
}

export interface WatchIssue {
  id: string
  type: 'traffic_drop' | 'slow_moving' | 'price_abnormal' | 'review_warning'
  title: string
  description: string
  metric_value: number
  threshold: number
  trend: 'up' | 'down' | 'stable'
}

export interface Highlight {
  id: string
  type: 'hot_product' | 'high_profit' | 'new_customer' | 'repeat_order'
  title: string
  description: string
  metric_value: number
  growth_rate: number
}

// 穿底订单详情
export interface OverflowOrder {
  order_id: string
  order_date: string
  store_name: string
  platform: string
  product_name: string
  quantity: number
  unit_price: number
  total_amount: number
  cost: number
  profit: number
  profit_rate: number
  overflow_reason: string
  loss_breakdown: LossBreakdown
}

export interface LossBreakdown {
  product_loss: number
  delivery_loss: number
  platform_loss: number
  promo_loss: number
}

// ==========================================
// 商品分析
// ==========================================
export interface Product {
  product_id: string
  product_name: string
  category: string
  unit_price: number
  cost: number
  stock: number
  sales_count: number
  revenue: number
  profit: number
  profit_rate: number
}

export interface ProductAnalysis {
  top_sellers: Product[]
  slow_moving: Product[]
  high_profit: Product[]
  low_profit: Product[]
  category_analysis: CategoryAnalysis[]
}

export interface CategoryAnalysis {
  category: string
  product_count: number
  total_sales: number
  total_revenue: number
  total_profit: number
  avg_profit_rate: number
}

// ==========================================
// 时段场景分析
// ==========================================
export interface SceneAnalysis {
  hourly_distribution: HourlyData[]
  day_of_week: DayOfWeekData[]
  platform_comparison: PlatformData[]
  scene_tags: SceneTag[]
}

export interface HourlyData {
  hour: number
  order_count: number
  revenue: number
  avg_order_value: number
}

export interface DayOfWeekData {
  day: number
  day_name: string
  order_count: number
  revenue: number
}

export interface PlatformData {
  platform: string
  order_count: number
  revenue: number
  profit: number
  profit_rate: number
  avg_order_value: number
}

export interface SceneTag {
  tag_id: string
  tag_name: string
  description: string
  order_count: number
  revenue_contribution: number
}

// ==========================================
// 客户分析
// ==========================================
export interface CustomerChurnAnalysis {
  total_customers: number
  active_customers: number
  churned_customers: number
  churn_rate: number
  at_risk_customers: AtRiskCustomer[]
  churn_reasons: ChurnReason[]
}

export interface AtRiskCustomer {
  customer_id: string
  last_order_date: string
  total_orders: number
  total_spent: number
  days_since_last_order: number
  risk_score: number
  suggested_action: string
}

export interface ChurnReason {
  reason: string
  percentage: number
  customer_count: number
}

// ==========================================
// 数据管理
// ==========================================
export interface DataUploadResult {
  success: boolean
  file_name: string
  rows_processed: number
  rows_inserted: number
  rows_updated: number
  errors: string[]
  upload_time: string
}

export interface DataStats {
  total_orders: number
  total_products: number
  total_stores: number
  date_range: DateRange | null
  data_freshness: string
  database_status: string
  redis_status: string
}

// ==========================================
// 系统监控
// ==========================================
export interface SystemStats {
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  active_connections: number
  cache_hit_rate: number
  avg_response_time: number
  uptime: string
}

export interface CacheStats {
  l1_hit_rate: number
  l2_hit_rate: number
  l3_hit_rate: number
  l4_hit_rate: number
  total_keys: number
  memory_used: string
}


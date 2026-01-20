/**
 * 订单数据概览 API
 * 
 * 与老版本Tab1完全一致的接口
 */
import { request } from './index'

// ==================== 类型定义 ====================

export interface OrderOverview {
  total_orders: number
  total_actual_sales: number
  total_profit: number
  avg_order_value: number
  profit_rate: number
  active_products: number
}

export interface ChannelStats {
  channel: string
  order_count: number
  amount: number
  profit: number
  order_ratio: number
  amount_ratio: number
  avg_value: number
  profit_rate: number
}

export interface TrendData {
  dates: string[]
  order_counts: number[]
  amounts: number[]
  profits: number[]
  avg_values: number[]
}

export interface OrderListItem {
  order_id: string
  order_date: string
  store_name: string
  channel: string
  amount: number
  profit: number
  profit_rate: number
}

export interface ProfitDistribution {
  labels: string[]
  counts: number[]
  colors: string[]
  total_orders: number
}

// 客单价区间分布
export interface PriceRangeItem {
  label: string
  count: number
  ratio: number
  color: string
}

export interface BusinessZone {
  label: string
  count: number
  ratio: number
}

export interface PriceDistribution {
  price_ranges: PriceRangeItem[]
  business_zones: {
    flow_zone: BusinessZone
    main_zone: BusinessZone
    profit_zone: BusinessZone
    high_zone: BusinessZone
  }
  avg_basket_depth: number
  total_orders: number
  avg_order_value: number
}

// 一级分类趋势
export interface CategoryTrendSeries {
  name: string
  data: number[]
  color: string
}

export interface CategoryTrend {
  categories: string[]
  weeks: string[]
  series: CategoryTrendSeries[]
}

// 环比数据
export interface PeriodMetrics {
  order_count: number
  total_sales: number
  total_profit: number
  avg_order_value: number
  profit_rate: number
  active_products: number
}

export interface ComparisonData {
  current: PeriodMetrics
  previous: PeriodMetrics
  changes: {
    order_count: number
    total_sales: number
    total_profit: number
    avg_order_value: number
    profit_rate: number
    active_products: number
  }
  period: {
    current_start: string
    current_end: string
    previous_start: string
    previous_end: string
    period_days: number
  }
}

// 渠道环比
export interface ChannelMetrics {
  order_count: number
  amount: number
  profit: number
  avg_value: number
  profit_rate: number
  // 成本结构
  product_cost: number
  product_cost_rate: number
  consumable_cost: number
  consumable_cost_rate: number
  product_discount: number
  product_discount_rate: number
  activity_subsidy: number
  activity_subsidy_rate: number
  delivery_cost: number
  delivery_cost_rate: number
  platform_fee: number
  platform_fee_rate: number
  total_cost_rate: number
  // 单均经济
  avg_profit_per_order: number
  avg_marketing_per_order: number
  avg_delivery_per_order: number
}

export interface ChannelComparison {
  channel: string
  current: ChannelMetrics
  previous: ChannelMetrics | null
  changes: {
    order_count: number | null
    amount: number | null
    profit: number | null
    avg_value: number | null
    profit_rate: number | null
  }
  rating: '优秀' | '良好' | '需改进'
}

// 异常诊断
export interface LowProfitOrder {
  order_id: string
  amount: number
  profit: number
  profit_rate: number
  channel: string
}

export interface HighDeliveryOrder {
  order_id: string
  amount: number
  delivery_cost: number
  delivery_ratio: number
  channel: string
}

export interface NegativeProfitOrder {
  order_id: string
  amount: number
  profit: number
  loss: number
  channel: string
}

export interface AnomalySummary {
  total_orders: number
  low_profit_count: number
  low_profit_ratio: number
  high_delivery_count: number
  high_delivery_ratio: number
  negative_profit_count: number
  negative_profit_ratio: number
  total_loss: number
}

export interface AnomalyDetection {
  low_profit: LowProfitOrder[]
  high_delivery: HighDeliveryOrder[]
  negative_profit: NegativeProfitOrder[]
  summary: AnomalySummary
}

export interface OrderQueryParams {
  page?: number
  page_size?: number
  start_date?: string
  end_date?: string
  store_name?: string
  channel?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// ==================== API 方法 ====================

export const orderApi = {
  /**
   * 获取订单概览（六大核心卡片）
   */
  getOverview(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: OrderOverview }> {
    return request.get('/orders/overview', { params })
  },
  
  /**
   * 获取渠道表现对比
   */
  getChannelStats(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: ChannelStats[] }> {
    return request.get('/orders/channels', { params })
  },
  
  /**
   * 获取订单趋势数据
   */
  getTrend(params: {
    days?: number
    store_name?: string
    granularity?: 'day' | 'week' | 'month'
  }): Promise<{ success: boolean; data: TrendData }> {
    return request.get('/orders/trend', { params })
  },
  
  /**
   * 获取订单列表
   */
  getList(params: OrderQueryParams): Promise<{
    success: boolean
    data: OrderListItem[]
    total: number
    page: number
    page_size: number
    total_pages: number
  }> {
    return request.get('/orders/list', { params })
  },
  
  /**
   * 获取门店列表
   */
  getStores(): Promise<{ success: boolean; data: string[] }> {
    return request.get('/orders/stores')
  },
  
  /**
   * 获取渠道列表
   */
  getChannels(): Promise<{ success: boolean; data: string[] }> {
    return request.get('/orders/channel-list')
  },
  
  /**
   * 获取利润区间分布
   */
  getProfitDistribution(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: ProfitDistribution }> {
    return request.get('/orders/profit-distribution', { params })
  },
  
  /**
   * 获取客单价区间分布（新增）
   */
  getPriceDistribution(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: PriceDistribution }> {
    return request.get('/orders/price-distribution', { params })
  },
  
  /**
   * 获取一级分类销售趋势（新增）
   */
  getCategoryTrend(params?: {
    store_name?: string
    channel?: string
    weeks?: number
  }): Promise<{ success: boolean; data: CategoryTrend }> {
    return request.get('/orders/category-trend', { params })
  },
  
  /**
   * 获取环比数据（新增）
   */
  getComparison(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: ComparisonData }> {
    return request.get('/orders/comparison', { params })
  },
  
  /**
   * 获取渠道环比对比（新增）
   */
  getChannelComparison(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: ChannelComparison[] }> {
    return request.get('/orders/channel-comparison', { params })
  },
  
  /**
   * 获取异常诊断数据（新增）
   */
  getAnomalyDetection(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; data: AnomalyDetection }> {
    return request.get('/orders/anomaly-detection', { params })
  },
  
  /**
   * 导出订单数据
   */
  exportOrders(params: OrderQueryParams): Promise<Blob> {
    return request.get('/orders/export', {
      params,
      responseType: 'blob'
    })
  }
}

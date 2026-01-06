/**
 * 诊断分析 API（今日必做核心）
 */
import { request } from './index'
import type { 
  DiagnosisSummary, 
  OverflowOrder, 
  CustomerChurnAnalysis,
  PaginatedResponse 
} from './types'

export interface DiagnosisParams {
  store_name?: string
  start_date?: string
  end_date?: string
}

export const diagnosisApi = {
  /**
   * 获取诊断汇总
   */
  getSummary(params?: DiagnosisParams): Promise<DiagnosisSummary> {
    return request.get('/diagnosis/summary', { params })
  },
  
  /**
   * 获取紧急问题列表
   */
  getUrgentIssues(params?: DiagnosisParams): Promise<{
    overflow_orders: OverflowOrder[]
    high_delivery_orders: unknown[]
    stockout_products: unknown[]
  }> {
    return request.get('/diagnosis/urgent', { params })
  },
  
  /**
   * 获取穿底订单详情
   */
  getOverflowOrders(params?: {
    page?: number
    page_size?: number
    store_name?: string
    start_date?: string
    end_date?: string
    min_loss?: number
  }): Promise<PaginatedResponse<OverflowOrder>> {
    return request.get('/diagnosis/overflow-orders', { params })
  },
  
  /**
   * 获取客户流失分析
   */
  getCustomerChurn(params?: {
    store_name?: string
    days_threshold?: number
  }): Promise<CustomerChurnAnalysis> {
    return request.get('/diagnosis/customer-churn', { params })
  },
  
  /**
   * 获取客单价异常
   */
  getAovAnomaly(params?: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{
    avg_aov: number
    anomaly_orders: unknown[]
    aov_distribution: { range: string; count: number }[]
  }> {
    return request.get('/diagnosis/aov-anomaly', { params })
  },
  
  /**
   * 获取配送费异常
   */
  getDeliveryAnomaly(params?: {
    store_name?: string
    threshold_rate?: number
  }): Promise<{
    avg_delivery_rate: number
    high_delivery_orders: unknown[]
    delivery_distribution: unknown[]
  }> {
    return request.get('/diagnosis/delivery-anomaly', { params })
  },
  
  /**
   * 获取关注问题
   */
  getWatchIssues(params?: DiagnosisParams): Promise<{
    traffic_drop: unknown[]
    slow_moving: unknown[]
    price_abnormal: unknown[]
  }> {
    return request.get('/diagnosis/watch', { params })
  },
  
  /**
   * 获取亮点表现
   */
  getHighlights(params?: DiagnosisParams): Promise<{
    hot_products: unknown[]
    high_profit_orders: unknown[]
    new_customers: unknown[]
  }> {
    return request.get('/diagnosis/highlights', { params })
  }
}


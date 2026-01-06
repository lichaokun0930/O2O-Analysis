/**
 * 商品 API
 */
import { request } from './index'
import type { Product, ProductAnalysis, CategoryAnalysis, PaginatedResponse } from './types'

export interface ProductQueryParams {
  page?: number
  page_size?: number
  category?: string
  keyword?: string
  min_profit_rate?: number
  max_profit_rate?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export const productApi = {
  /**
   * 获取商品列表
   */
  getProducts(params?: ProductQueryParams): Promise<PaginatedResponse<Product>> {
    return request.get('/products', { params })
  },
  
  /**
   * 获取商品分析汇总
   */
  getAnalysis(params?: {
    start_date?: string
    end_date?: string
    store_name?: string
  }): Promise<ProductAnalysis> {
    return request.get('/products/analysis', { params })
  },
  
  /**
   * 获取分类分析
   */
  getCategoryAnalysis(params?: {
    start_date?: string
    end_date?: string
  }): Promise<CategoryAnalysis[]> {
    return request.get('/products/category-analysis', { params })
  },
  
  /**
   * 获取畅销商品
   */
  getTopSellers(params?: {
    limit?: number
    start_date?: string
    end_date?: string
  }): Promise<Product[]> {
    return request.get('/products/top-sellers', { params })
  },
  
  /**
   * 获取滞销商品
   */
  getSlowMoving(params?: {
    days?: number
    threshold?: number
  }): Promise<Product[]> {
    return request.get('/products/slow-moving', { params })
  },
  
  /**
   * 获取高利润商品
   */
  getHighProfit(params?: {
    min_profit_rate?: number
    limit?: number
  }): Promise<Product[]> {
    return request.get('/products/high-profit', { params })
  },
  
  /**
   * 获取低利润商品（需要优化）
   */
  getLowProfit(params?: {
    max_profit_rate?: number
    limit?: number
  }): Promise<Product[]> {
    return request.get('/products/low-profit', { params })
  }
}


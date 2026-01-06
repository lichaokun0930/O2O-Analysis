/**
 * 数据管理 API - 完整版
 * 
 * 对标老版本 Dash 数据管理功能
 */
import { request } from './index'
import type { DataUploadResult, DataStats } from './types'

export interface Store {
  label: string
  value: string
  order_count: number
}

export interface CacheStats {
  enabled: boolean
  levels: {
    [key: string]: {
      name: string
      ttl: number
      status: string
    }
  }
  total_keys: number
  memory_usage: string
}

export interface StoreStats {
  store_name: string
  order_count: number
  date_range: {
    start: string | null
    end: string | null
  }
}

export interface DatabaseStatus {
  connected: boolean
  message?: string
  hint?: string
  order_count?: number
}

export const dataApi = {
  /**
   * 获取数据统计信息
   */
  getStats(): Promise<DataStats> {
    return request.get('/data/stats')
  },
  
  /**
   * 获取数据库状态
   */
  getDatabaseStatus(): Promise<DatabaseStatus> {
    return request.get('/data/database/status')
  },
  
  /**
   * 获取门店列表
   */
  getStores(): Promise<{ success: boolean; data: Store[]; message?: string }> {
    return request.get('/data/stores')
  },
  
  /**
   * 从数据库加载数据
   */
  loadFromDatabase(params: {
    store_name?: string
    start_date?: string
    end_date?: string
  }): Promise<{ success: boolean; message: string; data: any }> {
    return request.post('/data/database/load', null, { params })
  },
  
  /**
   * 上传订单数据
   */
  uploadOrders(file: File, options?: {
    mode?: 'append' | 'replace'
  }): Promise<DataUploadResult> {
    const formData = new FormData()
    formData.append('file', file)
    
    const params = new URLSearchParams()
    if (options?.mode) {
      params.append('mode', options.mode)
    }
    
    return request.post(`/data/upload/orders?${params.toString()}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  /**
   * 上传商品数据
   */
  uploadProducts(file: File): Promise<DataUploadResult> {
    const formData = new FormData()
    formData.append('file', file)
    
    return request.post('/data/upload/products', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  /**
   * 获取缓存统计
   */
  getCacheStats(): Promise<CacheStats> {
    return request.get('/data/cache/stats')
  },
  
  /**
   * 清除缓存
   */
  clearCache(level?: 1 | 2 | 3 | 4): Promise<{ success: boolean; message: string }> {
    return request.post('/data/clear-cache', { level })
  },
  
  /**
   * 重建缓存
   */
  rebuildCache(): Promise<{ success: boolean; message: string }> {
    return request.post('/data/rebuild-cache')
  },
  
  /**
   * 获取上传历史
   */
  getUploadHistory(params?: {
    page?: number
    page_size?: number
  }): Promise<{
    items: {
      id: string
      file_name: string
      upload_time: string
      status: 'success' | 'failed' | 'partial'
      rows_processed: number
      errors: string[]
    }[]
    total: number
  }> {
    return request.get('/data/upload-history', { params })
  },
  
  /**
   * 数据验证
   */
  validateData(): Promise<{
    is_valid: boolean
    issues: {
      type: string
      description: string
      affected_records: number
    }[]
  }> {
    return request.get('/data/validate')
  },
  
  /**
   * 导出数据
   */
  exportData(params: {
    type: 'orders' | 'products' | 'all'
    format: 'csv' | 'excel'
    date_range?: {
      start_date: string
      end_date: string
    }
  }): Promise<Blob> {
    return request.post('/data/export', params, {
      responseType: 'blob'
    })
  },
  
  /**
   * 获取门店数据统计
   */
  getStoreStats(storeName: string): Promise<StoreStats> {
    return request.get(`/data/store/${encodeURIComponent(storeName)}/stats`)
  },
  
  /**
   * 删除门店数据
   */
  deleteStoreData(storeName: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/data/store/${encodeURIComponent(storeName)}`)
  },
  
  /**
   * 优化数据库
   */
  optimizeDatabase(): Promise<{ success: boolean; message: string }> {
    return request.post('/data/database/optimize')
  }
}

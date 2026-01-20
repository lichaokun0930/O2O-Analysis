/**
 * 数据管理 API
 */
import request from './index';

export interface Store {
  label: string;
  value: string;
  order_count: number;
}

export interface DataStats {
  total_orders: number;
  total_stores: number;
  total_products: number;
  data_freshness: string;
  database_status: string;
  redis_status: string;
}

export interface StoreStats {
  store_name: string;
  order_count: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
}

export interface DataUploadResult {
  success: boolean;
  message: string;
  rows_inserted: number;
  errors?: string[];
}

export const dataApi = {
  // 获取数据统计信息
  getStats(): Promise<DataStats> {
    return request.get('/data/stats');
  },

  // 获取门店列表
  getStores(): Promise<{ success: boolean; data: Store[]; message?: string }> {
    return request.get('/data/stores');
  },

  // 从数据库加载数据
  loadFromDatabase(params: {
    store_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{ success: boolean; message: string; data: any }> {
    return request.post('/data/database/load', null, { params });
  },

  // 上传订单数据
  uploadOrders(file: File, options?: { mode?: 'append' | 'replace' }): Promise<DataUploadResult> {
    const formData = new FormData();
    formData.append('file', file);
    const params = new URLSearchParams();
    if (options?.mode) params.append('mode', options.mode);
    // 使用原生 fetch 避免 axios 默认 headers 干扰 multipart/form-data
    return fetch(`/api/v1/data/upload/orders?${params.toString()}`, {
      method: 'POST',
      body: formData,
    }).then(async (res) => {
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || '上传失败');
      }
      return data;
    });
  },

  // 获取门店数据统计
  getStoreStats(storeName: string): Promise<StoreStats> {
    return request.get(`/data/store/${encodeURIComponent(storeName)}/stats`);
  },

  // 删除门店数据
  deleteStoreData(storeName: string): Promise<{ success: boolean; message: string }> {
    return request.delete(`/data/store/${encodeURIComponent(storeName)}`);
  },

  // 清除缓存
  clearCache(level?: 1 | 2 | 3 | 4): Promise<{ success: boolean; message: string }> {
    return request.post('/data/clear-cache', { level });
  },

  // 优化数据库
  optimizeDatabase(): Promise<{ success: boolean; message: string }> {
    return request.post('/data/database/optimize');
  },
};

/**
 * 品类效益矩阵 API
 * 
 * 获取真实的品类销售数据（与Dash版本一致）
 */

import { apiClient } from './index';
import { CategoryMetric } from '@/types';

export interface CategoryMatrixParams {
  store_name?: string;
  parent_category?: string;
  channel?: string;
  start_date?: string;
  end_date?: string;
}

export interface CategoryMatrixResponse {
  success: boolean;
  data: CategoryMetric[];
  level: 'l1' | 'l3';
  parent?: string;
  total: number;
  error?: string;
}

export const categoryMatrixApi = {
  /**
   * 获取品类效益数据（含库存风险）
   * 
   * @param params.store_name 门店名称
   * @param params.parent_category 父级分类（用于下钻到三级分类）
   * @param params.channel 渠道筛选
   */
  async getPerformanceWithRisk(params: CategoryMatrixParams): Promise<CategoryMatrixResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.store_name) {
      queryParams.append('store_name', params.store_name);
    }
    if (params.parent_category) {
      queryParams.append('parent_category', params.parent_category);
    }
    if (params.channel) {
      queryParams.append('channel', params.channel);
    }
    
    const url = `/category-matrix/with-risk${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await apiClient.get<CategoryMatrixResponse>(url);
    return response.data;
  },

  /**
   * 获取品类效益数据（不含库存风险）
   */
  async getPerformance(params: CategoryMatrixParams): Promise<CategoryMatrixResponse> {
    const queryParams = new URLSearchParams();
    
    if (params.store_name) {
      queryParams.append('store_name', params.store_name);
    }
    if (params.parent_category) {
      queryParams.append('parent_category', params.parent_category);
    }
    if (params.channel) {
      queryParams.append('channel', params.channel);
    }
    if (params.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params.end_date) {
      queryParams.append('end_date', params.end_date);
    }
    
    const url = `/category-matrix/performance${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const response = await apiClient.get<CategoryMatrixResponse>(url);
    return response.data;
  }
};

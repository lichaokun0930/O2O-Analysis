/**
 * 库存风险分析 API
 * 
 * 与 Dash 版本完全一致的计算逻辑
 */

import { apiClient } from './index';
import { SkuRiskMetric } from '@/types';

export interface CategoryRiskStats {
  category: string;
  soldOutCount: number;
  slowMovingCount: number;
  inventoryTurnover: number;
  slowMovingDetail?: {
    light: number;
    medium: number;
    heavy: number;
    critical: number;
    total: number;
  };
}

export interface InventoryRiskSummary {
  sold_out: {
    total: number;
    products: SkuRiskMetric[];
    by_category: Record<string, number>;
  };
  slow_moving: {
    total: number;
    by_severity: {
      light: number;
      medium: number;
      heavy: number;
      critical: number;
    };
    products: SkuRiskMetric[];
    by_category: Record<string, { light: number; medium: number; heavy: number; critical: number; total: number }>;
  };
  by_category: CategoryRiskStats[];
  turnover: Record<string, number>;
}

// 🆕 趋势数据类型（重构版本）
export interface InventoryRiskTrendItem {
  date: string;
  // 售罄
  soldOutCount: number;
  soldOutRate: number;
  // 滞销（总计）
  slowMovingCount: number;
  slowMovingRate: number;
  // 滞销（分级）- 动态等级
  slowMovingByLevel: Record<string, number>;
  slowMovingRateByLevel: Record<string, number>;
  // 基数
  totalSku: number;
  totalSkuWithStock: number;
}

export interface InventoryRiskTrendResponse {
  success: boolean;
  data: InventoryRiskTrendItem[];
  // 🆕 自适应等级
  availableLevels: string[];  // ['light', 'medium'] 或 ['light', 'medium', 'heavy']
  trendStartDate: string;
  dateRange: {
    start: string;
    end: string;
  };
  totalDataDays: number;
  // 🆕 变化摘要
  changeSummary?: {
    soldOutRateChange: number;
    slowMovingRateChange: number;
    periodDays: number;
  };
  levelDefinitions: Record<string, string>;
  message?: string;
}

// 🆕 售罄分析数据类型
export interface SoldOutAnalysis {
  soldOutCount: number;
  estimatedLoss: number;
  byCategory: Array<{
    category: string;
    count: number;
    loss: number;
  }>;
  frequentSoldOut: Array<{
    name: string;
    times: number;
    avgRecoveryDays: number;
    category: string;
  }>;
  avgRecoveryDays: number;
}

export interface SoldOutAnalysisResponse {
  success: boolean;
  data: SoldOutAnalysis;
  period?: {
    start: string;
    end: string;
    days: number;
  };
  message?: string;
}

export const inventoryRiskApi = {
  /**
   * 获取库存风险汇总（与Dash版本一致）
   */
  getSummary: async (storeName?: string, category?: string): Promise<InventoryRiskSummary> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    if (category) params.append('category', category);
    
    const response = await apiClient.get(`/inventory-risk/summary?${params.toString()}`);
    return response.data.data;
  },

  /**
   * 获取售罄品列表
   * 售罄品定义: 库存=0 且 近7天有销量
   */
  getSoldOutProducts: async (
    storeName?: string,
    category?: string,
    page = 1,
    pageSize = 20
  ): Promise<{ data: SkuRiskMetric[]; total: number }> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    if (category) params.append('category', category);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const response = await apiClient.get(`/inventory-risk/sold-out?${params.toString()}`);
    return { data: response.data.data, total: response.data.total };
  },

  /**
   * 获取滞销品列表
   * 滞销品分级（与Dash版本一致）:
   * - light: 滞销天数 == 7
   * - medium: 滞销天数 8-15
   * - heavy: 滞销天数 16-30
   * - critical: 滞销天数 > 30
   */
  getSlowMovingProducts: async (
    storeName?: string,
    category?: string,
    severity?: 'light' | 'medium' | 'heavy' | 'critical',
    page = 1,
    pageSize = 20
  ): Promise<{ data: SkuRiskMetric[]; total: number; by_severity: Record<string, number> }> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    if (category) params.append('category', category);
    if (severity) params.append('severity', severity);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const response = await apiClient.get(`/inventory-risk/slow-moving?${params.toString()}`);
    return {
      data: response.data.data,
      total: response.data.total,
      by_severity: response.data.by_severity
    };
  },

  /**
   * 获取按分类的库存风险统计（与Dash版本一致）
   */
  getCategoryRiskStats: async (storeName?: string): Promise<CategoryRiskStats[]> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    
    const response = await apiClient.get(`/inventory-risk/category-risk?${params.toString()}`);
    return response.data.data;
  },

  /**
   * 获取库存风险趋势数据（售罄趋势 + 滞销趋势）
   */
  getRiskTrend: async (
    storeName?: string,
    category?: string,
    days = 30
  ): Promise<InventoryRiskTrendResponse> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    if (category) params.append('category', category);
    params.append('days', days.toString());
    
    const response = await apiClient.get(`/inventory-risk/trend?${params.toString()}`);
    return response.data;
  },

  /**
   * 获取售罄深度分析数据
   * 包含：售罄损失金额、品类分布、高频售罄品、恢复时间
   */
  getSoldOutAnalysis: async (
    storeName?: string,
    category?: string,
    days = 30
  ): Promise<SoldOutAnalysisResponse> => {
    const params = new URLSearchParams();
    if (storeName) params.append('store_name', storeName);
    if (category) params.append('category', category);
    params.append('days', days.toString());
    
    const response = await apiClient.get(`/inventory-risk/sold-out-analysis?${params.toString()}`);
    return response.data;
  }
};

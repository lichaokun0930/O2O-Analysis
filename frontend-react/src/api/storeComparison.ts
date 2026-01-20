/**
 * 全量门店对比分析 API
 */
import { apiClient } from './index';
import type { 
  StoreComparisonResponse, 
  StoreWeekOverWeekResponse,
  StoreRankingData,
  GlobalInsightsData
} from '../types';

export interface StoreComparisonParams {
  start_date?: string;
  end_date?: string;
  sort_by?: 'revenue' | 'profit' | 'profit_margin' | 'order_count';
  sort_order?: 'asc' | 'desc';
  channel?: string;
}

export interface StoreRankingParams {
  metric?: 'revenue' | 'profit' | 'profit_margin' | 'order_count';
  limit?: number;
  start_date?: string;
  end_date?: string;
}

export interface ExportParams {
  start_date?: string;
  end_date?: string;
  channel?: string;
  format?: 'json' | 'csv';
}

export const storeComparisonApi = {
  /**
   * 获取全量门店对比数据
   */
  getComparison: async (params?: StoreComparisonParams) => {
    const response = await apiClient.get<{ success: boolean; data: StoreComparisonResponse }>(
      '/stores/comparison',
      { params }
    );
    return response.data;
  },

  /**
   * 获取门店环比数据（支持自定义对比周期、渠道筛选）
   */
  getWeekOverWeek: async (
    end_date?: string, 
    previous_start?: string, 
    previous_end?: string, 
    channel?: string
  ) => {
    const response = await apiClient.get<{ success: boolean; data: StoreWeekOverWeekResponse }>(
      '/stores/comparison/week-over-week',
      { params: { end_date, previous_start, previous_end, channel } }
    );
    return response.data;
  },

  /**
   * 获取门店排行榜
   */
  getRanking: async (params?: StoreRankingParams) => {
    const response = await apiClient.get<{ success: boolean; data: StoreRankingData[] }>(
      '/stores/comparison/ranking',
      { params }
    );
    return response.data;
  },

  /**
   * 获取当前日期范围内有数据的渠道列表
   */
  getAvailableChannels: async (params?: { start_date?: string; end_date?: string }) => {
    const response = await apiClient.get<{ success: boolean; data: string[] }>(
      '/stores/comparison/available-channels',
      { params }
    );
    return response.data;
  },

  /**
   * 导出门店对比数据
   */
  exportData: async (params?: ExportParams) => {
    const response = await apiClient.get<{ 
      success: boolean; 
      data: {
        format: string;
        content: any;
        filename: string;
        summary?: any;
      }
    }>(
      '/stores/comparison/export',
      { params }
    );
    return response.data;
  },

  /**
   * 获取指定渠道下的门店列表
   */
  getStoresByChannel: async (params?: { start_date?: string; end_date?: string; channel?: string }) => {
    const response = await apiClient.get<{ success: boolean; data: string[]; count: number }>(
      '/stores/comparison/stores-by-channel',
      { params }
    );
    return response.data;
  },

  /**
   * 获取全局门店洞察分析
   */
  getGlobalInsights: async (params?: { 
    start_date?: string; 
    end_date?: string; 
    channel?: string;
    include_trends?: boolean;
  }) => {
    const response = await apiClient.get<{ success: boolean; data: GlobalInsightsData | null; message?: string }>(
      '/stores/comparison/global-insights',
      { params }
    );
    return response.data;
  }
};

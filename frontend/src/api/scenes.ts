/**
 * 时段场景分析 API
 */
import { request } from './index'
import type { 
  SceneAnalysis, 
  HourlyData, 
  DayOfWeekData, 
  PlatformData,
  SceneTag 
} from './types'

export interface SceneQueryParams {
  start_date?: string
  end_date?: string
  store_name?: string
  platform?: string
}

export const sceneApi = {
  /**
   * 获取场景分析汇总
   */
  getAnalysis(params?: SceneQueryParams): Promise<SceneAnalysis> {
    return request.get('/scenes/analysis', { params })
  },
  
  /**
   * 获取小时分布
   */
  getHourlyDistribution(params?: SceneQueryParams): Promise<HourlyData[]> {
    return request.get('/scenes/hourly', { params })
  },
  
  /**
   * 获取星期分布
   */
  getDayOfWeekDistribution(params?: SceneQueryParams): Promise<DayOfWeekData[]> {
    return request.get('/scenes/day-of-week', { params })
  },
  
  /**
   * 获取平台对比
   */
  getPlatformComparison(params?: SceneQueryParams): Promise<PlatformData[]> {
    return request.get('/scenes/platforms', { params })
  },
  
  /**
   * 获取场景标签
   */
  getSceneTags(params?: SceneQueryParams): Promise<SceneTag[]> {
    return request.get('/scenes/tags', { params })
  },
  
  /**
   * 获取热力图数据
   */
  getHeatmapData(params?: SceneQueryParams): Promise<{
    data: { hour: number; day: number; value: number }[]
  }> {
    return request.get('/scenes/heatmap', { params })
  },
  
  /**
   * 获取高峰时段分析
   */
  getPeakAnalysis(params?: SceneQueryParams): Promise<{
    peak_hours: number[]
    peak_days: number[]
    recommendations: string[]
  }> {
    return request.get('/scenes/peak-analysis', { params })
  }
}


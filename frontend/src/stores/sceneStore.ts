/**
 * 场景分析状态管理
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { sceneApi, type SceneQueryParams } from '@/api/scenes'
import type { 
  SceneAnalysis, 
  HourlyData, 
  DayOfWeekData, 
  PlatformData,
  SceneTag 
} from '@/api/types'

export const useSceneStore = defineStore('scene', () => {
  // State
  const analysis = ref<SceneAnalysis | null>(null)
  const hourlyData = ref<HourlyData[]>([])
  const dayOfWeekData = ref<DayOfWeekData[]>([])
  const platformData = ref<PlatformData[]>([])
  const sceneTags = ref<SceneTag[]>([])
  const heatmapData = ref<{ hour: number; day: number; value: number }[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const filters = ref<SceneQueryParams>({
    start_date: undefined,
    end_date: undefined,
    store_name: undefined,
    platform: undefined
  })
  
  // Actions
  async function fetchAnalysis(params?: SceneQueryParams) {
    loading.value = true
    error.value = null
    
    try {
      analysis.value = await sceneApi.getAnalysis({
        ...filters.value,
        ...params
      })
      
      // 同时填充子数据
      if (analysis.value) {
        hourlyData.value = analysis.value.hourly_distribution
        dayOfWeekData.value = analysis.value.day_of_week
        platformData.value = analysis.value.platform_comparison
        sceneTags.value = analysis.value.scene_tags
      }
    } catch (err) {
      error.value = '获取场景分析失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchHourlyDistribution(params?: SceneQueryParams) {
    try {
      hourlyData.value = await sceneApi.getHourlyDistribution({
        ...filters.value,
        ...params
      })
    } catch (err) {
      console.error('获取小时分布失败:', err)
    }
  }
  
  async function fetchDayOfWeekDistribution(params?: SceneQueryParams) {
    try {
      dayOfWeekData.value = await sceneApi.getDayOfWeekDistribution({
        ...filters.value,
        ...params
      })
    } catch (err) {
      console.error('获取星期分布失败:', err)
    }
  }
  
  async function fetchPlatformComparison(params?: SceneQueryParams) {
    try {
      platformData.value = await sceneApi.getPlatformComparison({
        ...filters.value,
        ...params
      })
    } catch (err) {
      console.error('获取平台对比失败:', err)
    }
  }
  
  async function fetchHeatmapData(params?: SceneQueryParams) {
    try {
      const response = await sceneApi.getHeatmapData({
        ...filters.value,
        ...params
      })
      heatmapData.value = response.data
    } catch (err) {
      console.error('获取热力图数据失败:', err)
    }
  }
  
  function setFilters(newFilters: Partial<SceneQueryParams>) {
    filters.value = { ...filters.value, ...newFilters }
  }
  
  function resetFilters() {
    filters.value = {
      start_date: undefined,
      end_date: undefined,
      store_name: undefined,
      platform: undefined
    }
  }
  
  // 刷新所有数据
  async function refreshAll() {
    await Promise.all([
      fetchAnalysis(),
      fetchHeatmapData()
    ])
  }
  
  return {
    // State
    analysis,
    hourlyData,
    dayOfWeekData,
    platformData,
    sceneTags,
    heatmapData,
    loading,
    error,
    filters,
    
    // Actions
    fetchAnalysis,
    fetchHourlyDistribution,
    fetchDayOfWeekDistribution,
    fetchPlatformComparison,
    fetchHeatmapData,
    setFilters,
    resetFilters,
    refreshAll
  }
})


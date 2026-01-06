/**
 * 数据管理状态 - 完整版
 * 
 * 对标老版本数据管理功能
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dataApi, type Store, type StoreStats, type CacheStats } from '@/api/data'
import type { DataStats, DataUploadResult } from '@/api/types'

export const useDataStore = defineStore('data', () => {
  // ==================== State ====================
  const stats = ref<DataStats | null>(null)
  const stores = ref<Store[]>([])
  const cacheStats = ref<CacheStats | null>(null)
  const uploadHistory = ref<{
    id: string
    file_name: string
    upload_time: string
    status: 'success' | 'failed' | 'partial'
    rows_processed: number
    errors: string[]
  }[]>([])
  const uploadHistoryTotal = ref(0)
  const lastUploadResult = ref<DataUploadResult | null>(null)
  const loading = ref(false)
  const uploading = ref(false)
  const error = ref<string | null>(null)
  
  // 数据库状态
  const databaseConnected = ref(false)
  const redisConnected = ref(false)
  
  // 当前数据源
  const currentDataSource = ref<'database' | 'upload' | null>('database')
  const currentStoreName = ref<string | null>(null)
  
  // ==================== Computed ====================
  const dataFreshness = computed(() => {
    if (!stats.value) return '未知'
    return stats.value.data_freshness
  })
  
  const hasData = computed(() => {
    return stats.value && stats.value.total_orders > 0
  })
  
  const databaseStatus = computed(() => {
    return stats.value?.database_status || '未连接'
  })
  
  const redisStatus = computed(() => {
    return stats.value?.redis_status || '未连接'
  })
  
  // ==================== Actions ====================
  
  /**
   * 获取数据统计
   */
  async function fetchStats() {
    loading.value = true
    error.value = null
    
    try {
      stats.value = await dataApi.getStats()
      databaseConnected.value = stats.value.database_status === '已连接'
      redisConnected.value = stats.value.redis_status === '已连接'
    } catch (err) {
      error.value = '获取数据统计失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取门店列表
   */
  async function fetchStores() {
    try {
      const res = await dataApi.getStores()
      if (res.success) {
        stores.value = res.data
      }
    } catch (err) {
      console.error('获取门店列表失败:', err)
    }
  }
  
  /**
   * 从数据库加载数据
   */
  async function loadFromDatabase(params: {
    store_name?: string
    start_date?: string
    end_date?: string
  }) {
    loading.value = true
    error.value = null
    
    try {
      const res = await dataApi.loadFromDatabase(params)
      if (res.success) {
        currentDataSource.value = 'database'
        currentStoreName.value = params.store_name || null
      }
      return res
    } catch (err) {
      error.value = '加载数据失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 上传订单数据
   */
  async function uploadOrders(file: File, mode: 'append' | 'replace' = 'replace') {
    uploading.value = true
    error.value = null
    
    try {
      lastUploadResult.value = await dataApi.uploadOrders(file, { mode })
      
      // 上传成功后刷新统计
      await fetchStats()
      await fetchStores()
      await fetchUploadHistory()
      
      return lastUploadResult.value
    } catch (err) {
      error.value = '上传订单数据失败'
      console.error(err)
      throw err
    } finally {
      uploading.value = false
    }
  }
  
  /**
   * 上传商品数据
   */
  async function uploadProducts(file: File) {
    uploading.value = true
    error.value = null
    
    try {
      lastUploadResult.value = await dataApi.uploadProducts(file)
      
      // 上传成功后刷新统计
      await fetchStats()
      await fetchUploadHistory()
      
      return lastUploadResult.value
    } catch (err) {
      error.value = '上传商品数据失败'
      console.error(err)
      throw err
    } finally {
      uploading.value = false
    }
  }
  
  /**
   * 获取上传历史
   */
  async function fetchUploadHistory(params?: { page?: number; page_size?: number }) {
    try {
      const response = await dataApi.getUploadHistory(params)
      uploadHistory.value = response.items
      uploadHistoryTotal.value = response.total
    } catch (err) {
      console.error('获取上传历史失败:', err)
    }
  }
  
  /**
   * 获取缓存统计
   */
  async function fetchCacheStats() {
    try {
      cacheStats.value = await dataApi.getCacheStats()
    } catch (err) {
      console.error('获取缓存统计失败:', err)
    }
  }
  
  /**
   * 清除缓存
   */
  async function clearCache(level?: 1 | 2 | 3 | 4) {
    loading.value = true
    
    try {
      const res = await dataApi.clearCache(level)
      return res
    } catch (err) {
      error.value = '清除缓存失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 重建缓存
   */
  async function rebuildCache() {
    loading.value = true
    
    try {
      const res = await dataApi.rebuildCache()
      return res
    } catch (err) {
      error.value = '重建缓存失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取门店统计
   */
  async function getStoreStats(storeName: string): Promise<StoreStats> {
    return await dataApi.getStoreStats(storeName)
  }
  
  /**
   * 删除门店数据
   */
  async function deleteStoreData(storeName: string) {
    loading.value = true
    
    try {
      const res = await dataApi.deleteStoreData(storeName)
      if (res.success) {
        await fetchStats()
        await fetchStores()
      }
      return res
    } catch (err) {
      error.value = '删除门店数据失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 优化数据库
   */
  async function optimizeDatabase() {
    loading.value = true
    
    try {
      const res = await dataApi.optimizeDatabase()
      return res
    } catch (err) {
      error.value = '优化数据库失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 导出数据
   */
  async function exportData(params: {
    type: 'orders' | 'products' | 'all'
    format: 'csv' | 'excel'
    date_range?: {
      start_date: string
      end_date: string
    }
  }) {
    loading.value = true
    
    try {
      const blob = await dataApi.exportData(params)
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${params.type}_export.${params.format === 'excel' ? 'xlsx' : 'csv'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      error.value = '导出数据失败'
      console.error(err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 验证数据
   */
  async function validateData() {
    try {
      return await dataApi.validateData()
    } catch (err) {
      console.error('验证数据失败:', err)
      throw err
    }
  }
  
  return {
    // State
    stats,
    stores,
    cacheStats,
    uploadHistory,
    uploadHistoryTotal,
    lastUploadResult,
    loading,
    uploading,
    error,
    databaseConnected,
    redisConnected,
    currentDataSource,
    currentStoreName,
    
    // Computed
    dataFreshness,
    hasData,
    databaseStatus,
    redisStatus,
    
    // Actions
    fetchStats,
    fetchStores,
    loadFromDatabase,
    uploadOrders,
    uploadProducts,
    fetchUploadHistory,
    fetchCacheStats,
    clearCache,
    rebuildCache,
    getStoreStats,
    deleteStoreData,
    optimizeDatabase,
    exportData,
    validateData
  }
})

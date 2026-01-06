/**
 * 全局数据缓存Store
 * 实现跨TAB数据共享，避免重复加载
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dataApi, type Store } from '@/api/data'
import type { DataStats } from '@/api/types'

// 缓存有效期（毫秒）
const CACHE_TTL = 5 * 60 * 1000 // 5分钟

interface GlobalFilters {
  store_name: string | null
  start_date: string | null
  end_date: string | null
  channel: string | null
}

interface StoreInfo {
  name: string
  order_count: number
}

interface ChannelInfo {
  name: string
  order_count: number
}

interface OrderData {
  order_id: string
  date: string
  store_name: string
  channel: string
  amount: number
  profit: number
  profit_rate: number
  product_count: number
}

export const useGlobalDataStore = defineStore('globalData', () => {
  // ==================== 状态 ====================
  
  // 基础数据（跨TAB共享）
  const stores = ref<StoreInfo[]>([])
  const channels = ref<ChannelInfo[]>([])
  const orderData = ref<OrderData[]>([])
  
  // 数据统计
  const dataStats = ref({
    total_orders: 0,
    total_stores: 0,
    total_products: 0,
    date_range: { start: '', end: '' }
  })
  
  // 全局筛选条件（跨TAB同步）
  const globalFilters = ref<GlobalFilters>({
    store_name: null,
    start_date: null,
    end_date: null,
    channel: null
  })
  
  // 加载状态
  const loading = ref({
    stores: false,
    channels: false,
    orders: false,
    stats: false
  })
  
  // 缓存时间戳
  const cacheTimestamps = ref({
    stores: 0,
    channels: 0,
    orders: 0,
    stats: 0
  })
  
  // 初始化状态
  const initialized = ref(false)
  const initializing = ref(false)
  
  // ==================== 计算属性 ====================
  
  const storeNames = computed(() => stores.value.map(s => s.name))
  const channelNames = computed(() => channels.value.map(c => c.name))
  
  const isDataLoaded = computed(() => 
    stores.value.length > 0 && dataStats.value.total_orders > 0
  )
  
  const hasValidCache = computed(() => ({
    stores: Date.now() - cacheTimestamps.value.stores < CACHE_TTL,
    channels: Date.now() - cacheTimestamps.value.channels < CACHE_TTL,
    orders: Date.now() - cacheTimestamps.value.orders < CACHE_TTL,
    stats: Date.now() - cacheTimestamps.value.stats < CACHE_TTL
  }))
  
  const isAnyLoading = computed(() => 
    Object.values(loading.value).some(v => v)
  )
  
  // ==================== 方法 ====================
  
  /**
   * 初始化全局数据（应用启动时调用一次）
   */
  async function initialize(force = false) {
    if (initializing.value) {
      console.log('🔄 全局数据正在初始化中，跳过重复调用')
      return
    }
    
    if (initialized.value && !force) {
      console.log('✅ 全局数据已初始化，使用缓存')
      return
    }
    
    initializing.value = true
    console.log('🚀 开始初始化全局数据...')
    
    try {
      // 并行加载所有基础数据
      await Promise.all([
        fetchStores(),
        fetchDataStats()
      ])
      
      initialized.value = true
      console.log('✅ 全局数据初始化完成')
    } catch (error) {
      console.error('❌ 全局数据初始化失败:', error)
      throw error
    } finally {
      initializing.value = false
    }
  }
  
  /**
   * 获取门店列表（带缓存）
   */
  async function fetchStores(force = false) {
    if (!force && hasValidCache.value.stores && stores.value.length > 0) {
      console.log('📦 使用缓存的门店数据')
      return stores.value
    }
    
    loading.value.stores = true
    try {
      const res = await dataApi.getStores()
      if (res.success && res.data) {
        // 转换API响应格式为内部格式
        stores.value = res.data.map((store: Store) => ({
          name: store.label || store.value,
          order_count: store.order_count || 0
        }))
        cacheTimestamps.value.stores = Date.now()
        console.log(`✅ 门店数据加载完成: ${stores.value.length} 个门店`)
      }
      return stores.value
    } catch (error) {
      console.error('❌ 获取门店列表失败:', error)
      // 不抛出错误，返回空数组
      return []
    } finally {
      loading.value.stores = false
    }
  }
  
  /**
   * 获取数据统计（带缓存）
   */
  async function fetchDataStats(force = false) {
    if (!force && hasValidCache.value.stats && dataStats.value.total_orders > 0) {
      console.log('📦 使用缓存的数据统计')
      return dataStats.value
    }
    
    loading.value.stats = true
    try {
      const res = await dataApi.getStats() as any
      // 处理不同的响应格式
      const statsData = res.data || res
      if (statsData) {
        dataStats.value = {
          total_orders: statsData.total_orders || 0,
          total_stores: statsData.total_stores || 0,
          total_products: statsData.total_products || 0,
          date_range: {
            start: statsData.date_range?.start_date || statsData.date_range?.start || '',
            end: statsData.date_range?.end_date || statsData.date_range?.end || ''
          }
        }
        cacheTimestamps.value.stats = Date.now()
        console.log(`✅ 数据统计加载完成: ${dataStats.value.total_orders} 笔订单`)
      }
      return dataStats.value
    } catch (error) {
      console.error('❌ 获取数据统计失败:', error)
      // 不抛出错误，返回默认值
      return dataStats.value
    } finally {
      loading.value.stats = false
    }
  }
  
  /**
   * 设置全局筛选条件（会触发所有TAB刷新）
   */
  function setGlobalFilters(filters: Partial<GlobalFilters>) {
    globalFilters.value = { ...globalFilters.value, ...filters }
    console.log('🔧 全局筛选条件更新:', globalFilters.value)
  }
  
  /**
   * 重置全局筛选条件
   */
  function resetFilters() {
    globalFilters.value = {
      store_name: null,
      start_date: null,
      end_date: null,
      channel: null
    }
    console.log('🔄 全局筛选条件已重置')
  }
  
  /**
   * 清除所有缓存
   */
  function clearCache() {
    stores.value = []
    channels.value = []
    orderData.value = []
    dataStats.value = {
      total_orders: 0,
      total_stores: 0,
      total_products: 0,
      date_range: { start: '', end: '' }
    }
    cacheTimestamps.value = {
      stores: 0,
      channels: 0,
      orders: 0,
      stats: 0
    }
    initialized.value = false
    console.log('🗑️ 全局缓存已清除')
  }
  
  /**
   * 刷新所有数据
   */
  async function refreshAll() {
    console.log('🔄 刷新所有全局数据...')
    clearCache()
    await initialize(true)
  }
  
  /**
   * 获取用于API请求的筛选参数
   */
  function getFilterParams(): Record<string, string> {
    const params: Record<string, string> = {}
    
    if (globalFilters.value.store_name) {
      params.store_name = globalFilters.value.store_name
    }
    if (globalFilters.value.start_date) {
      params.start_date = globalFilters.value.start_date
    }
    if (globalFilters.value.end_date) {
      params.end_date = globalFilters.value.end_date
    }
    if (globalFilters.value.channel) {
      params.channel = globalFilters.value.channel
    }
    
    return params
  }
  
  return {
    // 状态
    stores,
    channels,
    orderData,
    dataStats,
    globalFilters,
    loading,
    initialized,
    initializing,
    
    // 计算属性
    storeNames,
    channelNames,
    isDataLoaded,
    hasValidCache,
    isAnyLoading,
    
    // 方法
    initialize,
    fetchStores,
    fetchDataStats,
    setGlobalFilters,
    resetFilters,
    clearCache,
    refreshAll,
    getFilterParams
  }
})


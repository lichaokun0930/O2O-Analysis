/**
 * 订单状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { orderApi, type OrderQueryParams } from '@/api/orders'
import type { Order, OrderSummary, TrendData } from '@/api/types'

export const useOrderStore = defineStore('order', () => {
  // State
  const orders = ref<Order[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const summary = ref<OrderSummary | null>(null)
  const trendData = ref<TrendData[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 筛选条件
  const filters = ref<OrderQueryParams>({
    start_date: undefined,
    end_date: undefined,
    store_name: undefined,
    platform: undefined,
    min_profit: undefined,
    max_profit: undefined
  })
  
  // Computed
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const hasOverflowOrders = computed(() => 
    orders.value.some(o => o.profit < 0)
  )
  
  // Actions
  async function fetchOrders(params?: OrderQueryParams) {
    loading.value = true
    error.value = null
    
    try {
      const response = await orderApi.getOrders({
        page: currentPage.value,
        page_size: pageSize.value,
        ...filters.value,
        ...params
      })
      
      orders.value = response.items
      total.value = response.total
    } catch (err) {
      error.value = '获取订单列表失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchSummary(dateRange?: { start_date: string; end_date: string }) {
    loading.value = true
    
    try {
      summary.value = await orderApi.getSummary(dateRange)
    } catch (err) {
      error.value = '获取订单汇总失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchTrend(params: {
    start_date: string
    end_date: string
    granularity?: 'day' | 'week' | 'month'
  }) {
    try {
      const response = await orderApi.getTrend(params)
      trendData.value = response.dates.map((date, index) => ({
        date,
        value: response.values[index]
      }))
    } catch (err) {
      console.error('获取趋势数据失败:', err)
    }
  }
  
  function setFilters(newFilters: Partial<OrderQueryParams>) {
    filters.value = { ...filters.value, ...newFilters }
    currentPage.value = 1 // 重置页码
  }
  
  function setPage(page: number) {
    currentPage.value = page
    fetchOrders()
  }
  
  function setPageSize(size: number) {
    pageSize.value = size
    currentPage.value = 1
    fetchOrders()
  }
  
  function resetFilters() {
    filters.value = {
      start_date: undefined,
      end_date: undefined,
      store_name: undefined,
      platform: undefined,
      min_profit: undefined,
      max_profit: undefined
    }
    currentPage.value = 1
  }
  
  return {
    // State
    orders,
    total,
    currentPage,
    pageSize,
    summary,
    trendData,
    loading,
    error,
    filters,
    
    // Computed
    totalPages,
    hasOverflowOrders,
    
    // Actions
    fetchOrders,
    fetchSummary,
    fetchTrend,
    setFilters,
    setPage,
    setPageSize,
    resetFilters
  }
})


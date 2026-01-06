/**
 * 诊断分析状态管理（今日必做核心）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { diagnosisApi, type DiagnosisParams } from '@/api/diagnosis'
import type { 
  DiagnosisSummary, 
  OverflowOrder, 
  CustomerChurnAnalysis 
} from '@/api/types'

export const useDiagnosisStore = defineStore('diagnosis', () => {
  // State
  const summary = ref<DiagnosisSummary | null>(null)
  const overflowOrders = ref<OverflowOrder[]>([])
  const overflowTotal = ref(0)
  const customerChurn = ref<CustomerChurnAnalysis | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 当前筛选条件
  const filters = ref<DiagnosisParams>({
    store_name: undefined,
    start_date: undefined,
    end_date: undefined
  })
  
  // Computed
  const urgentCount = computed(() => summary.value?.urgent_count || 0)
  const watchCount = computed(() => summary.value?.watch_count || 0)
  const highlightCount = computed(() => summary.value?.highlight_count || 0)
  const totalLoss = computed(() => summary.value?.total_loss || 0)
  
  const hasUrgentIssues = computed(() => urgentCount.value > 0)
  const churnRate = computed(() => customerChurn.value?.churn_rate || 0)
  
  // Actions
  async function fetchDiagnosisSummary(params?: DiagnosisParams) {
    loading.value = true
    error.value = null
    
    try {
      summary.value = await diagnosisApi.getSummary({
        ...filters.value,
        ...params
      })
    } catch (err) {
      error.value = '获取诊断汇总失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchOverflowOrders(params?: {
    page?: number
    page_size?: number
    min_loss?: number
  }) {
    loading.value = true
    
    try {
      const response = await diagnosisApi.getOverflowOrders({
        ...filters.value,
        ...params
      })
      overflowOrders.value = response.items
      overflowTotal.value = response.total
    } catch (err) {
      error.value = '获取穿底订单失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchCustomerChurn(daysThreshold?: number) {
    loading.value = true
    
    try {
      customerChurn.value = await diagnosisApi.getCustomerChurn({
        store_name: filters.value.store_name,
        days_threshold: daysThreshold
      })
    } catch (err) {
      error.value = '获取客户流失分析失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  function setFilters(newFilters: Partial<DiagnosisParams>) {
    filters.value = { ...filters.value, ...newFilters }
  }
  
  function resetFilters() {
    filters.value = {
      store_name: undefined,
      start_date: undefined,
      end_date: undefined
    }
  }
  
  // 刷新所有数据
  async function refreshAll() {
    await Promise.all([
      fetchDiagnosisSummary(),
      fetchOverflowOrders(),
      fetchCustomerChurn()
    ])
  }
  
  return {
    // State
    summary,
    overflowOrders,
    overflowTotal,
    customerChurn,
    loading,
    error,
    filters,
    
    // Computed
    urgentCount,
    watchCount,
    highlightCount,
    totalLoss,
    hasUrgentIssues,
    churnRate,
    
    // Actions
    fetchDiagnosisSummary,
    fetchOverflowOrders,
    fetchCustomerChurn,
    setFilters,
    resetFilters,
    refreshAll
  }
})


/**
 * 商品状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { productApi, type ProductQueryParams } from '@/api/products'
import type { Product, ProductAnalysis, CategoryAnalysis } from '@/api/types'

export const useProductStore = defineStore('product', () => {
  // State
  const products = ref<Product[]>([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const analysis = ref<ProductAnalysis | null>(null)
  const categoryAnalysis = ref<CategoryAnalysis[]>([])
  const topSellers = ref<Product[]>([])
  const slowMoving = ref<Product[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const filters = ref<ProductQueryParams>({
    category: undefined,
    keyword: undefined,
    min_profit_rate: undefined,
    max_profit_rate: undefined
  })
  
  // Computed
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const categories = computed(() => 
    [...new Set(categoryAnalysis.value.map(c => c.category))]
  )
  
  // Actions
  async function fetchProducts(params?: ProductQueryParams) {
    loading.value = true
    error.value = null
    
    try {
      const response = await productApi.getProducts({
        page: currentPage.value,
        page_size: pageSize.value,
        ...filters.value,
        ...params
      })
      
      products.value = response.items
      total.value = response.total
    } catch (err) {
      error.value = '获取商品列表失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchAnalysis(params?: {
    start_date?: string
    end_date?: string
    store_name?: string
  }) {
    loading.value = true
    
    try {
      analysis.value = await productApi.getAnalysis(params)
    } catch (err) {
      error.value = '获取商品分析失败'
      console.error(err)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchCategoryAnalysis(params?: {
    start_date?: string
    end_date?: string
  }) {
    try {
      categoryAnalysis.value = await productApi.getCategoryAnalysis(params)
    } catch (err) {
      console.error('获取分类分析失败:', err)
    }
  }
  
  async function fetchTopSellers(limit = 10) {
    try {
      topSellers.value = await productApi.getTopSellers({ limit })
    } catch (err) {
      console.error('获取畅销商品失败:', err)
    }
  }
  
  async function fetchSlowMoving(days = 30) {
    try {
      slowMoving.value = await productApi.getSlowMoving({ days })
    } catch (err) {
      console.error('获取滞销商品失败:', err)
    }
  }
  
  function setFilters(newFilters: Partial<ProductQueryParams>) {
    filters.value = { ...filters.value, ...newFilters }
    currentPage.value = 1
  }
  
  function setPage(page: number) {
    currentPage.value = page
    fetchProducts()
  }
  
  function resetFilters() {
    filters.value = {
      category: undefined,
      keyword: undefined,
      min_profit_rate: undefined,
      max_profit_rate: undefined
    }
    currentPage.value = 1
  }
  
  return {
    // State
    products,
    total,
    currentPage,
    pageSize,
    analysis,
    categoryAnalysis,
    topSellers,
    slowMoving,
    loading,
    error,
    filters,
    
    // Computed
    totalPages,
    categories,
    
    // Actions
    fetchProducts,
    fetchAnalysis,
    fetchCategoryAnalysis,
    fetchTopSellers,
    fetchSlowMoving,
    setFilters,
    setPage,
    resetFilters
  }
})


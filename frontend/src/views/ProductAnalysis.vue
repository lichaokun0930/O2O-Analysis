<template>
  <div class="product-analysis">
    <div class="page-header">
      <h2>📦 商品分析</h2>
    </div>
    
    <!-- 筛选面板 -->
    <FilterPanel
      :show-date-range="true"
      :show-store="true"
      :stores="storeList"
      @search="handleSearch"
      @reset="handleReset"
    >
      <template #filters="{ filters }">
        <el-form-item label="分类">
          <el-select v-model="filters.category" placeholder="全部分类" clearable>
            <el-option
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.keyword"
            placeholder="商品名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
      </template>
    </FilterPanel>
    
    <!-- 汇总卡片 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6">
        <KPICard
          title="商品总数"
          :value="total"
          suffix="款"
          variant="info"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="畅销商品"
          :value="topSellers.length"
          suffix="款"
          variant="highlight"
          description="销量前20%"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="滞销商品"
          :value="slowMoving.length"
          suffix="款"
          variant="watch"
          description="30天无销量"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="低利润商品"
          :value="lowProfitCount"
          suffix="款"
          variant="urgent"
          description="利润率<10%"
        />
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>🏆 销量 TOP 10</h3>
          </div>
          <div class="dashboard-card__body">
            <G2PlotChart
              type="bar"
              :data="topSellersChartData"
              :config="barChartConfig"
              height="350px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>📊 分类销售额占比</h3>
          </div>
          <div class="dashboard-card__body">
            <PieChart
              :data="categoryPieData"
              angle-field="revenue"
              color-field="category"
              height="350px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 分类分析表格 -->
    <div class="dashboard-card" style="margin-top: 16px;">
      <div class="dashboard-card__header">
        <h3>📈 分类分析</h3>
      </div>
      <div class="dashboard-card__body">
        <el-table :data="categoryAnalysis" stripe v-loading="loading">
          <el-table-column prop="category" label="分类" min-width="120" />
          <el-table-column prop="product_count" label="商品数" width="100" align="right" />
          <el-table-column prop="total_sales" label="销量" width="100" align="right" />
          <el-table-column prop="total_revenue" label="销售额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.total_revenue?.toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="total_profit" label="利润" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.total_profit < 0 ? 'text-danger' : 'text-success'">
                ¥{{ row.total_profit?.toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="avg_profit_rate" label="平均利润率" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.avg_profit_rate < 0.1 ? 'text-danger' : 'text-success'">
                {{ (row.avg_profit_rate * 100).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <!-- 商品列表 -->
    <div class="dashboard-card" style="margin-top: 16px;">
      <div class="dashboard-card__header">
        <h3>📋 商品明细</h3>
      </div>
      <div class="dashboard-card__body">
        <DataTable
          :data="products"
          :columns="productColumns"
          :total="total"
          :loading="loading"
          @page-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductStore } from '@/stores/productStore'
import FilterPanel from '@/components/common/FilterPanel.vue'
import KPICard from '@/components/charts/KPICard.vue'
import G2PlotChart from '@/components/charts/G2PlotChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import DataTable from '@/components/tables/DataTable.vue'

const productStore = useProductStore()

// State
const storeList = ref<string[]>(['门店A', '门店B', '门店C'])
const lowProfitCount = ref(15)

// Computed
const loading = computed(() => productStore.loading)
const products = computed(() => productStore.products)
const total = computed(() => productStore.total)
const categories = computed(() => productStore.categories)
const categoryAnalysis = computed(() => productStore.categoryAnalysis)
const topSellers = computed(() => productStore.topSellers)
const slowMoving = computed(() => productStore.slowMoving)

const topSellersChartData = computed(() => {
  return topSellers.value.slice(0, 10).map(p => ({
    product: p.product_name.length > 10 ? p.product_name.substring(0, 10) + '...' : p.product_name,
    sales: p.sales_count
  })).reverse()
})

const categoryPieData = computed(() => {
  return categoryAnalysis.value.map(c => ({
    category: c.category,
    revenue: c.total_revenue
  }))
})

const barChartConfig = {
  xField: 'sales',
  yField: 'product',
  seriesField: 'product',
  legend: false,
  label: {
    position: 'right',
    offset: 4
  },
  barStyle: {
    radius: [4, 4, 0, 0]
  },
  color: '#1890ff'
}

// 表格列配置
const productColumns = [
  { prop: 'product_name', label: '商品名称', minWidth: 200 },
  { prop: 'category', label: '分类', width: 100 },
  { prop: 'unit_price', label: '单价', width: 90, type: 'money' as const },
  { prop: 'cost', label: '成本', width: 90, type: 'money' as const },
  { prop: 'sales_count', label: '销量', width: 80, align: 'right' as const, sortable: true },
  { prop: 'revenue', label: '销售额', width: 110, type: 'money' as const, sortable: true },
  { prop: 'profit', label: '利润', width: 100, type: 'money' as const },
  { prop: 'profit_rate', label: '利润率', width: 90, type: 'percent' as const, threshold: 0.1 }
]

// Methods
const handleSearch = (filters: Record<string, unknown>) => {
  productStore.setFilters(filters)
  productStore.fetchProducts()
  productStore.fetchCategoryAnalysis({
    start_date: filters.start_date as string,
    end_date: filters.end_date as string
  })
}

const handleReset = () => {
  productStore.resetFilters()
  productStore.fetchProducts()
}

const handlePageChange = (page: number) => {
  productStore.setPage(page)
}

const handleSizeChange = (size: number) => {
  productStore.setFilters({ page_size: size })
  productStore.fetchProducts()
}

// Lifecycle
onMounted(() => {
  productStore.fetchProducts()
  productStore.fetchCategoryAnalysis()
  productStore.fetchTopSellers(10)
  productStore.fetchSlowMoving(30)
})
</script>

<style lang="scss" scoped>
.product-analysis {
  .page-header {
    margin-bottom: 24px;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  .kpi-row {
    margin-bottom: 16px;
  }
  
  .chart-row {
    margin-bottom: 16px;
  }
  
  .text-danger {
    color: #ff4d4f;
  }
  
  .text-success {
    color: #52c41a;
  }
}
</style>


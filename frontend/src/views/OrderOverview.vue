<template>
  <div class="order-overview">
    <!-- 筛选栏 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <div class="filter-item">
          <span class="label">门店:</span>
          <el-select
            v-model="filters.store_name"
            placeholder="全部门店"
            clearable
            filterable
            style="width: 240px"
          >
            <el-option
              v-for="store in storeList"
              :key="store"
              :label="store"
              :value="store"
            />
          </el-select>
        </div>
        <div class="filter-item">
          <span class="label">日期:</span>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 260px"
          />
        </div>
        <div class="filter-actions">
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Download" :loading="exporting" @click="handleExport">导出</el-button>
        </div>
      </div>
    </el-card>

    <!-- 六大核心卡片 -->
    <div class="kpi-section">
      <h3 class="section-title">📊 核心经营指标</h3>
      <el-row :gutter="16">
        <el-col :span="4" v-for="(card, index) in kpiCards" :key="index">
          <el-card class="kpi-card" :class="card.class" shadow="hover" v-loading="loading">
            <div class="kpi-icon">{{ card.icon }}</div>
            <div class="kpi-content">
              <div class="kpi-label">{{ card.label }}</div>
              <div class="kpi-value">{{ card.prefix }}{{ formatNumber(card.value) }}{{ card.suffix }}</div>
              <div class="kpi-change" :class="getChangeClass(card.change, card.positive)">
                <span v-if="card.change !== null">
                  {{ card.change >= 0 ? '↑' : '↓' }} {{ Math.abs(card.change).toFixed(1) }}%
                </span>
                <span v-else class="no-change">--</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 渠道表现对比 -->
    <div class="channel-section">
      <h3 class="section-title">🏪 渠道表现对比</h3>
      <el-row :gutter="16">
        <el-col :span="6" v-for="channel in channelComparison" :key="channel.channel">
          <el-card class="channel-card" shadow="hover" v-loading="loading">
            <div class="channel-header">
              <span class="channel-name">{{ channel.channel }}</span>
              <el-tag :type="getRatingType(channel.rating)" size="small">{{ channel.rating }}</el-tag>
            </div>
            <div class="channel-metrics">
              <div class="metric-row">
                <span class="metric-label">订单数</span>
                <span class="metric-value">{{ channel.current.order_count }}</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.order_count)">
                  {{ formatChange(channel.changes.order_count) }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">销售额</span>
                <span class="metric-value">¥{{ formatNumber(channel.current.amount) }}</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.amount)">
                  {{ formatChange(channel.changes.amount) }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">利润</span>
                <span class="metric-value">¥{{ formatNumber(channel.current.profit) }}</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.profit)">
                  {{ formatChange(channel.changes.profit) }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">客单价</span>
                <span class="metric-value">¥{{ channel.current.avg_value.toFixed(2) }}</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.avg_value)">
                  {{ formatChange(channel.changes.avg_value) }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">利润率</span>
                <span class="metric-value">{{ channel.current.profit_rate.toFixed(1) }}%</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.profit_rate)">
                  {{ channel.changes.profit_rate >= 0 ? '+' : '' }}{{ channel.changes.profit_rate.toFixed(1) }}pp
                </span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="charts-section">
      <!-- 客单价区间分布 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>💰 客单价区间分布</span>
              <span class="basket-depth">购物篮深度: {{ priceDistribution?.avg_basket_depth || 0 }} SKU</span>
            </div>
          </template>
          <div ref="priceChartRef" class="chart-container"></div>
          <!-- 四大业务价格组 -->
          <div class="business-zones" v-if="priceDistribution">
            <div class="zone" v-for="(zone, key) in priceDistribution.business_zones" :key="key">
              <span class="zone-label">{{ zone.label }}</span>
              <span class="zone-count">{{ zone.count }}单</span>
              <span class="zone-ratio">{{ zone.ratio }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 一级分类销售趋势 -->
      <el-col :span="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span>📦 一级分类销售趋势</span>
              <el-select v-model="trendChannel" size="small" style="width: 120px">
                <el-option label="全部渠道" value="" />
                <el-option v-for="ch in channelList" :key="ch" :label="ch" :value="ch" />
              </el-select>
            </div>
          </template>
          <div ref="categoryChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 订单趋势图 -->
    <el-card class="chart-card trend-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>📈 订单趋势分析</span>
          <div class="trend-controls">
            <el-radio-group v-model="granularity" size="small" @change="fetchTrend">
              <el-radio-button label="day">按日</el-radio-button>
              <el-radio-button label="week">按周</el-radio-button>
              <el-radio-button label="month">按月</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      <div ref="trendChartRef" class="chart-container-large"></div>
    </el-card>

    <!-- 异常诊断面板 -->
    <el-card class="anomaly-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>⚠️ 异常诊断</span>
        </div>
      </template>
      <el-row :gutter="16" v-if="anomalyData">
        <!-- 汇总卡片 -->
        <el-col :span="6">
          <div class="anomaly-summary">
            <div class="summary-item">
              <span class="summary-label">低利润率订单</span>
              <span class="summary-value danger">{{ anomalyData.summary.low_profit_count }}</span>
              <span class="summary-ratio">占 {{ anomalyData.summary.low_profit_ratio }}%</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">高配送成本订单</span>
              <span class="summary-value warning">{{ anomalyData.summary.high_delivery_count }}</span>
              <span class="summary-ratio">占 {{ anomalyData.summary.high_delivery_ratio }}%</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">负利润订单</span>
              <span class="summary-value danger">{{ anomalyData.summary.negative_profit_count }}</span>
              <span class="summary-ratio">损失 ¥{{ formatNumber(anomalyData.summary.total_loss) }}</span>
            </div>
          </div>
        </el-col>
        <!-- 异常订单列表 -->
        <el-col :span="18">
          <el-tabs v-model="activeAnomalyTab">
            <el-tab-pane label="低利润率" name="low_profit">
              <el-table :data="anomalyData.low_profit" size="small" max-height="200">
                <el-table-column prop="order_id" label="订单ID" width="150" />
                <el-table-column prop="channel" label="渠道" width="100" />
                <el-table-column prop="amount" label="金额" width="100">
                  <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
                </el-table-column>
                <el-table-column prop="profit_rate" label="利润率" width="100">
                  <template #default="{ row }">
                    <span class="danger-text">{{ row.profit_rate.toFixed(1) }}%</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="高配送成本" name="high_delivery">
              <el-table :data="anomalyData.high_delivery" size="small" max-height="200">
                <el-table-column prop="order_id" label="订单ID" width="150" />
                <el-table-column prop="channel" label="渠道" width="100" />
                <el-table-column prop="delivery_cost" label="配送成本" width="100">
                  <template #default="{ row }">¥{{ row.delivery_cost.toFixed(2) }}</template>
                </el-table-column>
                <el-table-column prop="delivery_ratio" label="占比" width="100">
                  <template #default="{ row }">
                    <span class="warning-text">{{ row.delivery_ratio.toFixed(1) }}%</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="负利润" name="negative_profit">
              <el-table :data="anomalyData.negative_profit" size="small" max-height="200">
                <el-table-column prop="order_id" label="订单ID" width="150" />
                <el-table-column prop="channel" label="渠道" width="100" />
                <el-table-column prop="amount" label="金额" width="100">
                  <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
                </el-table-column>
                <el-table-column prop="loss" label="亏损" width="100">
                  <template #default="{ row }">
                    <span class="danger-text">-¥{{ row.loss.toFixed(2) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </el-col>
      </el-row>
    </el-card>

    <!-- 订单列表 -->
    <el-card class="list-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span>📋 订单明细</span>
          <span class="total-count">共 {{ pagination.total }} 笔订单</span>
        </div>
      </template>
      <el-table
        :data="orderList"
        v-loading="listLoading"
        @sort-change="handleSortChange"
        :row-class-name="getRowClassName"
      >
        <el-table-column prop="order_id" label="订单ID" width="180" />
        <el-table-column prop="order_date" label="日期" width="120" sortable="custom" />
        <el-table-column prop="store_name" label="门店" min-width="200" />
        <el-table-column prop="channel" label="渠道" width="120">
          <template #default="{ row }">
            <el-tag :type="getChannelTagType(row.channel)" size="small">{{ row.channel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120" sortable="custom">
          <template #default="{ row }">¥{{ row.amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="profit" label="利润" width="120" sortable="custom">
          <template #default="{ row }">
            <span :class="row.profit < 0 ? 'danger-text' : 'success-text'">
              ¥{{ row.profit.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_rate" label="利润率" width="100">
          <template #default="{ row }">
            <span :class="getProfitRateClass(row.profit_rate)">
              {{ row.profit_rate.toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { Download, Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { 
  orderApi, 
  type OrderOverview, 
  type ChannelComparison, 
  type TrendData, 
  type OrderListItem,
  type PriceDistribution,
  type CategoryTrend,
  type ComparisonData,
  type AnomalyDetection
} from '@/api/orders'
import { useGlobalDataStore } from '@/stores/globalDataStore'

// 全局数据Store
const globalStore = useGlobalDataStore()

// 状态
const loading = ref(false)
const listLoading = ref(false)
const exporting = ref(false)
const storeList = ref<string[]>([])
const channelList = ref<string[]>([])

// 筛选条件
const filters = ref({
  store_name: '',
})
const dateRange = ref<string[]>([])
const granularity = ref<'day' | 'week' | 'month'>('day')
const trendChannel = ref('')
const activeAnomalyTab = ref('low_profit')

// 数据
const overview = ref<OrderOverview>({
  total_orders: 0,
  total_actual_sales: 0,
  total_profit: 0,
  avg_order_value: 0,
  profit_rate: 0,
  active_products: 0,
})
const comparison = ref<ComparisonData | null>(null)
const channelComparison = ref<ChannelComparison[]>([])
const trendData = ref<TrendData>({
  dates: [],
  order_counts: [],
  amounts: [],
  profits: [],
  avg_values: [],
})
const priceDistribution = ref<PriceDistribution | null>(null)
const categoryTrend = ref<CategoryTrend | null>(null)
const anomalyData = ref<AnomalyDetection | null>(null)
const orderList = ref<OrderListItem[]>([])

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 排序
const sortConfig = ref({
  sort_by: 'date',
  sort_order: 'desc' as 'asc' | 'desc',
})

// 图表实例
const priceChartRef = ref<HTMLElement>()
const categoryChartRef = ref<HTMLElement>()
const trendChartRef = ref<HTMLElement>()
let priceChart: echarts.ECharts | null = null
let categoryChart: echarts.ECharts | null = null
let trendChart: echarts.ECharts | null = null

// 计算KPI卡片数据
const kpiCards = computed(() => {
  const changes = comparison.value?.changes || {}
  return [
    {
      icon: '📦',
      label: '订单总数',
      value: overview.value.total_orders,
      prefix: '',
      suffix: '笔',
      change: changes.order_count ?? null,
      positive: true,
      class: 'kpi-orders'
    },
    {
      icon: '💰',
      label: '商品实收额',
      value: overview.value.total_actual_sales,
      prefix: '¥',
      suffix: '',
      change: changes.total_sales ?? null,
      positive: true,
      class: 'kpi-sales'
    },
    {
      icon: '💎',
      label: '总利润',
      value: overview.value.total_profit,
      prefix: '¥',
      suffix: '',
      change: changes.total_profit ?? null,
      positive: true,
      class: 'kpi-profit'
    },
    {
      icon: '🛒',
      label: '平均客单价',
      value: overview.value.avg_order_value,
      prefix: '¥',
      suffix: '',
      change: changes.avg_order_value ?? null,
      positive: true,
      class: 'kpi-aov'
    },
    {
      icon: '📈',
      label: '总利润率',
      value: overview.value.profit_rate,
      prefix: '',
      suffix: '%',
      change: changes.profit_rate ?? null,
      positive: true,
      class: 'kpi-rate'
    },
    {
      icon: '🏷️',
      label: '动销商品数',
      value: overview.value.active_products,
      prefix: '',
      suffix: '个',
      change: changes.active_products ?? null,
      positive: true,
      class: 'kpi-products'
    },
  ]
})

// 格式化函数
const formatNumber = (num: number): string => {
  if (num === null || num === undefined) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

const formatChange = (change: number): string => {
  if (change === null || change === undefined) return '--'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(1)}%`
}

// 获取筛选参数
const getFilterParams = () => {
  const params: Record<string, string> = {}
  if (filters.value.store_name) {
    params.store_name = filters.value.store_name
  }
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  return params
}

// 数据获取方法
const fetchOverview = async () => {
  try {
    const res = await orderApi.getOverview(getFilterParams())
    if (res.success) {
      overview.value = res.data
    }
  } catch (err) {
    console.error('获取概览数据失败:', err)
  }
}

const fetchComparison = async () => {
  try {
    const res = await orderApi.getComparison(getFilterParams())
    if (res.success) {
      comparison.value = res.data
    }
  } catch (err) {
    console.error('获取环比数据失败:', err)
  }
}

const fetchChannelComparison = async () => {
  try {
    const res = await orderApi.getChannelComparison(getFilterParams())
    if (res.success) {
      channelComparison.value = res.data
    }
  } catch (err) {
    console.error('获取渠道环比数据失败:', err)
  }
}

const fetchTrend = async () => {
  try {
    const params = {
      ...getFilterParams(),
      days: 30,
      granularity: granularity.value,
    }
    const res = await orderApi.getTrend(params)
    if (res.success) {
      trendData.value = res.data
      renderTrendChart()
    }
  } catch (err) {
    console.error('获取趋势数据失败:', err)
  }
}

const fetchPriceDistribution = async () => {
  try {
    const res = await orderApi.getPriceDistribution(getFilterParams())
    if (res.success) {
      priceDistribution.value = res.data
      renderPriceChart()
    }
  } catch (err) {
    console.error('获取客单价分布失败:', err)
  }
}

const fetchCategoryTrend = async () => {
  try {
    const params = {
      ...getFilterParams(),
      channel: trendChannel.value || undefined,
      weeks: 4,
    }
    const res = await orderApi.getCategoryTrend(params)
    if (res.success) {
      categoryTrend.value = res.data
      renderCategoryChart()
    }
  } catch (err) {
    console.error('获取分类趋势失败:', err)
  }
}

const fetchAnomalyDetection = async () => {
  try {
    const res = await orderApi.getAnomalyDetection(getFilterParams())
    if (res.success) {
      anomalyData.value = res.data
    }
  } catch (err) {
    console.error('获取异常诊断失败:', err)
  }
}

const fetchOrderList = async () => {
  listLoading.value = true
  try {
    const params = {
      ...getFilterParams(),
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      sort_by: sortConfig.value.sort_by,
      sort_order: sortConfig.value.sort_order,
    }
    const res = await orderApi.getList(params)
    if (res.success) {
      orderList.value = res.data
      pagination.value.total = res.total
    }
  } catch (err) {
    console.error('获取订单列表失败:', err)
  } finally {
    listLoading.value = false
  }
}

const fetchStores = async () => {
  try {
    // 优先使用全局缓存
    if (globalStore.storeNames.length > 0) {
      storeList.value = globalStore.storeNames
      return
    }
    const res = await orderApi.getStores()
    if (res.success) {
      storeList.value = res.data
    }
  } catch (err) {
    console.error('获取门店列表失败:', err)
  }
}

const fetchChannels = async () => {
  try {
    const res = await orderApi.getChannels()
    if (res.success) {
      channelList.value = res.data
    }
  } catch (err) {
    console.error('获取渠道列表失败:', err)
  }
}

// 渲染图表
const renderPriceChart = () => {
  if (!priceChartRef.value || !priceDistribution.value) return
  
  if (!priceChart) {
    priceChart = echarts.init(priceChartRef.value)
  }
  
  const data = priceDistribution.value.price_ranges
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const item = params[0]
        return `${item.name}<br/>订单数: ${item.value}单<br/>占比: ${data[item.dataIndex].ratio}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.label),
      axisLabel: { rotate: 30, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: '订单数',
    },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: d.count,
        itemStyle: { color: d.color }
      })),
      label: {
        show: true,
        position: 'top',
        fontSize: 10,
      },
    }],
  }
  
  priceChart.setOption(option)
}

const renderCategoryChart = () => {
  if (!categoryChartRef.value || !categoryTrend.value) return
  
  if (!categoryChart) {
    categoryChart = echarts.init(categoryChartRef.value)
  }
  
  const { weeks, series } = categoryTrend.value
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: series.map(s => s.name),
      bottom: 0,
      type: 'scroll',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: weeks.map(w => w.slice(5)), // 只显示月-日
    },
    yAxis: {
      type: 'value',
      name: '销售额(¥)',
    },
    series: series.map(s => ({
      name: s.name,
      type: 'line',
      data: s.data,
      smooth: true,
      itemStyle: { color: s.color },
    })),
  }
  
  categoryChart.setOption(option)
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  
  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }
  
  const { dates, order_counts, amounts, profits } = trendData.value
  
  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['订单数', '销售额', '利润'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLabel: { rotate: 45 },
    },
    yAxis: [
      {
        type: 'value',
        name: '订单数',
        position: 'left',
      },
      {
        type: 'value',
        name: '金额(¥)',
        position: 'right',
      },
    ],
    series: [
      {
        name: '订单数',
        type: 'bar',
        data: order_counts,
        itemStyle: { color: '#409EFF' },
        yAxisIndex: 0,
      },
      {
        name: '销售额',
        type: 'line',
        data: amounts,
        smooth: true,
        itemStyle: { color: '#67C23A' },
        yAxisIndex: 1,
      },
      {
        name: '利润',
        type: 'line',
        data: profits,
        smooth: true,
        itemStyle: { color: '#E6A23C' },
        yAxisIndex: 1,
      },
    ],
  }
  
  trendChart.setOption(option)
}

// 事件处理
const handleSearch = () => {
  pagination.value.page = 1
  fetchAllData()
}

const handleReset = () => {
  filters.value.store_name = ''
  dateRange.value = []
  pagination.value.page = 1
  fetchAllData()
}

const handleExport = async () => {
  exporting.value = true
  try {
    const blob = await orderApi.exportOrders(getFilterParams())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `订单经营分析报告_${new Date().toISOString().slice(0, 10)}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchOrderList()
}

const handleSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.page = 1
  fetchOrderList()
}

const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
  if (prop === 'order_date') sortConfig.value.sort_by = 'date'
  else if (prop === 'amount') sortConfig.value.sort_by = 'amount'
  else if (prop === 'profit') sortConfig.value.sort_by = 'profit'
  
  sortConfig.value.sort_order = order === 'ascending' ? 'asc' : 'desc'
  fetchOrderList()
}

// 样式辅助函数
const getChangeClass = (change: number, positive = true) => {
  if (change === null || change === undefined) return ''
  if (positive) {
    return change >= 0 ? 'positive' : 'negative'
  } else {
    return change <= 0 ? 'positive' : 'negative'
  }
}

const getRatingType = (rating: string) => {
  if (rating === '优秀') return 'success'
  if (rating === '良好') return 'warning'
  return 'danger'
}

const getChannelTagType = (channel: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  if (channel.includes('美团')) return 'warning'
  if (channel.includes('饿了么')) return '' // primary
  if (channel.includes('抖音')) return 'danger'
  if (channel.includes('京东')) return 'success'
  return 'info'
}

const getRowClassName = ({ row }: { row: OrderListItem }) => {
  if (row.profit < 0) return 'row-danger'
  if (row.profit_rate < 5) return 'row-warning'
  return ''
}

const getProfitRateClass = (rate: number) => {
  if (rate < 0) return 'danger-text'
  if (rate < 10) return 'warning-text'
  return 'success-text'
}

// 获取所有数据
const fetchAllData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchOverview(),
      fetchComparison(),
      fetchChannelComparison(),
      fetchTrend(),
      fetchPriceDistribution(),
      fetchCategoryTrend(),
      fetchAnomalyDetection(),
      fetchOrderList(),
    ])
  } finally {
    loading.value = false
  }
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  priceChart?.resize()
  categoryChart?.resize()
  trendChart?.resize()
}

// 监听渠道筛选变化
watch(() => trendChannel.value, () => {
  fetchCategoryTrend()
})

// 生命周期
onMounted(async () => {
  // 初始化全局数据
  await globalStore.initialize()
  
  await fetchStores()
  await fetchChannels()
  await fetchAllData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  priceChart?.dispose()
  categoryChart?.dispose()
  trendChart?.dispose()
})
</script>

<style scoped lang="scss">
.order-overview {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100vh;
}

.filter-card {
  margin-bottom: 16px;
  
  .filter-row {
    display: flex;
    align-items: center;
    gap: 24px;
    flex-wrap: wrap;
  }
  
  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .label {
      color: #606266;
      font-weight: 500;
    }
  }
  
  .filter-actions {
    margin-left: auto;
  }
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

// KPI 卡片
.kpi-section {
  margin-bottom: 16px;
}

.kpi-card {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  transition: all 0.3s;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  .kpi-icon {
    font-size: 28px;
    margin-bottom: 8px;
  }
  
  .kpi-label {
    font-size: 13px;
    color: #909399;
    margin-bottom: 4px;
  }
  
  .kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #303133;
  }
  
  .kpi-change {
    font-size: 12px;
    margin-top: 4px;
    
    &.positive {
      color: #67C23A;
    }
    
    &.negative {
      color: #F56C6C;
    }
    
    .no-change {
      color: #909399;
    }
  }
}

// 渠道卡片
.channel-section {
  margin-bottom: 16px;
}

.channel-card {
  .channel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    
    .channel-name {
      font-size: 15px;
      font-weight: 600;
    }
  }
  
  .channel-metrics {
    .metric-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 6px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .metric-label {
        font-size: 12px;
        color: #909399;
      }
      
      .metric-value {
        font-size: 13px;
        font-weight: 600;
      }
      
      .metric-change {
        font-size: 11px;
        
        &.positive {
          color: #67C23A;
        }
        
        &.negative {
          color: #F56C6C;
        }
      }
    }
  }
}

// 图表卡片
.charts-section {
  margin-bottom: 16px;
}

.chart-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .basket-depth {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .chart-container {
    height: 280px;
  }
  
  .business-zones {
    display: flex;
    justify-content: space-around;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
    
    .zone {
      text-align: center;
      
      .zone-label {
        display: block;
        font-size: 11px;
        color: #909399;
      }
      
      .zone-count {
        display: block;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
      
      .zone-ratio {
        font-size: 11px;
        color: #409EFF;
      }
    }
  }
}

.trend-card {
  margin-bottom: 16px;
  
  .chart-container-large {
    height: 350px;
  }
  
  .trend-controls {
    display: flex;
    gap: 12px;
  }
}

// 异常诊断
.anomaly-card {
  margin-bottom: 16px;
  
  .anomaly-summary {
    .summary-item {
      padding: 12px;
      margin-bottom: 8px;
      background: #f5f7fa;
      border-radius: 6px;
      
      .summary-label {
        display: block;
        font-size: 12px;
        color: #909399;
        margin-bottom: 4px;
      }
      
      .summary-value {
        font-size: 24px;
        font-weight: 700;
        
        &.danger {
          color: #F56C6C;
        }
        
        &.warning {
          color: #E6A23C;
        }
      }
      
      .summary-ratio {
        display: block;
        font-size: 11px;
        color: #909399;
        margin-top: 2px;
      }
    }
  }
}

// 订单列表
.list-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .total-count {
      font-size: 13px;
      color: #909399;
    }
  }
  
  .pagination-wrapper {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

// 通用样式
.danger-text {
  color: #F56C6C;
}

.warning-text {
  color: #E6A23C;
}

.success-text {
  color: #67C23A;
}

:deep(.row-danger) {
  background-color: #fef0f0 !important;
}

:deep(.row-warning) {
  background-color: #fdf6ec !important;
}
</style>

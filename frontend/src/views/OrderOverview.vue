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
        <el-col :span="8" v-for="channel in channelComparison" :key="channel.channel">
          <el-card class="channel-card" shadow="hover" v-loading="loading">
            <!-- 渠道头部 -->
            <div class="channel-header">
              <span class="channel-name">{{ getChannelIcon(channel.channel) }} {{ channel.channel }}</span>
              <el-tag :type="getRatingType(channel.rating)" size="small">{{ channel.rating }}</el-tag>
            </div>
            
            <!-- 核心指标区域 -->
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
                <span class="metric-value">¥{{ (channel.current.avg_value || 0).toFixed(2) }}</span>
                <span class="metric-change" :class="getChangeClass(channel.changes.avg_value)">
                  {{ formatChange(channel.changes.avg_value) }}
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">利润率</span>
                <span class="metric-value" :class="getProfitRateClass(channel.current.profit_rate)">
                  {{ (channel.current.profit_rate || 0).toFixed(1) }}%
                </span>
                <span class="metric-change" :class="getChangeClass(channel.changes.profit_rate)">
                  {{ formatProfitRateChange(channel.changes.profit_rate) }}
                </span>
              </div>
            </div>
            
            <!-- 单均经济区域 -->
            <div class="unit-economics">
              <div class="section-label">💰 单均经济</div>
              <el-row :gutter="8">
                <el-col :span="8">
                  <div class="unit-item">
                    <span class="unit-label">单均利润</span>
                    <span class="unit-value success">¥{{ (channel.current.avg_profit_per_order || 0).toFixed(2) }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="unit-item">
                    <span class="unit-label">单均营销</span>
                    <span class="unit-value warning">¥{{ (channel.current.avg_marketing_per_order || 0).toFixed(2) }}</span>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="unit-item">
                    <span class="unit-label">单均配送</span>
                    <span class="unit-value">¥{{ (channel.current.avg_delivery_per_order || 0).toFixed(2) }}</span>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <!-- 成本结构区域 -->
            <div class="cost-structure">
              <div class="section-label">📉 成本结构</div>
              
              <!-- 商品成本 -->
              <div class="cost-item">
                <div class="cost-header">
                  <span class="cost-name">📦 商品成本</span>
                  <span class="cost-amount">¥{{ formatNumber(channel.current.product_cost || 0) }}</span>
                  <span class="cost-rate primary">{{ (channel.current.product_cost_rate || 0).toFixed(1) }}%</span>
                </div>
                <el-progress 
                  :percentage="Math.min(channel.current.product_cost_rate || 0, 70)" 
                  :stroke-width="8"
                  :show-text="false"
                  color="#409EFF"
                />
              </div>
              
              <!-- 配送成本 -->
              <div class="cost-item">
                <div class="cost-header">
                  <span class="cost-name">🚚 配送成本</span>
                  <span class="cost-amount">¥{{ formatNumber(channel.current.delivery_cost || 0) }}</span>
                  <span class="cost-rate">{{ (channel.current.delivery_cost_rate || 0).toFixed(1) }}%</span>
                </div>
                <el-progress 
                  :percentage="Math.min((channel.current.delivery_cost_rate || 0) * 3.3, 100)" 
                  :stroke-width="8"
                  :show-text="false"
                  color="#909399"
                />
              </div>
              
              <!-- 平台服务费 -->
              <div class="cost-item">
                <div class="cost-header">
                  <span class="cost-name">📱 平台服务费</span>
                  <span class="cost-amount">¥{{ formatNumber(channel.current.platform_fee || 0) }}</span>
                  <span class="cost-rate info">{{ (channel.current.platform_fee_rate || 0).toFixed(1) }}%</span>
                </div>
                <el-progress 
                  :percentage="Math.min((channel.current.platform_fee_rate || 0) * 3.3, 100)" 
                  :stroke-width="8"
                  :show-text="false"
                  color="#67C23A"
                />
              </div>
              
              <!-- 总成本率 -->
              <div class="total-cost-rate">
                <span class="total-label">📊 总成本率</span>
                <span class="total-value" :class="getTotalCostRateClass(channel.current.total_cost_rate)">
                  {{ (channel.current.total_cost_rate || 0).toFixed(1) }}%
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
import { Download, Search, Refresh, ArrowDown } from '@element-plus/icons-vue'
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

// 日期范围（可选，不设置则加载门店所有数据）
const dateRange = ref<string[]>([])

// 是否已初始化加载（首次需要选择门店后才加载数据）
const isInitialized = ref(false)
const granularity = ref<'day' | 'week' | 'month'>('day')
const trendChannel = ref('')
const activeAnomalyTab = ref('low_profit')

// 渠道对比表格V2相关状态
const showCostDetail = ref(true)
const costCollapseActive = ref(['cost'])
const expandedChannel = ref<string>('')

// 切换渠道展开状态
const toggleChannelExpand = (channelName: string) => {
  if (expandedChannel.value === channelName) {
    expandedChannel.value = ''
  } else {
    expandedChannel.value = channelName
  }
}

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

// 渠道对比表格数据
const channelTableData = computed(() => [
  { key: 'order_count', metric: '订单数', icon: '📦' },
  { key: 'amount', metric: '销售额', icon: '💰' },
  { key: 'profit', metric: '利润', icon: '💎' },
  { key: 'avg_value', metric: '客单价', icon: '🛒' },
  { key: 'profit_rate', metric: '利润率', icon: '📈' },
])

// 格式化单元格值
const formatCellValue = (key: string, channel: ChannelComparison): string => {
  const current = channel.current
  switch (key) {
    case 'order_count':
      return current.order_count?.toLocaleString() || '0'
    case 'amount':
      return '¥' + formatNumber(current.amount || 0)
    case 'profit':
      return '¥' + formatNumber(current.profit || 0)
    case 'avg_value':
      return '¥' + (current.avg_value || 0).toFixed(2)
    case 'profit_rate':
      return (current.profit_rate || 0).toFixed(1) + '%'
    default:
      return '--'
  }
}

// 格式化单元格变化
const formatCellChange = (key: string, channel: ChannelComparison): string => {
  const changes = channel.changes
  const change = changes[key as keyof typeof changes]
  if (change === null || change === undefined) return '--'
  if (key === 'profit_rate') {
    const sign = change >= 0 ? '+' : ''
    return `${sign}${change.toFixed(1)}pp`
  }
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(1)}%`
}

// 获取单元格值样式
const getCellValueClass = (key: string, channel: ChannelComparison): string => {
  if (key === 'profit_rate') {
    const rate = channel.current.profit_rate || 0
    if (rate >= 20) return 'high-profit'
    if (rate >= 10) return 'medium-profit'
    return 'low-profit'
  }
  if (key === 'profit') {
    return (channel.current.profit || 0) >= 0 ? 'success-text' : 'danger-text'
  }
  return ''
}

// 获取单元格变化样式
const getCellChangeClass = (key: string, channel: ChannelComparison): string => {
  const changes = channel.changes
  const change = changes[key as keyof typeof changes]
  if (change === null || change === undefined) return ''
  return change >= 0 ? 'positive' : 'negative'
}

// 获取最优渠道
const getBestChannel = (key: string): string => {
  if (!channelComparison.value.length) return '--'
  let best = channelComparison.value[0]
  for (const ch of channelComparison.value) {
    const currentVal = ch.current[key as keyof typeof ch.current] as number || 0
    const bestVal = best.current[key as keyof typeof best.current] as number || 0
    if (currentVal > bestVal) {
      best = ch
    }
  }
  return best.channel.substring(0, 2) // 取前两个字符
}

// 获取渠道行样式
const getChannelRowClass = ({ row }: { row: any }): string => {
  if (row.key === 'profit_rate') return 'highlight-row'
  return ''
}

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

// 格式化利润率环比（使用pp而不是%）
const formatProfitRateChange = (change: number | null): string => {
  if (change === null || change === undefined) return '--'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(1)}pp`
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
    // 直接调用API获取门店列表（不依赖全局缓存）
    const res = await orderApi.getStores()
    if (res.success && res.data.length > 0) {
      storeList.value = res.data
      console.log(`✅ 门店列表加载成功: ${res.data.length} 个门店`)
    } else {
      // 如果orders API返回空，尝试从data API获取
      console.log('⚠️ orders API返回空，尝试从data API获取门店列表')
      const dataRes = await fetch('/api/v1/data/stores')
      const dataJson = await dataRes.json()
      if (dataJson.success && dataJson.data.length > 0) {
        // 转换格式：data API返回的是 {label, value, order_count}
        storeList.value = dataJson.data.map((s: any) => s.value || s.label)
        console.log(`✅ 从data API加载门店列表: ${storeList.value.length} 个门店`)
      }
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
  // 必须选择门店才能查询
  if (!filters.value.store_name) {
    ElMessage.warning('请先选择门店')
    return
  }
  
  pagination.value.page = 1
  isInitialized.value = true
  fetchAllData()
}

const handleReset = () => {
  filters.value.store_name = ''
  dateRange.value = []
  pagination.value.page = 1
  isInitialized.value = false
  
  // 重置数据为空
  overview.value = {
    total_orders: 0,
    total_actual_sales: 0,
    total_profit: 0,
    avg_order_value: 0,
    profit_rate: 0,
    active_products: 0,
  }
  comparison.value = null
  channelComparison.value = []
  trendData.value = { dates: [], order_counts: [], amounts: [], profits: [], avg_values: [] }
  priceDistribution.value = null
  categoryTrend.value = null
  anomalyData.value = null
  orderList.value = []
  pagination.value.total = 0
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

// 获取渠道图标
const getChannelIcon = (channel: string): string => {
  if (channel.includes('美团')) return '🟡'
  if (channel.includes('饿了么')) return '🔵'
  if (channel.includes('京东')) return '🔴'
  if (channel.includes('抖音')) return '🎵'
  if (channel.includes('收银机')) return '💳'
  if (channel.includes('闪购')) return '⚡'
  return '📱'
}

// 获取总成本率样式类
const getTotalCostRateClass = (rate: number): string => {
  if (rate < 70) return 'success-text'
  if (rate < 85) return 'warning-text'
  return 'danger-text'
}

// 渠道下钻处理
const handleChannelDrillDown = (channel: any) => {
  // TODO: 实现渠道下钻功能
  // 可以跳转到渠道详情页或打开弹窗
  ElMessage.info(`即将深入分析渠道: ${channel.channel}`)
  console.log('渠道下钻数据:', channel)
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
  if (isInitialized.value) {
    fetchCategoryTrend()
  }
})

// 生命周期
onMounted(async () => {
  // 初始化全局数据
  await globalStore.initialize()
  
  // 只加载门店和渠道列表，不加载数据
  // 用户需要选择门店后点击查询才加载数据
  await fetchStores()
  await fetchChannels()
  
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

// 渠道卡片V3 - 简洁卡片 + 渐进披露
.channel-section-v3 {
  margin-bottom: 20px;
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 16px;
  }
}

.channel-card-v3 {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
  
  &:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
  }
  
  &.is-expanded {
    box-shadow: 0 6px 24px rgba(64, 158, 255, 0.15);
    border-color: #409EFF;
  }
  
  .card-header-v3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    
    .channel-icon {
      font-size: 20px;
    }
    
    .channel-name {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
      flex: 1;
    }
  }
  
  .hero-metric {
    text-align: center;
    padding: 16px 0;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 16px;
    
    .hero-value {
      font-size: 28px;
      font-weight: 700;
      color: #303133;
      line-height: 1.2;
    }
    
    .hero-change {
      font-size: 13px;
      margin-top: 4px;
      
      &.positive {
        color: #67C23A;
      }
      
      &.negative {
        color: #F56C6C;
      }
    }
  }
  
  .key-metrics {
    display: flex;
    justify-content: space-around;
    margin-bottom: 16px;
    
    .key-item {
      text-align: center;
      
      .key-label {
        display: block;
        font-size: 12px;
        color: #909399;
        margin-bottom: 4px;
      }
      
      .key-value {
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
    }
  }
  
  .expand-trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 8px;
    color: #409EFF;
    font-size: 13px;
    cursor: pointer;
    border-radius: 6px;
    transition: background 0.2s;
    
    &:hover {
      background: #ecf5ff;
    }
    
    .el-icon {
      transition: transform 0.3s;
      
      &.is-rotate {
        transform: rotate(180deg);
      }
    }
  }
  
  .detail-panel {
    padding-top: 16px;
    border-top: 1px dashed #ebeef5;
    margin-top: 12px;
    
    .detail-section {
      margin-bottom: 16px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .section-label {
        font-size: 12px;
        font-weight: 600;
        color: #606266;
        margin-bottom: 10px;
      }
    }
    
    .detail-row {
      display: flex;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid #f5f5f5;
      
      &:last-child {
        border-bottom: none;
      }
      
      .detail-label {
        flex: 1;
        font-size: 13px;
        color: #606266;
      }
      
      .detail-value {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-right: 12px;
      }
      
      .detail-change {
        font-size: 12px;
        min-width: 50px;
        text-align: right;
        
        &.positive {
          color: #67C23A;
        }
        
        &.negative {
          color: #F56C6C;
        }
      }
    }
    
    .unit-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      
      .unit-item {
        text-align: center;
        padding: 10px 4px;
        background: #f9f9f9;
        border-radius: 6px;
        
        .unit-label {
          display: block;
          font-size: 11px;
          color: #909399;
          margin-bottom: 4px;
        }
        
        .unit-value {
          font-size: 14px;
          font-weight: 600;
          
          &.success {
            color: #67C23A;
          }
          
          &.warning {
            color: #E6A23C;
          }
        }
      }
    }
    
    .cost-mini-bar {
      height: 8px;
      background: #f0f0f0;
      border-radius: 4px;
      display: flex;
      overflow: hidden;
      margin-bottom: 8px;
      
      .cost-segment {
        height: 100%;
      }
    }
    
    .cost-total {
      font-size: 12px;
      color: #909399;
      text-align: right;
      
      strong {
        font-size: 14px;
      }
    }
  }
}

// 利润率颜色
.high-profit, .channel-card-v3 .key-value.high-profit {
  color: #67C23A !important;
}

.medium-profit, .channel-card-v3 .key-value.medium-profit {
  color: #E6A23C !important;
}

.low-profit, .channel-card-v3 .key-value.low-profit {
  color: #F56C6C !important;
}

// 保留旧版渠道卡片样式（兼容）
.channel-section {
  margin-bottom: 16px;
}

.channel-card {
  height: 100%;
  
  .channel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f0f0f0;
    
    .channel-name {
      font-size: 15px;
      font-weight: 600;
    }
  }
  
  .channel-metrics {
    margin-bottom: 12px;
    
    .metric-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 0;
      border-bottom: 1px solid #f5f5f5;
      
      &:last-child {
        border-bottom: none;
      }
      
      .metric-label {
        font-size: 12px;
        color: #909399;
        flex: 1;
      }
      
      .metric-value {
        font-size: 13px;
        font-weight: 600;
        flex: 1;
        text-align: center;
      }
      
      .metric-change {
        font-size: 11px;
        flex: 1;
        text-align: right;
        
        &.positive {
          color: #67C23A;
        }
        
        &.negative {
          color: #F56C6C;
        }
      }
    }
  }
  
  // 单均经济区域
  .unit-economics {
    margin-bottom: 12px;
    padding: 8px;
    background: #f9f9f9;
    border-radius: 6px;
    
    .section-label {
      font-size: 12px;
      font-weight: 600;
      color: #606266;
      margin-bottom: 8px;
    }
    
    .unit-item {
      text-align: center;
      
      .unit-label {
        display: block;
        font-size: 10px;
        color: #909399;
        margin-bottom: 2px;
      }
      
      .unit-value {
        font-size: 13px;
        font-weight: 600;
        color: #606266;
        
        &.success {
          color: #67C23A;
        }
        
        &.warning {
          color: #E6A23C;
        }
      }
    }
  }
  
  // 成本结构区域
  .cost-structure {
    margin-bottom: 12px;
    
    .section-label {
      font-size: 12px;
      font-weight: 600;
      color: #606266;
      margin-bottom: 8px;
    }
    
    .cost-item {
      margin-bottom: 8px;
      
      .cost-header {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
        
        .cost-name {
          font-size: 11px;
          font-weight: 500;
          flex: 1;
        }
        
        .cost-amount {
          font-size: 11px;
          color: #606266;
          margin-right: 8px;
        }
        
        .cost-rate {
          font-size: 11px;
          font-weight: 600;
          
          &.primary {
            color: #409EFF;
          }
          
          &.danger {
            color: #F56C6C;
          }
          
          &.warning {
            color: #E6A23C;
          }
          
          &.info {
            color: #67C23A;
          }
        }
      }
    }
    
    .total-cost-rate {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 8px;
      margin-top: 8px;
      border-top: 1px dashed #dcdfe6;
      
      .total-label {
        font-size: 12px;
        font-weight: 600;
      }
      
      .total-value {
        font-size: 14px;
        font-weight: 700;
      }
    }
  }
  
  // 下钻按钮
  .drill-down-btn {
    margin-top: 12px;
    
    .w-full {
      width: 100%;
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

<template>
  <div class="scene-analysis">
    <div class="page-header">
      <h2>⏰ 时段场景分析</h2>
    </div>
    
    <!-- 筛选面板 -->
    <FilterPanel
      :show-date-range="true"
      :show-store="true"
      :show-platform="true"
      :stores="storeList"
      @search="handleSearch"
      @reset="handleReset"
    />
    
    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <!-- 小时分布 -->
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>📊 小时订单分布</h3>
          </div>
          <div class="dashboard-card__body">
            <G2PlotChart
              type="column"
              :data="hourlyChartData"
              :config="hourlyConfig"
              height="300px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
      
      <!-- 星期分布 -->
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>📅 星期订单分布</h3>
          </div>
          <div class="dashboard-card__body">
            <G2PlotChart
              type="column"
              :data="dayOfWeekChartData"
              :config="dayConfig"
              height="300px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <el-row :gutter="16" class="chart-row">
      <!-- 热力图 -->
      <el-col :span="16">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>🔥 订单热力图</h3>
            <span class="header-tip">横轴: 小时，纵轴: 星期</span>
          </div>
          <div class="dashboard-card__body">
            <EChartsChart
              :option="heatmapOption"
              height="350px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
      
      <!-- 平台对比 -->
      <el-col :span="8">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>🏪 平台订单占比</h3>
          </div>
          <div class="dashboard-card__body">
            <PieChart
              :data="platformPieData"
              angle-field="order_count"
              color-field="platform"
              height="350px"
              :loading="loading"
            />
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 平台对比表格 -->
    <div class="dashboard-card" style="margin-top: 16px;">
      <div class="dashboard-card__header">
        <h3>📈 平台数据对比</h3>
      </div>
      <div class="dashboard-card__body">
        <el-table :data="platformData" stripe v-loading="loading">
          <el-table-column prop="platform" label="平台" width="120">
            <template #default="{ row }">
              <el-tag :type="getPlatformTagType(row.platform)" size="small">
                {{ row.platform }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="order_count" label="订单数" width="100" align="right" />
          <el-table-column prop="revenue" label="销售额" width="130" align="right">
            <template #default="{ row }">
              ¥{{ row.revenue?.toLocaleString() }}
            </template>
          </el-table-column>
          <el-table-column prop="profit" label="利润" width="120" align="right">
            <template #default="{ row }">
              <span :class="row.profit < 0 ? 'text-danger' : 'text-success'">
                ¥{{ row.profit?.toLocaleString() }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="profit_rate" label="利润率" width="100" align="right">
            <template #default="{ row }">
              <span :class="row.profit_rate < 0.1 ? 'text-danger' : 'text-success'">
                {{ (row.profit_rate * 100).toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="avg_order_value" label="平均客单价" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.avg_order_value?.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
    
    <!-- 场景标签 -->
    <div class="dashboard-card" style="margin-top: 16px;">
      <div class="dashboard-card__header">
        <h3>🏷️ 场景标签分析</h3>
      </div>
      <div class="dashboard-card__body">
        <div class="scene-tags">
          <div 
            v-for="tag in sceneTags" 
            :key="tag.tag_id"
            class="scene-tag-card"
          >
            <div class="tag-name">{{ tag.tag_name }}</div>
            <div class="tag-desc">{{ tag.description }}</div>
            <div class="tag-stats">
              <span class="tag-count">{{ tag.order_count }} 单</span>
              <span class="tag-revenue">贡献 {{ (tag.revenue_contribution * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSceneStore } from '@/stores/sceneStore'
import FilterPanel from '@/components/common/FilterPanel.vue'
import G2PlotChart from '@/components/charts/G2PlotChart.vue'
import EChartsChart from '@/components/charts/EChartsChart.vue'
import PieChart from '@/components/charts/PieChart.vue'

const sceneStore = useSceneStore()

// State
const storeList = ref<string[]>(['门店A', '门店B', '门店C'])

// Computed
const loading = computed(() => sceneStore.loading)
const hourlyData = computed(() => sceneStore.hourlyData)
const dayOfWeekData = computed(() => sceneStore.dayOfWeekData)
const platformData = computed(() => sceneStore.platformData)
const sceneTags = computed(() => sceneStore.sceneTags)
const heatmapData = computed(() => sceneStore.heatmapData)

const hourlyChartData = computed(() => {
  return hourlyData.value.map(d => ({
    hour: `${d.hour}:00`,
    orders: d.order_count,
    revenue: d.revenue
  }))
})

const dayOfWeekChartData = computed(() => {
  return dayOfWeekData.value.map(d => ({
    day: d.day_name,
    orders: d.order_count,
    revenue: d.revenue
  }))
})

const platformPieData = computed(() => {
  return platformData.value.map(p => ({
    platform: p.platform,
    order_count: p.order_count
  }))
})

const hourlyConfig = {
  xField: 'hour',
  yField: 'orders',
  label: {
    position: 'top',
    style: { fontSize: 10 }
  },
  color: '#1890ff',
  columnStyle: {
    radius: [4, 4, 0, 0]
  }
}

const dayConfig = {
  xField: 'day',
  yField: 'orders',
  label: {
    position: 'top',
    style: { fontSize: 10 }
  },
  color: '#52c41a',
  columnStyle: {
    radius: [4, 4, 0, 0]
  }
}

// 热力图配置（ECharts）
const heatmapOption = computed(() => {
  const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  
  // 转换数据格式
  const data = heatmapData.value.map(d => [d.hour, d.day, d.value || 0])
  
  // 计算最大值
  const maxValue = Math.max(...heatmapData.value.map(d => d.value || 0), 1)
  
  return {
    tooltip: {
      position: 'top',
      formatter: (params: { data: number[] }) => {
        return `${days[params.data[1]]} ${hours[params.data[0]]}<br/>订单数: ${params.data[2]}`
      }
    },
    grid: {
      top: 30,
      bottom: 30,
      left: 60,
      right: 30
    },
    xAxis: {
      type: 'category',
      data: hours,
      splitArea: { show: true },
      axisLabel: {
        interval: 2,
        fontSize: 10
      }
    },
    yAxis: {
      type: 'category',
      data: days,
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: maxValue,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: ['#e6f7ff', '#1890ff', '#003a8c']
      }
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
})

// Methods
const handleSearch = (filters: Record<string, unknown>) => {
  sceneStore.setFilters(filters)
  sceneStore.refreshAll()
}

const handleReset = () => {
  sceneStore.resetFilters()
  sceneStore.refreshAll()
}

const getPlatformTagType = (platform: string) => {
  switch (platform) {
    case '美团': return 'warning'
    case '饿了么': return 'primary'
    case '抖音': return 'danger'
    default: return 'info'
  }
}

// Lifecycle
onMounted(() => {
  sceneStore.refreshAll()
})
</script>

<style lang="scss" scoped>
.scene-analysis {
  .page-header {
    margin-bottom: 24px;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  .chart-row {
    margin-bottom: 16px;
  }
  
  .header-tip {
    font-size: 12px;
    color: #909399;
  }
  
  .scene-tags {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .scene-tag-card {
    background: #f5f7fa;
    border-radius: 8px;
    padding: 16px;
    transition: all 0.3s;
    
    &:hover {
      background: #e6f7ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
    }
    
    .tag-name {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 8px;
    }
    
    .tag-desc {
      font-size: 13px;
      color: #909399;
      margin-bottom: 12px;
    }
    
    .tag-stats {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      
      .tag-count {
        color: #1890ff;
        font-weight: 500;
      }
      
      .tag-revenue {
        color: #52c41a;
        font-weight: 500;
      }
    }
  }
  
  .text-danger {
    color: #ff4d4f;
  }
  
  .text-success {
    color: #52c41a;
  }
}
</style>


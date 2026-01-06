<template>
  <div class="aov-anomaly">
    <!-- 概览统计 -->
    <el-row :gutter="16" class="overview-row">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <div class="stat-value">¥{{ avgAOV.toFixed(2) }}</div>
            <div class="stat-label">平均客单价</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card warning">
          <div class="stat-icon">📉</div>
          <div class="stat-content">
            <div class="stat-value">{{ lowAOVCount }}</div>
            <div class="stat-label">低于均值30%的订单</div>
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card success">
          <div class="stat-icon">📈</div>
          <div class="stat-content">
            <div class="stat-value">{{ highAOVCount }}</div>
            <div class="stat-label">高于均值50%的订单</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 客单价分布图 -->
    <div class="chart-section">
      <h4>📊 客单价分布</h4>
      <G2PlotChart
        type="column"
        :data="distributionData"
        :config="distributionConfig"
        height="300px"
        :loading="loading"
      />
    </div>
    
    <!-- 异常订单列表 -->
    <div class="anomaly-section">
      <div class="section-header">
        <h4>⚠️ 客单价异常订单</h4>
        <el-radio-group v-model="anomalyType" size="small">
          <el-radio-button label="low">偏低</el-radio-button>
          <el-radio-button label="high">偏高</el-radio-button>
        </el-radio-group>
      </div>
      
      <el-table :data="filteredAnomalyOrders" stripe v-loading="loading">
        <el-table-column prop="order_date" label="日期" width="100" />
        <el-table-column prop="order_id" label="订单号" width="140" />
        <el-table-column prop="store_name" label="门店" width="100" />
        <el-table-column prop="platform" label="平台" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.platform }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="订单金额" width="100" align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(row.total_amount)">
              ¥{{ row.total_amount?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="item_count" label="商品数" width="80" align="right" />
        <el-table-column prop="deviation" label="偏离度" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.deviation < 0 ? 'text-danger' : 'text-success'">
              {{ row.deviation > 0 ? '+' : '' }}{{ (row.deviation * 100).toFixed(1) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="可能原因" min-width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="getReasonType(row.reason)">
              {{ row.reason || '待分析' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 分析建议 -->
    <div class="suggestion-section">
      <h4>💡 优化建议</h4>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-alert
            title="提升低客单价订单"
            type="warning"
            :closable="false"
          >
            <template #default>
              <ul class="suggestion-list">
                <li>设置满减活动，引导凑单</li>
                <li>推荐搭配商品，提升连带率</li>
                <li>设置起送门槛，筛选优质订单</li>
              </ul>
            </template>
          </el-alert>
        </el-col>
        <el-col :span="12">
          <el-alert
            title="维护高客单价客户"
            type="success"
            :closable="false"
          >
            <template #default>
              <ul class="suggestion-list">
                <li>建立VIP客户标签，重点维护</li>
                <li>提供专属优惠券，增加粘性</li>
                <li>分析高客单品类，加强推广</li>
              </ul>
            </template>
          </el-alert>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import G2PlotChart from '@/components/charts/G2PlotChart.vue'

interface Props {
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

// State
const anomalyType = ref<'low' | 'high'>('low')
const avgAOV = ref(68.5)

// 模拟数据
const distributionData = ref([
  { range: '0-20', count: 120 },
  { range: '20-40', count: 280 },
  { range: '40-60', count: 450 },
  { range: '60-80', count: 380 },
  { range: '80-100', count: 220 },
  { range: '100-150', count: 150 },
  { range: '150+', count: 80 }
])

const anomalyOrders = ref([
  { order_date: '2024-01-15', order_id: 'MT20240115001', store_name: '门店A', platform: '美团', total_amount: 15.5, item_count: 1, deviation: -0.77, reason: '仅购买单品' },
  { order_date: '2024-01-15', order_id: 'MT20240115002', store_name: '门店B', platform: '饿了么', total_amount: 22.0, item_count: 2, deviation: -0.68, reason: '促销活动' },
  { order_date: '2024-01-14', order_id: 'MT20240114003', store_name: '门店A', platform: '美团', total_amount: 188.0, item_count: 8, deviation: 1.74, reason: '团购订单' },
  { order_date: '2024-01-14', order_id: 'MT20240114004', store_name: '门店C', platform: '抖音', total_amount: 156.0, item_count: 6, deviation: 1.28, reason: '高价商品' }
])

const distributionConfig = {
  xField: 'range',
  yField: 'count',
  label: {
    position: 'top',
    style: { fontSize: 12 }
  },
  color: '#1890ff',
  columnStyle: {
    radius: [4, 4, 0, 0]
  },
  xAxis: {
    label: {
      formatter: (text: string) => '¥' + text
    }
  }
}

// Computed
const lowAOVCount = computed(() => {
  return anomalyOrders.value.filter(o => o.deviation < -0.3).length
})

const highAOVCount = computed(() => {
  return anomalyOrders.value.filter(o => o.deviation > 0.5).length
})

const filteredAnomalyOrders = computed(() => {
  return anomalyOrders.value.filter(o => {
    return anomalyType.value === 'low' ? o.deviation < -0.3 : o.deviation > 0.5
  })
})

// Methods
const getAmountClass = (amount: number) => {
  const deviation = (amount - avgAOV.value) / avgAOV.value
  if (deviation < -0.3) return 'text-danger'
  if (deviation > 0.5) return 'text-success'
  return ''
}

const getReasonType = (reason: string) => {
  if (reason?.includes('促销')) return 'warning'
  if (reason?.includes('团购')) return 'success'
  if (reason?.includes('单品')) return 'danger'
  return 'info'
}
</script>

<style lang="scss" scoped>
.aov-anomaly {
  .overview-row {
    margin-bottom: 24px;
  }
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    
    &.warning {
      background: linear-gradient(135deg, #fffbe6 0%, #fff 100%);
      border: 1px solid #ffe58f;
    }
    
    &.success {
      background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
      border: 1px solid #b7eb8f;
    }
    
    .stat-icon {
      font-size: 32px;
    }
    
    .stat-content {
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: #303133;
      }
      
      .stat-label {
        font-size: 13px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }
  
  .chart-section,
  .anomaly-section,
  .suggestion-section {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 16px;
    }
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h4 {
      margin: 0;
    }
  }
  
  .suggestion-list {
    margin: 8px 0 0;
    padding-left: 20px;
    
    li {
      line-height: 1.8;
      color: #606266;
    }
  }
  
  .text-danger {
    color: #ff4d4f;
    font-weight: 500;
  }
  
  .text-success {
    color: #52c41a;
    font-weight: 500;
  }
}
</style>


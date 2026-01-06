<template>
  <div class="urgent-issues">
    <!-- 问题汇总 -->
    <div class="issue-summary">
      <div class="summary-item">
        <el-icon :size="32" color="#ff4d4f"><Warning /></el-icon>
        <div class="summary-content">
          <div class="summary-value">{{ overflowOrders.length }}</div>
          <div class="summary-label">穿底订单</div>
        </div>
      </div>
      <div class="summary-item">
        <el-icon :size="32" color="#ff4d4f"><Money /></el-icon>
        <div class="summary-content">
          <div class="summary-value">¥{{ totalLoss.toFixed(2) }}</div>
          <div class="summary-label">总损失金额</div>
        </div>
      </div>
    </div>
    
    <!-- 穿底订单表格 -->
    <div class="overflow-section">
      <div class="section-header">
        <h4>📉 穿底订单（利润为负）</h4>
        <el-tag type="danger" size="small">需立即处理</el-tag>
      </div>
      
      <el-table
        :data="overflowOrders"
        stripe
        :row-class-name="getRowClassName"
        v-loading="loading"
        @row-click="handleRowClick"
        style="cursor: pointer;"
      >
        <el-table-column prop="order_date" label="日期" width="100" />
        <el-table-column prop="order_id" label="订单号" width="140" />
        <el-table-column prop="store_name" label="门店" min-width="100" />
        <el-table-column prop="platform" label="平台" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getPlatformType(row.platform)">
              {{ row.platform }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="商品" min-width="150" show-overflow-tooltip />
        <el-table-column prop="quantity" label="数量" width="60" align="right" />
        <el-table-column prop="total_amount" label="订单金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="profit" label="利润" width="100" align="right">
          <template #default="{ row }">
            <span class="text-danger font-bold">
              ¥{{ row.profit?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="overflow_reason" label="穿底原因" min-width="120">
          <template #default="{ row }">
            <el-tag 
              size="small" 
              :type="getReasonType(row.overflow_reason)"
            >
              {{ row.overflow_reason || '待分析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="handleViewDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 损失分析图表 -->
    <div class="loss-analysis" v-if="overflowOrders.length > 0">
      <div class="section-header">
        <h4>📊 损失分布分析</h4>
      </div>
      
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="chart-card">
            <h5>按门店分布</h5>
            <PieChart
              :data="storeLossData"
              angle-field="loss"
              color-field="store"
              height="250px"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="chart-card">
            <h5>按原因分布</h5>
            <PieChart
              :data="reasonLossData"
              angle-field="loss"
              color-field="reason"
              height="250px"
            />
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 处理建议 -->
    <div class="suggestions" v-if="overflowOrders.length > 0">
      <div class="section-header">
        <h4>💡 处理建议</h4>
      </div>
      <el-alert
        v-for="(suggestion, index) in suggestions"
        :key="index"
        :title="suggestion.title"
        :type="suggestion.type"
        :description="suggestion.description"
        show-icon
        :closable="false"
        style="margin-bottom: 12px;"
      />
    </div>
    
    <!-- 空状态 -->
    <el-empty v-if="overflowOrders.length === 0 && !loading" description="太棒了！暂无穿底订单">
      <template #image>
        <el-icon :size="80" color="#52c41a"><CircleCheck /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Warning, Money, CircleCheck } from '@element-plus/icons-vue'
import type { OverflowOrder } from '@/api/types'
import PieChart from '@/components/charts/PieChart.vue'

interface Props {
  overflowOrders: OverflowOrder[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  viewDetail: [order: OverflowOrder]
}>()

// Computed
const totalLoss = computed(() => {
  return props.overflowOrders.reduce((sum, order) => {
    return sum + Math.abs(order.profit < 0 ? order.profit : 0)
  }, 0)
})

const storeLossData = computed(() => {
  const storeMap = new Map<string, number>()
  props.overflowOrders.forEach(order => {
    const store = order.store_name || '未知门店'
    const current = storeMap.get(store) || 0
    storeMap.set(store, current + Math.abs(order.profit))
  })
  return Array.from(storeMap.entries()).map(([store, loss]) => ({
    store,
    loss
  }))
})

const reasonLossData = computed(() => {
  const reasonMap = new Map<string, number>()
  props.overflowOrders.forEach(order => {
    const reason = order.overflow_reason || '待分析'
    const current = reasonMap.get(reason) || 0
    reasonMap.set(reason, current + Math.abs(order.profit))
  })
  return Array.from(reasonMap.entries()).map(([reason, loss]) => ({
    reason,
    loss
  }))
})

const suggestions = computed(() => {
  const items: Array<{ title: string; description: string; type: 'warning' | 'error' | 'info' }> = []
  
  if (props.overflowOrders.length > 10) {
    items.push({
      title: '穿底订单过多',
      description: '建议检查商品定价策略，可能存在批量定价错误或促销力度过大的情况。',
      type: 'error'
    })
  }
  
  // 检查配送费问题
  const highDeliveryCount = props.overflowOrders.filter(o => 
    o.loss_breakdown?.delivery_loss > o.total_amount * 0.3
  ).length
  if (highDeliveryCount > 0) {
    items.push({
      title: `${highDeliveryCount} 单配送费过高`,
      description: '建议与配送服务商协商费率，或调整配送范围策略。',
      type: 'warning'
    })
  }
  
  // 检查促销问题
  const highPromoCount = props.overflowOrders.filter(o =>
    o.loss_breakdown?.promo_loss > o.total_amount * 0.2
  ).length
  if (highPromoCount > 0) {
    items.push({
      title: `${highPromoCount} 单促销折扣过大`,
      description: '建议审核促销活动设置，确保折扣在可接受范围内。',
      type: 'warning'
    })
  }
  
  if (items.length === 0) {
    items.push({
      title: '正在分析问题原因',
      description: '系统正在分析穿底订单的具体原因，请稍后查看详细报告。',
      type: 'info'
    })
  }
  
  return items
})

// Methods
const getRowClassName = ({ row }: { row: OverflowOrder }) => {
  const loss = Math.abs(row.profit)
  if (loss > 50) return 'row-critical'
  if (loss > 20) return 'row-danger'
  return 'row-warning'
}

const getPlatformType = (platform: string) => {
  switch (platform) {
    case '美团': return 'warning'
    case '饿了么': return 'primary'
    case '抖音': return 'danger'
    default: return 'info'
  }
}

const getReasonType = (reason: string) => {
  if (reason?.includes('配送')) return 'warning'
  if (reason?.includes('促销')) return 'danger'
  if (reason?.includes('成本')) return 'info'
  return 'info'
}

const handleRowClick = (row: OverflowOrder) => {
  emit('viewDetail', row)
}

const handleViewDetail = (row: OverflowOrder) => {
  emit('viewDetail', row)
}
</script>

<style lang="scss" scoped>
.urgent-issues {
  .issue-summary {
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    padding: 20px;
    background: linear-gradient(135deg, #fff2f0 0%, #fff 100%);
    border-radius: 8px;
    border: 1px solid #ffccc7;
  }
  
  .summary-item {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .summary-content {
    .summary-value {
      font-size: 28px;
      font-weight: 700;
      color: #ff4d4f;
    }
    
    .summary-label {
      font-size: 13px;
      color: #909399;
    }
  }
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  .overflow-section {
    margin-bottom: 24px;
  }
  
  .loss-analysis {
    margin-bottom: 24px;
    
    .chart-card {
      background: #fafafa;
      border-radius: 8px;
      padding: 16px;
      
      h5 {
        font-size: 14px;
        color: #606266;
        margin: 0 0 12px;
      }
    }
  }
  
  .suggestions {
    margin-top: 24px;
  }
  
  .text-danger {
    color: #ff4d4f;
  }
  
  .font-bold {
    font-weight: 600;
  }
  
  :deep(.row-critical) {
    background-color: #fff1f0 !important;
  }
  
  :deep(.row-danger) {
    background-color: #fff7e6 !important;
  }
  
  :deep(.row-warning) {
    background-color: #fffbe6 !important;
  }
}
</style>


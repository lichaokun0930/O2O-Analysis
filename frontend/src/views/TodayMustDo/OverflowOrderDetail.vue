<template>
  <div class="overflow-order-detail">
    <!-- 订单基本信息 -->
    <el-descriptions title="订单信息" :column="2" border>
      <el-descriptions-item label="订单号">{{ order.order_id }}</el-descriptions-item>
      <el-descriptions-item label="订单日期">{{ order.order_date }}</el-descriptions-item>
      <el-descriptions-item label="门店">{{ order.store_name }}</el-descriptions-item>
      <el-descriptions-item label="平台">
        <el-tag size="small">{{ order.platform }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="商品名称" :span="2">{{ order.product_name }}</el-descriptions-item>
      <el-descriptions-item label="数量">{{ order.quantity }}</el-descriptions-item>
      <el-descriptions-item label="单价">¥{{ order.unit_price?.toFixed(2) }}</el-descriptions-item>
    </el-descriptions>
    
    <!-- 财务明细 -->
    <div class="finance-section">
      <h4>💰 财务明细</h4>
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="finance-item">
            <div class="finance-label">订单金额</div>
            <div class="finance-value">¥{{ order.total_amount?.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="finance-item">
            <div class="finance-label">商品成本</div>
            <div class="finance-value">¥{{ order.cost?.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="finance-item">
            <div class="finance-label">利润</div>
            <div class="finance-value danger">¥{{ order.profit?.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="finance-item">
            <div class="finance-label">利润率</div>
            <div class="finance-value danger">{{ (order.profit_rate * 100)?.toFixed(2) }}%</div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 损失分解 -->
    <div class="loss-breakdown" v-if="order.loss_breakdown">
      <h4>📊 损失分解</h4>
      <div class="breakdown-chart">
        <div 
          v-for="(value, key) in order.loss_breakdown" 
          :key="key"
          class="breakdown-bar"
        >
          <div class="bar-label">{{ getLossLabel(key) }}</div>
          <div class="bar-container">
            <div 
              class="bar-fill" 
              :style="{ width: getBarWidth(value) + '%', background: getLossColor(key) }"
            ></div>
          </div>
          <div class="bar-value">¥{{ Math.abs(value).toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="breakdown-summary">
        <span class="summary-label">总损失:</span>
        <span class="summary-value">¥{{ totalLoss.toFixed(2) }}</span>
      </div>
    </div>
    
    <!-- 穿底原因 -->
    <div class="reason-section">
      <h4>🔍 穿底原因分析</h4>
      <el-alert
        :title="order.overflow_reason || '待分析'"
        :type="getReasonAlertType(order.overflow_reason)"
        show-icon
        :closable="false"
      >
        <template #default>
          <p>{{ getReasonDescription(order.overflow_reason) }}</p>
        </template>
      </el-alert>
    </div>
    
    <!-- 处理建议 -->
    <div class="suggestion-section">
      <h4>💡 处理建议</h4>
      <el-steps direction="vertical" :active="0">
        <el-step 
          v-for="(step, index) in suggestions" 
          :key="index"
          :title="step.title"
          :description="step.description"
        />
      </el-steps>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { OverflowOrder } from '@/api/types'

interface Props {
  order: OverflowOrder
}

const props = defineProps<Props>()

// Computed
const totalLoss = computed(() => {
  if (!props.order.loss_breakdown) return Math.abs(props.order.profit)
  return Object.values(props.order.loss_breakdown).reduce((sum, val) => sum + Math.abs(val), 0)
})

const suggestions = computed(() => {
  const reason = props.order.overflow_reason
  
  if (reason?.includes('配送')) {
    return [
      { title: '核查配送费设置', description: '检查该区域配送费是否设置合理' },
      { title: '优化配送范围', description: '考虑缩小配送范围或调整配送费率' },
      { title: '与骑手协商', description: '与配送服务商协商降低配送成本' }
    ]
  }
  
  if (reason?.includes('促销')) {
    return [
      { title: '审核促销规则', description: '检查促销活动设置是否存在漏洞' },
      { title: '设置优惠上限', description: '为促销活动设置最大折扣限制' },
      { title: '排除亏本商品', description: '将低利润商品排除出促销范围' }
    ]
  }
  
  return [
    { title: '分析订单成本', description: '详细核算该订单各项成本' },
    { title: '调整商品定价', description: '根据成本重新评估定价策略' },
    { title: '优化供应链', description: '寻找更低成本的供应渠道' }
  ]
})

// Methods
const getLossLabel = (key: string) => {
  const labels: Record<string, string> = {
    product_loss: '商品亏损',
    delivery_loss: '配送亏损',
    platform_loss: '平台费用',
    promo_loss: '促销折扣'
  }
  return labels[key] || key
}

const getLossColor = (key: string) => {
  const colors: Record<string, string> = {
    product_loss: '#ff4d4f',
    delivery_loss: '#faad14',
    platform_loss: '#1890ff',
    promo_loss: '#722ed1'
  }
  return colors[key] || '#909399'
}

const getBarWidth = (value: number) => {
  if (totalLoss.value === 0) return 0
  return (Math.abs(value) / totalLoss.value) * 100
}

const getReasonAlertType = (reason: string) => {
  if (reason?.includes('配送')) return 'warning'
  if (reason?.includes('促销')) return 'error'
  if (reason?.includes('成本')) return 'info'
  return 'info'
}

const getReasonDescription = (reason: string) => {
  if (reason?.includes('配送')) {
    return '该订单配送费用过高，导致整体利润为负。建议检查配送设置或与配送商协商费率。'
  }
  if (reason?.includes('促销')) {
    return '促销折扣力度过大，导致商品售价低于成本。建议审核促销规则，设置合理的折扣上限。'
  }
  if (reason?.includes('成本')) {
    return '商品成本高于售价，可能是定价策略问题或成本上涨未及时调价。建议重新评估定价。'
  }
  return '系统正在分析该订单的穿底原因，请稍后查看详细报告。'
}
</script>

<style lang="scss" scoped>
.overflow-order-detail {
  .finance-section,
  .loss-breakdown,
  .reason-section,
  .suggestion-section {
    margin-top: 24px;
    
    h4 {
      font-size: 15px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 16px;
    }
  }
  
  .finance-item {
    background: #f5f7fa;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    
    .finance-label {
      font-size: 13px;
      color: #909399;
      margin-bottom: 8px;
    }
    
    .finance-value {
      font-size: 20px;
      font-weight: 700;
      color: #303133;
      
      &.danger {
        color: #ff4d4f;
      }
    }
  }
  
  .breakdown-chart {
    .breakdown-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
      
      .bar-label {
        width: 80px;
        font-size: 13px;
        color: #606266;
      }
      
      .bar-container {
        flex: 1;
        height: 20px;
        background: #f0f0f0;
        border-radius: 4px;
        overflow: hidden;
      }
      
      .bar-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s;
      }
      
      .bar-value {
        width: 80px;
        text-align: right;
        font-size: 14px;
        font-weight: 500;
        color: #ff4d4f;
      }
    }
  }
  
  .breakdown-summary {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px dashed #e4e7ed;
    
    .summary-label {
      font-size: 14px;
      color: #606266;
    }
    
    .summary-value {
      font-size: 18px;
      font-weight: 700;
      color: #ff4d4f;
    }
  }
}
</style>


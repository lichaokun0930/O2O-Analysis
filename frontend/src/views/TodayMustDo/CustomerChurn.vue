<template>
  <div class="customer-churn">
    <!-- 流失概览 -->
    <el-row :gutter="16" class="overview-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ churnData?.total_customers || 0 }}</div>
          <div class="stat-label">总客户数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value success">{{ churnData?.active_customers || 0 }}</div>
          <div class="stat-label">活跃客户</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value danger">{{ churnData?.churned_customers || 0 }}</div>
          <div class="stat-label">流失客户</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value" :class="churnRateClass">
            {{ ((churnData?.churn_rate || 0) * 100).toFixed(1) }}%
          </div>
          <div class="stat-label">流失率</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 筛选条件 -->
    <div class="filter-row">
      <span class="filter-label">流失判定阈值:</span>
      <el-radio-group v-model="daysThreshold" @change="handleThresholdChange">
        <el-radio-button :label="30">30天</el-radio-button>
        <el-radio-button :label="60">60天</el-radio-button>
        <el-radio-button :label="90">90天</el-radio-button>
      </el-radio-group>
    </div>
    
    <el-row :gutter="16">
      <!-- 流失原因分析 -->
      <el-col :span="8">
        <div class="analysis-card">
          <h4>📊 流失原因分布</h4>
          <div class="reason-list" v-if="churnData?.churn_reasons?.length">
            <div 
              v-for="reason in churnData.churn_reasons" 
              :key="reason.reason"
              class="reason-item"
            >
              <div class="reason-info">
                <span class="reason-name">{{ reason.reason }}</span>
                <span class="reason-count">{{ reason.customer_count }} 人</span>
              </div>
              <el-progress 
                :percentage="reason.percentage * 100" 
                :stroke-width="8"
                :color="getReasonColor(reason.reason)"
              />
            </div>
          </div>
          <el-empty v-else description="暂无数据" :image-size="80" />
        </div>
      </el-col>
      
      <!-- 高风险客户列表 -->
      <el-col :span="16">
        <div class="analysis-card">
          <div class="card-header">
            <h4>⚠️ 高风险流失客户</h4>
            <el-tag type="danger" size="small">需重点关注</el-tag>
          </div>
          
          <el-table 
            :data="atRiskCustomers" 
            stripe 
            v-loading="loading"
            max-height="400"
          >
            <el-table-column prop="customer_id" label="客户ID" width="120" />
            <el-table-column prop="last_order_date" label="最后下单" width="110" />
            <el-table-column prop="total_orders" label="历史订单" width="90" align="right" />
            <el-table-column prop="total_spent" label="累计消费" width="110" align="right">
              <template #default="{ row }">
                ¥{{ row.total_spent?.toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column prop="days_since_last_order" label="未下单天数" width="100" align="right">
              <template #default="{ row }">
                <span :class="getDaysClass(row.days_since_last_order)">
                  {{ row.days_since_last_order }} 天
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="risk_score" label="风险分" width="90" align="center">
              <template #default="{ row }">
                <el-progress
                  type="circle"
                  :percentage="row.risk_score"
                  :width="40"
                  :stroke-width="4"
                  :color="getRiskColor(row.risk_score)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="suggested_action" label="建议行动" min-width="150">
              <template #default="{ row }">
                <el-tag size="small" type="warning">
                  {{ row.suggested_action }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { CustomerChurnAnalysis } from '@/api/types'

interface Props {
  churnData: CustomerChurnAnalysis | null
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const emit = defineEmits<{
  refresh: [daysThreshold: number]
}>()

const daysThreshold = ref(30)

// Computed
const churnRateClass = computed(() => {
  const rate = props.churnData?.churn_rate || 0
  if (rate > 0.3) return 'danger'
  if (rate > 0.15) return 'warning'
  return 'success'
})

const atRiskCustomers = computed(() => {
  return props.churnData?.at_risk_customers || []
})

// Methods
const handleThresholdChange = (value: number) => {
  emit('refresh', value)
}

const getReasonColor = (reason: string) => {
  if (reason.includes('价格')) return '#ff4d4f'
  if (reason.includes('服务')) return '#faad14'
  if (reason.includes('竞争')) return '#722ed1'
  return '#1890ff'
}

const getDaysClass = (days: number) => {
  if (days > 60) return 'text-danger'
  if (days > 30) return 'text-warning'
  return ''
}

const getRiskColor = (score: number) => {
  if (score >= 80) return '#ff4d4f'
  if (score >= 60) return '#faad14'
  return '#52c41a'
}
</script>

<style lang="scss" scoped>
.customer-churn {
  .overview-row {
    margin-bottom: 24px;
  }
  
  .stat-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    
    .stat-value {
      font-size: 32px;
      font-weight: 700;
      color: #303133;
      
      &.success { color: #52c41a; }
      &.danger { color: #ff4d4f; }
      &.warning { color: #faad14; }
    }
    
    .stat-label {
      font-size: 13px;
      color: #909399;
      margin-top: 8px;
    }
  }
  
  .filter-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 8px;
    
    .filter-label {
      font-size: 14px;
      color: #606266;
    }
  }
  
  .analysis-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    height: 100%;
    
    .card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }
    
    h4 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0 0 16px;
    }
  }
  
  .reason-list {
    .reason-item {
      margin-bottom: 16px;
      
      .reason-info {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        
        .reason-name {
          font-size: 14px;
          color: #303133;
        }
        
        .reason-count {
          font-size: 13px;
          color: #909399;
        }
      }
    }
  }
  
  .text-danger {
    color: #ff4d4f;
    font-weight: 500;
  }
  
  .text-warning {
    color: #faad14;
  }
}
</style>


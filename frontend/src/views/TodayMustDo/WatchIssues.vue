<template>
  <div class="watch-issues">
    <div class="issue-cards" v-loading="loading">
      <div 
        v-for="issue in issues" 
        :key="issue.id"
        class="issue-card"
        :class="`issue-card--${issue.type}`"
      >
        <div class="issue-card__header">
          <span class="issue-icon">{{ getIssueIcon(issue.type) }}</span>
          <span class="issue-title">{{ issue.title }}</span>
          <el-tag size="small" :type="getTrendType(issue.trend)">
            {{ getTrendText(issue.trend) }}
          </el-tag>
        </div>
        
        <div class="issue-card__body">
          <p class="issue-desc">{{ issue.description }}</p>
          
          <div class="issue-metrics">
            <div class="metric">
              <span class="metric-label">当前值</span>
              <span class="metric-value">{{ formatMetricValue(issue.metric_value, issue.type) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">阈值</span>
              <span class="metric-value threshold">{{ formatMetricValue(issue.threshold, issue.type) }}</span>
            </div>
            <div class="metric">
              <span class="metric-label">偏离度</span>
              <span class="metric-value" :class="getDeviationClass(issue)">
                {{ getDeviation(issue) }}
              </span>
            </div>
          </div>
        </div>
        
        <div class="issue-card__footer">
          <el-button type="primary" text size="small">
            <el-icon><View /></el-icon>
            查看详情
          </el-button>
          <el-button type="warning" text size="small">
            <el-icon><Bell /></el-icon>
            设置提醒
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <el-empty v-if="issues.length === 0 && !loading" description="暂无需要关注的问题">
      <template #image>
        <el-icon :size="80" color="#faad14"><InfoFilled /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { View, Bell, InfoFilled } from '@element-plus/icons-vue'
import type { WatchIssue } from '@/api/types'

interface Props {
  issues: WatchIssue[]
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

// Methods
const getIssueIcon = (type: string) => {
  switch (type) {
    case 'traffic_drop': return '📉'
    case 'slow_moving': return '📦'
    case 'price_abnormal': return '💰'
    case 'review_warning': return '⭐'
    default: return '⚠️'
  }
}

const getTrendType = (trend: string) => {
  switch (trend) {
    case 'up': return 'success'
    case 'down': return 'danger'
    default: return 'info'
  }
}

const getTrendText = (trend: string) => {
  switch (trend) {
    case 'up': return '上升中'
    case 'down': return '下降中'
    default: return '持平'
  }
}

const formatMetricValue = (value: number, type: string) => {
  if (type === 'price_abnormal') {
    return '¥' + value.toFixed(2)
  }
  if (type === 'traffic_drop') {
    return value.toFixed(1) + '%'
  }
  return value.toString()
}

const getDeviation = (issue: WatchIssue) => {
  const deviation = ((issue.metric_value - issue.threshold) / issue.threshold * 100).toFixed(1)
  return (parseFloat(deviation) > 0 ? '+' : '') + deviation + '%'
}

const getDeviationClass = (issue: WatchIssue) => {
  const deviation = (issue.metric_value - issue.threshold) / issue.threshold
  if (issue.type === 'traffic_drop') {
    return deviation < 0 ? 'text-danger' : 'text-success'
  }
  return deviation > 0 ? 'text-danger' : 'text-success'
}
</script>

<style lang="scss" scoped>
.watch-issues {
  .issue-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 16px;
  }
  
  .issue-card {
    background: #fff;
    border-radius: 8px;
    border: 1px solid #e4e7ed;
    overflow: hidden;
    transition: all 0.3s;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }
    
    &--traffic_drop {
      border-left: 4px solid #ff4d4f;
    }
    
    &--slow_moving {
      border-left: 4px solid #faad14;
    }
    
    &--price_abnormal {
      border-left: 4px solid #722ed1;
    }
    
    &--review_warning {
      border-left: 4px solid #1890ff;
    }
    
    &__header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 16px;
      background: #fafafa;
      border-bottom: 1px solid #f0f0f0;
      
      .issue-icon {
        font-size: 20px;
      }
      
      .issue-title {
        flex: 1;
        font-weight: 600;
        color: #303133;
      }
    }
    
    &__body {
      padding: 16px;
      
      .issue-desc {
        font-size: 13px;
        color: #606266;
        margin: 0 0 16px;
        line-height: 1.6;
      }
      
      .issue-metrics {
        display: flex;
        gap: 24px;
        
        .metric {
          .metric-label {
            display: block;
            font-size: 12px;
            color: #909399;
            margin-bottom: 4px;
          }
          
          .metric-value {
            font-size: 18px;
            font-weight: 600;
            color: #303133;
            
            &.threshold {
              color: #909399;
            }
          }
        }
      }
    }
    
    &__footer {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 12px 16px;
      background: #fafafa;
      border-top: 1px solid #f0f0f0;
    }
  }
  
  .text-danger {
    color: #ff4d4f !important;
  }
  
  .text-success {
    color: #52c41a !important;
  }
}
</style>


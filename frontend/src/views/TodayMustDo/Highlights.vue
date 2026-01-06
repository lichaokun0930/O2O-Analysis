<template>
  <div class="highlights">
    <div class="highlight-cards" v-loading="loading">
      <div 
        v-for="highlight in highlights" 
        :key="highlight.id"
        class="highlight-card"
      >
        <div class="highlight-card__icon">
          {{ getHighlightIcon(highlight.type) }}
        </div>
        
        <div class="highlight-card__content">
          <h4 class="highlight-title">{{ highlight.title }}</h4>
          <p class="highlight-desc">{{ highlight.description }}</p>
          
          <div class="highlight-stats">
            <div class="stat">
              <span class="stat-value">{{ formatValue(highlight.metric_value) }}</span>
              <span class="stat-label">{{ getMetricLabel(highlight.type) }}</span>
            </div>
            <div class="stat growth">
              <el-icon v-if="highlight.growth_rate > 0"><ArrowUp /></el-icon>
              <el-icon v-else><ArrowDown /></el-icon>
              <span class="stat-value" :class="highlight.growth_rate > 0 ? 'up' : 'down'">
                {{ Math.abs(highlight.growth_rate).toFixed(1) }}%
              </span>
              <span class="stat-label">环比</span>
            </div>
          </div>
        </div>
        
        <div class="highlight-card__badge">
          <el-tag type="success" size="small">亮点</el-tag>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <el-empty v-if="highlights.length === 0 && !loading" description="暂无亮点数据">
      <template #image>
        <el-icon :size="80" color="#52c41a"><Trophy /></el-icon>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { ArrowUp, ArrowDown, Trophy } from '@element-plus/icons-vue'
import type { Highlight } from '@/api/types'

interface Props {
  highlights: Highlight[]
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false
})

// Methods
const getHighlightIcon = (type: string) => {
  switch (type) {
    case 'hot_product': return '🔥'
    case 'high_profit': return '💰'
    case 'new_customer': return '👥'
    case 'repeat_order': return '🔄'
    default: return '⭐'
  }
}

const getMetricLabel = (type: string) => {
  switch (type) {
    case 'hot_product': return '销量'
    case 'high_profit': return '利润'
    case 'new_customer': return '新客数'
    case 'repeat_order': return '复购率'
    default: return '数值'
  }
}

const formatValue = (value: number) => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + '万'
  }
  if (value < 1) {
    return (value * 100).toFixed(1) + '%'
  }
  return value.toLocaleString()
}
</script>

<style lang="scss" scoped>
.highlights {
  .highlight-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  
  .highlight-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
    border: 1px solid #b7eb8f;
    border-radius: 8px;
    padding: 20px;
    position: relative;
    transition: all 0.3s;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(82, 196, 26, 0.15);
      transform: translateY(-2px);
    }
    
    &__icon {
      font-size: 32px;
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    &__content {
      flex: 1;
      
      .highlight-title {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        margin: 0 0 8px;
      }
      
      .highlight-desc {
        font-size: 13px;
        color: #606266;
        margin: 0 0 16px;
        line-height: 1.5;
      }
      
      .highlight-stats {
        display: flex;
        gap: 24px;
        
        .stat {
          display: flex;
          flex-direction: column;
          
          &.growth {
            flex-direction: row;
            align-items: center;
            gap: 4px;
            
            .el-icon {
              font-size: 14px;
            }
          }
          
          .stat-value {
            font-size: 20px;
            font-weight: 700;
            color: #52c41a;
            
            &.up {
              color: #52c41a;
            }
            
            &.down {
              color: #ff4d4f;
            }
          }
          
          .stat-label {
            font-size: 12px;
            color: #909399;
          }
        }
      }
    }
    
    &__badge {
      position: absolute;
      top: 12px;
      right: 12px;
    }
  }
}
</style>


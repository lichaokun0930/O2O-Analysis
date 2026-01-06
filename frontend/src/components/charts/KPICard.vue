<template>
  <div class="kpi-card" :class="[`kpi-card--${variant}`, { 'kpi-card--clickable': clickable }]" @click="handleClick">
    <div class="kpi-card__header">
      <span class="kpi-card__title">{{ title }}</span>
      <el-tooltip v-if="tooltip" :content="tooltip" placement="top">
        <el-icon class="kpi-card__info"><InfoFilled /></el-icon>
      </el-tooltip>
    </div>
    
    <div class="kpi-card__body">
      <div class="kpi-card__value" :style="{ color: valueColor }">
        <span v-if="prefix" class="kpi-card__prefix">{{ prefix }}</span>
        <span class="kpi-card__number">{{ formattedValue }}</span>
        <span v-if="suffix" class="kpi-card__suffix">{{ suffix }}</span>
      </div>
      
      <div v-if="showTrend && trend !== undefined" class="kpi-card__trend" :class="trendClass">
        <el-icon v-if="trend > 0"><ArrowUp /></el-icon>
        <el-icon v-else-if="trend < 0"><ArrowDown /></el-icon>
        <el-icon v-else><Minus /></el-icon>
        <span>{{ Math.abs(trend).toFixed(1) }}%</span>
      </div>
    </div>
    
    <div v-if="description" class="kpi-card__footer">
      <span class="kpi-card__desc">{{ description }}</span>
    </div>
    
    <div v-if="icon" class="kpi-card__icon">
      <el-icon :size="40" :color="iconColor">
        <component :is="icon" />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { InfoFilled, ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'

interface Props {
  title: string
  value: number | string
  prefix?: string
  suffix?: string
  trend?: number
  showTrend?: boolean
  description?: string
  tooltip?: string
  icon?: string
  variant?: 'default' | 'urgent' | 'watch' | 'highlight' | 'info'
  color?: string
  clickable?: boolean
  precision?: number
}

const props = withDefaults(defineProps<Props>(), {
  showTrend: true,
  variant: 'default',
  clickable: false,
  precision: 0
})

const emit = defineEmits<{
  click: []
}>()

// 格式化数值
const formattedValue = computed(() => {
  if (typeof props.value === 'string') {
    return props.value
  }
  
  const num = props.value
  
  // 大数字格式化
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  } else if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  
  return num.toFixed(props.precision)
})

// 数值颜色
const valueColor = computed(() => {
  if (props.color) return props.color
  
  switch (props.variant) {
    case 'urgent': return '#ff4d4f'
    case 'watch': return '#faad14'
    case 'highlight': return '#52c41a'
    case 'info': return '#1890ff'
    default: return '#303133'
  }
})

// 图标颜色
const iconColor = computed(() => {
  switch (props.variant) {
    case 'urgent': return 'rgba(255, 77, 79, 0.15)'
    case 'watch': return 'rgba(250, 173, 20, 0.15)'
    case 'highlight': return 'rgba(82, 196, 26, 0.15)'
    case 'info': return 'rgba(24, 144, 255, 0.15)'
    default: return 'rgba(0, 0, 0, 0.05)'
  }
})

// 趋势样式
const trendClass = computed(() => {
  if (!props.trend) return ''
  return props.trend > 0 ? 'kpi-card__trend--up' : 'kpi-card__trend--down'
})

const handleClick = () => {
  if (props.clickable) {
    emit('click')
  }
}
</script>

<style lang="scss" scoped>
.kpi-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  
  &--clickable {
    cursor: pointer;
    
    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
      transform: translateY(-2px);
    }
  }
  
  &--urgent {
    border-left: 4px solid #ff4d4f;
  }
  
  &--watch {
    border-left: 4px solid #faad14;
  }
  
  &--highlight {
    border-left: 4px solid #52c41a;
  }
  
  &--info {
    border-left: 4px solid #1890ff;
  }
  
  &__header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
  
  &__title {
    font-size: 14px;
    color: #909399;
    font-weight: 500;
  }
  
  &__info {
    color: #c0c4cc;
    cursor: help;
    
    &:hover {
      color: #909399;
    }
  }
  
  &__body {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }
  
  &__value {
    display: flex;
    align-items: baseline;
  }
  
  &__prefix {
    font-size: 18px;
    margin-right: 2px;
  }
  
  &__number {
    font-size: 32px;
    font-weight: 700;
    line-height: 1.2;
    font-family: 'DIN Alternate', 'Helvetica Neue', sans-serif;
  }
  
  &__suffix {
    font-size: 14px;
    margin-left: 4px;
    color: #909399;
  }
  
  &__trend {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    padding: 2px 8px;
    border-radius: 4px;
    
    &--up {
      color: #52c41a;
      background-color: #f6ffed;
    }
    
    &--down {
      color: #ff4d4f;
      background-color: #fff2f0;
    }
  }
  
  &__footer {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #f0f0f0;
  }
  
  &__desc {
    font-size: 12px;
    color: #909399;
  }
  
  &__icon {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    opacity: 0.8;
  }
}
</style>


<template>
  <div class="pie-chart">
    <div class="pie-chart__header" v-if="title">
      <h3>{{ title }}</h3>
    </div>
    
    <G2PlotChart
      type="pie"
      :data="data"
      :config="chartConfig"
      :height="height"
      :loading="loading"
    />
    
    <div v-if="showLegend" class="pie-chart__legend">
      <div 
        v-for="(item, index) in data" 
        :key="index"
        class="legend-item"
      >
        <span class="legend-color" :style="{ background: colors[index % colors.length] }"></span>
        <span class="legend-label">{{ item[angleField] }}</span>
        <span class="legend-value">{{ formatValue(item[colorField]) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import G2PlotChart from './G2PlotChart.vue'

interface Props {
  title?: string
  data: Record<string, unknown>[]
  angleField?: string
  colorField?: string
  height?: string
  loading?: boolean
  showLegend?: boolean
  innerRadius?: number
}

const props = withDefaults(defineProps<Props>(), {
  angleField: 'value',
  colorField: 'type',
  height: '300px',
  loading: false,
  showLegend: true,
  innerRadius: 0.6
})

const colors = [
  '#1890ff', '#52c41a', '#faad14', '#ff4d4f',
  '#722ed1', '#13c2c2', '#eb2f96', '#2f54eb'
]

const chartConfig = computed(() => ({
  angleField: props.angleField,
  colorField: props.colorField,
  innerRadius: props.innerRadius,
  radius: 0.8,
  label: {
    type: 'inner',
    offset: '-30%',
    content: ({ percent }: { percent: number }) => `${(percent * 100).toFixed(0)}%`,
    style: {
      fontSize: 14,
      textAlign: 'center',
      fill: '#fff'
    }
  },
  legend: false,
  statistic: props.innerRadius > 0 ? {
    title: {
      content: '总计',
      style: {
        fontSize: '14px',
        color: '#909399'
      }
    },
    content: {
      style: {
        fontSize: '20px',
        fontWeight: 'bold',
        color: '#303133'
      }
    }
  } : false,
  interactions: [
    { type: 'element-active' },
    { type: 'pie-legend-active' }
  ],
  color: colors
}))

const formatValue = (value: unknown) => {
  if (typeof value === 'number') {
    if (value >= 10000) {
      return (value / 10000).toFixed(1) + '万'
    }
    return value.toLocaleString()
  }
  return value
}
</script>

<style lang="scss" scoped>
.pie-chart {
  &__header {
    margin-bottom: 16px;
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  &__legend {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 16px;
    padding: 12px;
    background: #fafafa;
    border-radius: 8px;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }
  
  .legend-color {
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }
  
  .legend-label {
    color: #606266;
  }
  
  .legend-value {
    font-weight: 600;
    color: #303133;
  }
}
</style>


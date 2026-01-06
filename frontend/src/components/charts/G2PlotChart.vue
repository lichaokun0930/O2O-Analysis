<template>
  <div ref="containerRef" class="g2plot-chart" :style="{ height: height }">
    <div v-if="loading" class="chart-loading">
      <el-skeleton :rows="5" animated />
    </div>
    <div v-if="error" class="chart-error">
      <el-empty :description="error" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { 
  Line, Column, Bar, Pie, Area, DualAxes, 
  Gauge, Liquid, Rose, Scatter, Heatmap,
  type LineOptions, type ColumnOptions, type PieOptions
} from '@antv/g2plot'

type ChartType = 'line' | 'column' | 'bar' | 'pie' | 'area' | 'dual-axes' | 
                  'gauge' | 'liquid' | 'rose' | 'scatter' | 'heatmap'

interface Props {
  type: ChartType
  data: unknown[]
  config?: Record<string, unknown>
  height?: string
  loading?: boolean
  error?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false,
  config: () => ({})
})

const containerRef = ref<HTMLElement>()
const chart = shallowRef<unknown>(null)

// 图表类型映射
const chartMap: Record<ChartType, typeof Line> = {
  'line': Line,
  'column': Column,
  'bar': Bar,
  'pie': Pie,
  'area': Area,
  'dual-axes': DualAxes,
  'gauge': Gauge,
  'liquid': Liquid,
  'rose': Rose,
  'scatter': Scatter,
  'heatmap': Heatmap
}

// 默认配置
const getDefaultConfig = (type: ChartType) => {
  const baseConfig = {
    autoFit: true,
    padding: 'auto',
    animation: {
      appear: {
        animation: 'fade-in',
        duration: 300
      }
    }
  }
  
  switch (type) {
    case 'line':
      return {
        ...baseConfig,
        smooth: true,
        point: {
          size: 3,
          shape: 'circle'
        }
      }
    case 'column':
      return {
        ...baseConfig,
        columnWidthRatio: 0.6,
        label: {
          position: 'top',
          style: {
            fill: '#303133',
            fontSize: 12
          }
        }
      }
    case 'pie':
      return {
        ...baseConfig,
        innerRadius: 0.6,
        label: {
          type: 'spider',
          content: '{name}\n{percentage}'
        },
        interactions: [{ type: 'element-active' }]
      }
    case 'area':
      return {
        ...baseConfig,
        smooth: true,
        areaStyle: {
          fillOpacity: 0.3
        }
      }
    case 'gauge':
      return {
        ...baseConfig,
        range: {
          color: ['#52c41a', '#faad14', '#ff4d4f']
        },
        indicator: {
          pointer: {
            style: {
              stroke: '#303133'
            }
          }
        }
      }
    default:
      return baseConfig
  }
}

// 创建图表
const createChart = () => {
  if (!containerRef.value || !props.data?.length) return
  
  destroyChart()
  
  const ChartClass = chartMap[props.type]
  if (!ChartClass) {
    console.error(`不支持的图表类型: ${props.type}`)
    return
  }
  
  const defaultConfig = getDefaultConfig(props.type)
  const config = {
    ...defaultConfig,
    data: props.data,
    ...props.config
  } as LineOptions | ColumnOptions | PieOptions
  
  chart.value = new ChartClass(containerRef.value, config)
  ;(chart.value as { render: () => void }).render()
}

// 更新图表数据
const updateChart = () => {
  if (chart.value && props.data?.length) {
    ;(chart.value as { changeData: (data: unknown[]) => void }).changeData(props.data)
  } else {
    createChart()
  }
}

// 销毁图表
const destroyChart = () => {
  if (chart.value) {
    ;(chart.value as { destroy: () => void }).destroy()
    chart.value = null
  }
}

// 监听数据变化
watch(
  () => props.data,
  () => {
    if (!props.loading) {
      updateChart()
    }
  },
  { deep: true }
)

// 监听配置变化
watch(
  () => props.config,
  () => {
    createChart()
  },
  { deep: true }
)

// 监听类型变化
watch(
  () => props.type,
  () => {
    createChart()
  }
)

onMounted(() => {
  if (!props.loading) {
    createChart()
  }
})

onUnmounted(() => {
  destroyChart()
})

// 暴露方法
defineExpose({
  refresh: createChart,
  getChart: () => chart.value
})
</script>

<style lang="scss" scoped>
.g2plot-chart {
  width: 100%;
  position: relative;
  
  .chart-loading,
  .chart-error {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.8);
    z-index: 10;
  }
}
</style>


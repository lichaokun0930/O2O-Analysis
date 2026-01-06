<template>
  <div ref="containerRef" class="echarts-chart" :style="{ height: height }">
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
import * as echarts from 'echarts'
import type { EChartsOption, ECharts } from 'echarts'

interface Props {
  option: EChartsOption
  height?: string
  loading?: boolean
  error?: string
  theme?: string | object
}

const props = withDefaults(defineProps<Props>(), {
  height: '300px',
  loading: false,
  theme: 'light'
})

const containerRef = ref<HTMLElement>()
const chart = shallowRef<ECharts | null>(null)

// 创建图表
const createChart = () => {
  if (!containerRef.value) return
  
  destroyChart()
  
  chart.value = echarts.init(containerRef.value, props.theme)
  chart.value.setOption(props.option)
}

// 更新图表
const updateChart = () => {
  if (chart.value) {
    chart.value.setOption(props.option, true)
  } else {
    createChart()
  }
}

// 销毁图表
const destroyChart = () => {
  if (chart.value) {
    chart.value.dispose()
    chart.value = null
  }
}

// 响应式调整大小
const handleResize = () => {
  chart.value?.resize()
}

// 监听 option 变化
watch(
  () => props.option,
  () => {
    if (!props.loading) {
      updateChart()
    }
  },
  { deep: true }
)

// 监听 loading 状态
watch(
  () => props.loading,
  (loading) => {
    if (chart.value) {
      if (loading) {
        chart.value.showLoading({
          text: '加载中...',
          color: '#1890ff',
          maskColor: 'rgba(255, 255, 255, 0.8)'
        })
      } else {
        chart.value.hideLoading()
      }
    }
  }
)

onMounted(() => {
  if (!props.loading) {
    createChart()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  destroyChart()
})

// 暴露方法
defineExpose({
  refresh: createChart,
  resize: handleResize,
  getChart: () => chart.value
})
</script>

<style lang="scss" scoped>
.echarts-chart {
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


<template>
  <div class="trend-chart">
    <div class="trend-chart__header" v-if="title">
      <h3>{{ title }}</h3>
      <div class="trend-chart__actions">
        <el-radio-group v-model="granularity" size="small" @change="handleGranularityChange">
          <el-radio-button label="day">日</el-radio-button>
          <el-radio-button label="week">周</el-radio-button>
          <el-radio-button label="month">月</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    
    <G2PlotChart
      type="line"
      :data="chartData"
      :config="chartConfig"
      :height="height"
      :loading="loading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import G2PlotChart from './G2PlotChart.vue'

interface TrendDataItem {
  date: string
  value: number
  label?: string
}

interface Props {
  title?: string
  data: TrendDataItem[]
  xField?: string
  yField?: string
  height?: string
  loading?: boolean
  showGranularity?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  xField: 'date',
  yField: 'value',
  height: '300px',
  loading: false,
  showGranularity: true
})

const emit = defineEmits<{
  granularityChange: [value: 'day' | 'week' | 'month']
}>()

const granularity = ref<'day' | 'week' | 'month'>('day')

const chartData = computed(() => {
  return props.data.map(item => ({
    [props.xField]: item.date,
    [props.yField]: item.value,
    label: item.label
  }))
})

const chartConfig = computed(() => ({
  xField: props.xField,
  yField: props.yField,
  smooth: true,
  point: {
    size: 3,
    shape: 'circle',
    style: {
      fill: '#fff',
      stroke: '#1890ff',
      lineWidth: 2
    }
  },
  lineStyle: {
    stroke: '#1890ff',
    lineWidth: 2
  },
  area: {
    style: {
      fill: 'l(270) 0:rgba(24, 144, 255, 0.4) 1:rgba(24, 144, 255, 0.05)'
    }
  },
  xAxis: {
    label: {
      formatter: (text: string) => {
        if (granularity.value === 'month') {
          return text.substring(0, 7)
        }
        return text.substring(5) // 去掉年份
      }
    }
  },
  yAxis: {
    label: {
      formatter: (v: string) => {
        const num = parseFloat(v)
        if (num >= 10000) {
          return (num / 10000).toFixed(1) + '万'
        }
        return v
      }
    }
  },
  tooltip: {
    showCrosshairs: true,
    crosshairs: {
      type: 'x'
    }
  }
}))

const handleGranularityChange = (value: 'day' | 'week' | 'month') => {
  emit('granularityChange', value)
}
</script>

<style lang="scss" scoped>
.trend-chart {
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
  }
  
  &__actions {
    display: flex;
    gap: 12px;
  }
}
</style>


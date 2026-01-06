<template>
  <div class="filter-panel">
    <el-form :model="filters" inline>
      <!-- 日期范围 -->
      <el-form-item v-if="showDateRange" label="日期范围">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          :shortcuts="dateShortcuts"
          @change="handleDateChange"
        />
      </el-form-item>
      
      <!-- 门店选择 -->
      <el-form-item v-if="showStore" label="门店">
        <el-select
          v-model="filters.store_name"
          placeholder="全部门店"
          clearable
          filterable
          @change="handleFilterChange"
        >
          <el-option
            v-for="store in stores"
            :key="store"
            :label="store"
            :value="store"
          />
        </el-select>
      </el-form-item>
      
      <!-- 平台选择 -->
      <el-form-item v-if="showPlatform" label="平台">
        <el-select
          v-model="filters.platform"
          placeholder="全部平台"
          clearable
          @change="handleFilterChange"
        >
          <el-option label="美团" value="美团" />
          <el-option label="饿了么" value="饿了么" />
          <el-option label="抖音" value="抖音" />
        </el-select>
      </el-form-item>
      
      <!-- 自定义插槽 -->
      <slot name="filters" :filters="filters"></slot>
      
      <!-- 操作按钮 -->
      <el-form-item>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <slot name="actions"></slot>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

interface Filters {
  start_date?: string
  end_date?: string
  store_name?: string
  platform?: string
  [key: string]: unknown
}

interface Props {
  showDateRange?: boolean
  showStore?: boolean
  showPlatform?: boolean
  stores?: string[]
  defaultFilters?: Partial<Filters>
}

const props = withDefaults(defineProps<Props>(), {
  showDateRange: true,
  showStore: true,
  showPlatform: false,
  stores: () => []
})

const emit = defineEmits<{
  search: [filters: Filters]
  reset: []
  change: [filters: Filters]
}>()

const filters = reactive<Filters>({
  start_date: undefined,
  end_date: undefined,
  store_name: undefined,
  platform: undefined,
  ...props.defaultFilters
})

const dateRange = ref<[string, string] | null>(null)

// 日期快捷选项
const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = dayjs()
      return [today.toDate(), today.toDate()]
    }
  },
  {
    text: '昨天',
    value: () => {
      const yesterday = dayjs().subtract(1, 'day')
      return [yesterday.toDate(), yesterday.toDate()]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = dayjs()
      const start = end.subtract(6, 'day')
      return [start.toDate(), end.toDate()]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = dayjs()
      const start = end.subtract(29, 'day')
      return [start.toDate(), end.toDate()]
    }
  },
  {
    text: '本月',
    value: () => {
      const start = dayjs().startOf('month')
      const end = dayjs().endOf('month')
      return [start.toDate(), end.toDate()]
    }
  },
  {
    text: '上月',
    value: () => {
      const start = dayjs().subtract(1, 'month').startOf('month')
      const end = dayjs().subtract(1, 'month').endOf('month')
      return [start.toDate(), end.toDate()]
    }
  }
]

const handleDateChange = (value: [string, string] | null) => {
  if (value) {
    filters.start_date = value[0]
    filters.end_date = value[1]
  } else {
    filters.start_date = undefined
    filters.end_date = undefined
  }
  handleFilterChange()
}

const handleFilterChange = () => {
  emit('change', { ...filters })
}

const handleSearch = () => {
  emit('search', { ...filters })
}

const handleReset = () => {
  dateRange.value = null
  Object.keys(filters).forEach(key => {
    filters[key] = undefined
  })
  emit('reset')
}

// 初始化默认日期范围（最近7天）
onMounted(() => {
  if (props.showDateRange && !filters.start_date) {
    const end = dayjs()
    const start = end.subtract(6, 'day')
    dateRange.value = [start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD')]
    filters.start_date = dateRange.value[0]
    filters.end_date = dateRange.value[1]
  }
})

// 暴露 filters
defineExpose({
  filters,
  setFilters: (newFilters: Partial<Filters>) => {
    Object.assign(filters, newFilters)
    if (newFilters.start_date && newFilters.end_date) {
      dateRange.value = [newFilters.start_date, newFilters.end_date]
    }
  }
})
</script>

<style lang="scss" scoped>
.filter-panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 16px 24px;
  margin-bottom: 16px;
  
  .el-form-item {
    margin-bottom: 0;
    margin-right: 16px;
  }
}
</style>


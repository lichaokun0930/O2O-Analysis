<template>
  <div class="data-table">
    <el-table
      ref="tableRef"
      :data="data"
      :height="height"
      :max-height="maxHeight"
      :stripe="stripe"
      :border="border"
      :row-class-name="rowClassName"
      :default-sort="defaultSort"
      :loading="loading"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      v-loading="loading"
    >
      <!-- 选择列 -->
      <el-table-column v-if="selectable" type="selection" width="50" />
      
      <!-- 序号列 -->
      <el-table-column v-if="showIndex" type="index" label="序号" width="60" align="center" />
      
      <!-- 动态列 -->
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :sortable="col.sortable"
        :align="col.align || 'left'"
        :fixed="col.fixed"
        :show-overflow-tooltip="col.showOverflow !== false"
      >
        <template #default="{ row, $index }">
          <!-- 自定义插槽 -->
          <slot v-if="$slots[col.prop]" :name="col.prop" :row="row" :index="$index" />
          
          <!-- 标签类型 -->
          <template v-else-if="col.type === 'tag'">
            <el-tag 
              :type="getTagType(row[col.prop], col.tagMap)"
              size="small"
            >
              {{ col.formatter ? col.formatter(row[col.prop], row) : row[col.prop] }}
            </el-tag>
          </template>
          
          <!-- 金额类型 -->
          <template v-else-if="col.type === 'money'">
            <span :class="getMoneyClass(row[col.prop])">
              {{ formatMoney(row[col.prop]) }}
            </span>
          </template>
          
          <!-- 百分比类型 -->
          <template v-else-if="col.type === 'percent'">
            <span :class="getPercentClass(row[col.prop], col.threshold)">
              {{ formatPercent(row[col.prop]) }}
            </span>
          </template>
          
          <!-- 日期类型 -->
          <template v-else-if="col.type === 'date'">
            {{ formatDate(row[col.prop], col.dateFormat) }}
          </template>
          
          <!-- 操作列 -->
          <template v-else-if="col.type === 'actions'">
            <div class="action-buttons">
              <el-button
                v-for="action in col.actions"
                :key="action.key"
                :type="action.type || 'primary'"
                :size="action.size || 'small'"
                link
                @click.stop="handleAction(action.key, row)"
              >
                {{ action.label }}
              </el-button>
            </div>
          </template>
          
          <!-- 默认显示 -->
          <template v-else>
            {{ col.formatter ? col.formatter(row[col.prop], row) : row[col.prop] }}
          </template>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div v-if="pagination" class="data-table__pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import type { TableInstance } from 'element-plus'

interface TableColumn {
  prop: string
  label: string
  width?: number | string
  minWidth?: number | string
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  fixed?: boolean | 'left' | 'right'
  showOverflow?: boolean
  type?: 'tag' | 'money' | 'percent' | 'date' | 'actions'
  tagMap?: Record<string, string>
  threshold?: number
  dateFormat?: string
  formatter?: (value: unknown, row: unknown) => string
  actions?: Array<{
    key: string
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
    size?: 'small' | 'default' | 'large'
  }>
}

interface Props {
  data: unknown[]
  columns: TableColumn[]
  height?: string | number
  maxHeight?: string | number
  stripe?: boolean
  border?: boolean
  loading?: boolean
  selectable?: boolean
  showIndex?: boolean
  pagination?: boolean
  total?: number
  defaultSort?: { prop: string; order: 'ascending' | 'descending' }
  pageSizes?: number[]
  rowClassName?: (data: { row: unknown; rowIndex: number }) => string
}

const props = withDefaults(defineProps<Props>(), {
  stripe: true,
  border: false,
  loading: false,
  selectable: false,
  showIndex: false,
  pagination: true,
  total: 0,
  pageSizes: () => [10, 20, 50, 100]
})

const emit = defineEmits<{
  selectionChange: [selection: unknown[]]
  sortChange: [data: { prop: string; order: 'ascending' | 'descending' | null }]
  rowClick: [row: unknown]
  action: [key: string, row: unknown]
  pageChange: [page: number]
  sizeChange: [size: number]
}>()

const tableRef = ref<TableInstance>()
const currentPage = ref(1)
const pageSize = ref(20)

// 格式化金额
const formatMoney = (value: number | null | undefined) => {
  if (value == null) return '-'
  const prefix = value < 0 ? '-¥' : '¥'
  return prefix + Math.abs(value).toFixed(2)
}

// 金额样式类
const getMoneyClass = (value: number) => {
  if (value < 0) return 'text-danger'
  if (value > 0) return 'text-success'
  return ''
}

// 格式化百分比
const formatPercent = (value: number | null | undefined) => {
  if (value == null) return '-'
  return (value * 100).toFixed(2) + '%'
}

// 百分比样式类
const getPercentClass = (value: number, threshold?: number) => {
  if (threshold !== undefined) {
    return value < threshold ? 'text-danger' : 'text-success'
  }
  return value < 0 ? 'text-danger' : 'text-success'
}

// 格式化日期
const formatDate = (value: string, format = 'YYYY-MM-DD') => {
  if (!value) return '-'
  return dayjs(value).format(format)
}

// 获取标签类型
const getTagType = (value: unknown, tagMap?: Record<string, string>) => {
  if (tagMap && typeof value === 'string') {
    return tagMap[value] || 'info'
  }
  return 'info'
}

// 事件处理
const handleSelectionChange = (selection: unknown[]) => {
  emit('selectionChange', selection)
}

const handleSortChange = (data: { prop: string; order: 'ascending' | 'descending' | null }) => {
  emit('sortChange', data)
}

const handleRowClick = (row: unknown) => {
  emit('rowClick', row)
}

const handleAction = (key: string, row: unknown) => {
  emit('action', key, row)
}

const handlePageChange = (page: number) => {
  emit('pageChange', page)
}

const handleSizeChange = (size: number) => {
  currentPage.value = 1
  emit('sizeChange', size)
}

// 暴露方法
defineExpose({
  clearSelection: () => tableRef.value?.clearSelection(),
  getSelectionRows: () => tableRef.value?.getSelectionRows(),
  toggleRowSelection: (row: unknown, selected: boolean) => 
    tableRef.value?.toggleRowSelection(row, selected)
})
</script>

<style lang="scss" scoped>
.data-table {
  &__pagination {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
  }
  
  .text-danger {
    color: #ff4d4f;
    font-weight: 500;
  }
  
  .text-success {
    color: #52c41a;
    font-weight: 500;
  }
}
</style>


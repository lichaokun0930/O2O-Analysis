<template>
  <div class="today-must-do">
    <div class="page-header">
      <h2>✅ 今日必做</h2>
      <div class="header-actions">
        <el-tag v-if="lastCheckTime" type="info" size="small">
          最后检查: {{ lastCheckTime }}
        </el-tag>
        <el-button type="primary" @click="refreshAll" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新诊断
        </el-button>
      </div>
    </div>
    
    <!-- 汇总统计卡片 -->
    <el-row :gutter="16" class="summary-row">
      <el-col :span="6">
        <KPICard
          title="🔴 紧急问题"
          :value="summary?.urgent_count || 0"
          suffix="项"
          variant="urgent"
          :clickable="true"
          @click="activeTab = 'urgent'"
          :loading="loading"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="💰 总损失金额"
          :value="summary?.total_loss || 0"
          prefix="¥"
          variant="urgent"
          :loading="loading"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="🟡 关注问题"
          :value="summary?.watch_count || 0"
          suffix="项"
          variant="watch"
          :clickable="true"
          @click="activeTab = 'watch'"
          :loading="loading"
        />
      </el-col>
      <el-col :span="6">
        <KPICard
          title="🟢 亮点表现"
          :value="summary?.highlight_count || 0"
          suffix="项"
          variant="highlight"
          :clickable="true"
          @click="activeTab = 'highlights'"
          :loading="loading"
        />
      </el-col>
    </el-row>
    
    <!-- 筛选面板 -->
    <FilterPanel
      ref="filterRef"
      :show-date-range="true"
      :show-store="true"
      :stores="storeList"
      @search="handleSearch"
      @reset="handleReset"
    />
    
    <!-- 两层架构标签页 -->
    <el-tabs v-model="activeTab" type="border-card" class="diagnosis-tabs">
      <!-- 🔴 紧急处理 -->
      <el-tab-pane name="urgent">
        <template #label>
          <span class="tab-label urgent">
            🔴 紧急处理
            <el-badge v-if="(summary?.urgent_count || 0) > 0" :value="summary?.urgent_count" />
          </span>
        </template>
        <UrgentIssues
          :overflow-orders="overflowOrders"
          :loading="loading"
          @view-detail="handleViewOverflowDetail"
        />
      </el-tab-pane>
      
      <!-- 🟡 关注观察 -->
      <el-tab-pane name="watch">
        <template #label>
          <span class="tab-label watch">
            🟡 关注观察
            <el-badge v-if="(summary?.watch_count || 0) > 0" :value="summary?.watch_count" type="warning" />
          </span>
        </template>
        <WatchIssues
          :issues="summary?.watch_issues || []"
          :loading="loading"
        />
      </el-tab-pane>
      
      <!-- 🟢 亮点表现 -->
      <el-tab-pane name="highlights">
        <template #label>
          <span class="tab-label highlight">
            🟢 亮点表现
            <el-badge v-if="(summary?.highlight_count || 0) > 0" :value="summary?.highlight_count" type="success" />
          </span>
        </template>
        <Highlights
          :highlights="summary?.highlights || []"
          :loading="loading"
        />
      </el-tab-pane>
      
      <!-- 客户流失分析 -->
      <el-tab-pane name="churn" label="👥 客户流失">
        <CustomerChurn
          :churn-data="customerChurn"
          :loading="loading"
          @refresh="fetchCustomerChurn"
        />
      </el-tab-pane>
      
      <!-- 客单价异常 -->
      <el-tab-pane name="aov" label="💰 客单价异常">
        <AOVAnomaly
          :loading="loading"
        />
      </el-tab-pane>
    </el-tabs>
    
    <!-- 穿底订单详情弹窗 -->
    <el-dialog
      v-model="overflowDetailVisible"
      title="穿底订单详情"
      width="800px"
    >
      <OverflowOrderDetail
        v-if="selectedOverflowOrder"
        :order="selectedOverflowOrder"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { useDiagnosisStore } from '@/stores/diagnosisStore'
import type { OverflowOrder } from '@/api/types'
import FilterPanel from '@/components/common/FilterPanel.vue'
import KPICard from '@/components/charts/KPICard.vue'
import UrgentIssues from './UrgentIssues.vue'
import WatchIssues from './WatchIssues.vue'
import Highlights from './Highlights.vue'
import CustomerChurn from './CustomerChurn.vue'
import AOVAnomaly from './AOVAnomaly.vue'
import OverflowOrderDetail from './OverflowOrderDetail.vue'
import dayjs from 'dayjs'

const diagnosisStore = useDiagnosisStore()

// State
const activeTab = ref('urgent')
const storeList = ref<string[]>(['门店A', '门店B', '门店C'])
const overflowDetailVisible = ref(false)
const selectedOverflowOrder = ref<OverflowOrder | null>(null)
const filterRef = ref()

// Computed
const loading = computed(() => diagnosisStore.loading)
const summary = computed(() => diagnosisStore.summary)
const overflowOrders = computed(() => diagnosisStore.overflowOrders)
const customerChurn = computed(() => diagnosisStore.customerChurn)

const lastCheckTime = computed(() => {
  if (!summary.value?.check_time) return ''
  return dayjs(summary.value.check_time).format('HH:mm:ss')
})

// Methods
const handleSearch = (filters: Record<string, unknown>) => {
  diagnosisStore.setFilters({
    store_name: filters.store_name as string,
    start_date: filters.start_date as string,
    end_date: filters.end_date as string
  })
  refreshAll()
}

const handleReset = () => {
  diagnosisStore.resetFilters()
  refreshAll()
}

const refreshAll = async () => {
  await diagnosisStore.refreshAll()
}

const fetchCustomerChurn = async (daysThreshold?: number) => {
  await diagnosisStore.fetchCustomerChurn(daysThreshold)
}

const handleViewOverflowDetail = (order: OverflowOrder) => {
  selectedOverflowOrder.value = order
  overflowDetailVisible.value = true
}

// Lifecycle
onMounted(() => {
  refreshAll()
})
</script>

<style lang="scss" scoped>
.today-must-do {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .summary-row {
    margin-bottom: 16px;
  }
  
  .diagnosis-tabs {
    margin-top: 16px;
    
    :deep(.el-tabs__header) {
      background: #fafafa;
    }
    
    :deep(.el-tabs__content) {
      padding: 20px;
    }
  }
  
  .tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
    
    &.urgent .el-badge {
      :deep(.el-badge__content) {
        background-color: #ff4d4f;
      }
    }
    
    &.watch .el-badge {
      :deep(.el-badge__content) {
        background-color: #faad14;
      }
    }
    
    &.highlight .el-badge {
      :deep(.el-badge__content) {
        background-color: #52c41a;
      }
    }
  }
}
</style>


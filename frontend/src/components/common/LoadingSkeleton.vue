<template>
  <div class="loading-skeleton" :class="`loading-skeleton--${variant}`">
    <!-- KPI卡片骨架 -->
    <template v-if="variant === 'kpi'">
      <el-skeleton animated>
        <template #template>
          <div class="skeleton-kpi">
            <el-skeleton-item variant="text" style="width: 40%; height: 16px" />
            <el-skeleton-item variant="h1" style="width: 60%; height: 32px; margin-top: 12px" />
            <el-skeleton-item variant="text" style="width: 30%; height: 14px; margin-top: 8px" />
          </div>
        </template>
      </el-skeleton>
    </template>
    
    <!-- 图表骨架 -->
    <template v-else-if="variant === 'chart'">
      <el-skeleton animated>
        <template #template>
          <div class="skeleton-chart">
            <el-skeleton-item variant="text" style="width: 30%; height: 20px" />
            <div class="skeleton-chart__body">
              <el-skeleton-item variant="rect" style="width: 100%; height: 100%" />
            </div>
          </div>
        </template>
      </el-skeleton>
    </template>
    
    <!-- 表格骨架 -->
    <template v-else-if="variant === 'table'">
      <el-skeleton animated :rows="rows" />
    </template>
    
    <!-- 默认骨架 -->
    <template v-else>
      <el-skeleton animated :rows="rows" />
    </template>
  </div>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'kpi' | 'chart' | 'table' | 'default'
  rows?: number
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
  rows: 5
})
</script>

<style lang="scss" scoped>
.loading-skeleton {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  
  &--kpi {
    .skeleton-kpi {
      display: flex;
      flex-direction: column;
    }
  }
  
  &--chart {
    .skeleton-chart {
      &__body {
        height: 280px;
        margin-top: 16px;
      }
    }
  }
}
</style>


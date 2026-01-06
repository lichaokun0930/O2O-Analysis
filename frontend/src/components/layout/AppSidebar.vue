<template>
  <aside class="app-sidebar" :class="{ 'is-collapsed': isCollapsed }">
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      router
      class="sidebar-menu"
      background-color="#001529"
      text-color="rgba(255, 255, 255, 0.65)"
      active-text-color="#1890ff"
    >
      <!-- 今日必做 -->
      <el-menu-item index="/today-must-do">
        <el-icon><Notification /></el-icon>
        <template #title>
          <span>✅ 今日必做</span>
          <el-badge v-if="urgentCount > 0" :value="urgentCount" class="menu-badge" />
        </template>
      </el-menu-item>
      
      <!-- 订单数据概览 -->
      <el-menu-item index="/order-overview">
        <el-icon><DataLine /></el-icon>
        <template #title>📊 订单数据概览</template>
      </el-menu-item>
      
      <!-- 商品分析 -->
      <el-menu-item index="/product-analysis">
        <el-icon><Goods /></el-icon>
        <template #title>📦 商品分析</template>
      </el-menu-item>
      
      <!-- 时段场景分析 -->
      <el-menu-item index="/scene-analysis">
        <el-icon><Timer /></el-icon>
        <template #title>⏰ 时段场景分析</template>
      </el-menu-item>
      
      <!-- 分隔线 -->
      <div class="menu-divider"></div>
      
      <!-- 数据管理 -->
      <el-menu-item index="/data-management">
        <el-icon><FolderOpened /></el-icon>
        <template #title>🗄️ 数据管理</template>
      </el-menu-item>
      
      <!-- 系统监控 -->
      <el-menu-item index="/system-monitor">
        <el-icon><Monitor /></el-icon>
        <template #title>🖥️ 系统监控</template>
      </el-menu-item>
    </el-menu>
    
    <!-- 折叠按钮 -->
    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon :size="16">
        <Fold v-if="!isCollapsed" />
        <Expand v-else />
      </el-icon>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDiagnosisStore } from '@/stores/diagnosisStore'
import { 
  Notification, DataLine, Goods, Timer, 
  FolderOpened, Monitor, Fold, Expand 
} from '@element-plus/icons-vue'

const route = useRoute()
const diagnosisStore = useDiagnosisStore()
const isCollapsed = ref(false)

const activeMenu = computed(() => route.path)
const urgentCount = computed(() => diagnosisStore.summary?.urgentCount || 0)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style lang="scss" scoped>
.app-sidebar {
  width: 220px;
  height: calc(100vh - 60px);
  background-color: #001529;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  
  &.is-collapsed {
    width: 64px;
  }
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  
  .el-menu-item {
    height: 50px;
    line-height: 50px;
    
    &:hover {
      background-color: #000c17 !important;
    }
    
    &.is-active {
      background-color: #1890ff !important;
      color: #fff !important;
      
      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 3px;
        background-color: #fff;
      }
    }
  }
}

.menu-badge {
  margin-left: 8px;
  
  :deep(.el-badge__content) {
    background-color: #ff4d4f;
    border: none;
  }
}

.menu-divider {
  height: 1px;
  background-color: rgba(255, 255, 255, 0.1);
  margin: 16px 20px;
}

.collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.65);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
  
  &:hover {
    color: #fff;
    background-color: rgba(255, 255, 255, 0.05);
  }
}
</style>


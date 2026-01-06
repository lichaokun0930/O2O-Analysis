<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <!-- 全局加载指示器 -->
      <div v-if="globalStore.initializing" class="global-loading">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在加载数据...</span>
      </div>
      
      <AppHeader />
      <div class="main-content">
        <AppSidebar />
        <div class="page-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { Loading } from '@element-plus/icons-vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import { useGlobalDataStore } from '@/stores/globalDataStore'

// 全局数据Store
const globalStore = useGlobalDataStore()

// 应用启动时初始化全局数据
onMounted(async () => {
  console.log('🚀 应用启动，初始化全局数据...')
  try {
    await globalStore.initialize()
    console.log('✅ 全局数据初始化完成')
  } catch (error) {
    console.error('❌ 全局数据初始化失败:', error)
  }
})
</script>

<style lang="scss">
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  font-size: 16px;
  color: #409EFF;
  
  .loading-icon {
    font-size: 48px;
    margin-bottom: 16px;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.main-content {
  display: flex;
  flex: 1;
  margin-top: 60px; // header height
}

.page-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: #f5f7fa;
}

// 页面切换动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>


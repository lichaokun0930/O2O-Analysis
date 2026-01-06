<template>
  <header class="app-header">
    <div class="app-header__left">
      <div class="app-header__logo">
        <el-icon :size="24" color="#1890ff"><DataAnalysis /></el-icon>
        <span class="app-header__title">订单数据看板</span>
      </div>
    </div>
    
    <div class="app-header__center">
      <el-tag type="success" size="small" v-if="connectionStatus === 'connected'">
        <el-icon><Check /></el-icon> 服务已连接
      </el-tag>
      <el-tag type="danger" size="small" v-else>
        <el-icon><Close /></el-icon> 服务断开
      </el-tag>
    </div>
    
    <div class="app-header__right">
      <span class="app-header__time">{{ currentTime }}</span>
      <el-dropdown>
        <el-button text>
          <el-icon :size="18"><User /></el-icon>
          <span style="margin-left: 4px;">管理员</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>系统设置</el-dropdown-item>
            <el-dropdown-item divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { DataAnalysis, User, Check, Close } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const currentTime = ref('')
const connectionStatus = ref<'connected' | 'disconnected'>('connected')
let timer: number

const updateTime = () => {
  currentTime.value = dayjs().format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style lang="scss" scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: linear-gradient(135deg, #001529 0%, #002140 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  
  &__left {
    display: flex;
    align-items: center;
  }
  
  &__logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  &__title {
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    letter-spacing: 1px;
  }
  
  &__center {
    flex: 1;
    display: flex;
    justify-content: center;
  }
  
  &__right {
    display: flex;
    align-items: center;
    gap: 20px;
  }
  
  &__time {
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    font-family: 'Consolas', monospace;
  }
  
  .el-button {
    color: rgba(255, 255, 255, 0.85);
    
    &:hover {
      color: #fff;
    }
  }
}
</style>


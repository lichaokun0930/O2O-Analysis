<template>
  <div class="system-monitor">
    <div class="page-header">
      <h2>🖥️ 系统监控</h2>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>
    
    <!-- 系统状态卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="monitor-card">
          <div class="monitor-card__header">
            <el-icon :size="24" color="#1890ff"><Monitor /></el-icon>
            <span>CPU 使用率</span>
          </div>
          <div class="monitor-card__body">
            <el-progress 
              type="dashboard" 
              :percentage="systemStats.cpu_usage" 
              :color="getProgressColor(systemStats.cpu_usage)"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="monitor-card">
          <div class="monitor-card__header">
            <el-icon :size="24" color="#52c41a"><Cpu /></el-icon>
            <span>内存使用率</span>
          </div>
          <div class="monitor-card__body">
            <el-progress 
              type="dashboard" 
              :percentage="systemStats.memory_usage" 
              :color="getProgressColor(systemStats.memory_usage)"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="monitor-card">
          <div class="monitor-card__header">
            <el-icon :size="24" color="#faad14"><Coin /></el-icon>
            <span>磁盘使用率</span>
          </div>
          <div class="monitor-card__body">
            <el-progress 
              type="dashboard" 
              :percentage="systemStats.disk_usage" 
              :color="getProgressColor(systemStats.disk_usage)"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="monitor-card">
          <div class="monitor-card__header">
            <el-icon :size="24" color="#722ed1"><Connection /></el-icon>
            <span>活跃连接</span>
          </div>
          <div class="monitor-card__body">
            <div class="big-number">{{ systemStats.active_connections }}</div>
            <div class="sub-text">当前连接数</div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 缓存统计 -->
    <div class="dashboard-card">
      <div class="dashboard-card__header">
        <h3>🗃️ 四级缓存命中率</h3>
      </div>
      <div class="dashboard-card__body">
        <el-row :gutter="24">
          <el-col :span="6">
            <div class="cache-stat">
              <div class="cache-level-badge l1">L1</div>
              <div class="cache-stat__value">{{ (cacheStats.l1_hit_rate * 100).toFixed(1) }}%</div>
              <div class="cache-stat__label">请求级缓存</div>
              <el-progress 
                :percentage="cacheStats.l1_hit_rate * 100" 
                :stroke-width="8"
                color="#52c41a"
              />
            </div>
          </el-col>
          <el-col :span="6">
            <div class="cache-stat">
              <div class="cache-level-badge l2">L2</div>
              <div class="cache-stat__value">{{ (cacheStats.l2_hit_rate * 100).toFixed(1) }}%</div>
              <div class="cache-stat__label">会话级缓存</div>
              <el-progress 
                :percentage="cacheStats.l2_hit_rate * 100" 
                :stroke-width="8"
                color="#1890ff"
              />
            </div>
          </el-col>
          <el-col :span="6">
            <div class="cache-stat">
              <div class="cache-level-badge l3">L3</div>
              <div class="cache-stat__value">{{ (cacheStats.l3_hit_rate * 100).toFixed(1) }}%</div>
              <div class="cache-stat__label">Redis缓存</div>
              <el-progress 
                :percentage="cacheStats.l3_hit_rate * 100" 
                :stroke-width="8"
                color="#faad14"
              />
            </div>
          </el-col>
          <el-col :span="6">
            <div class="cache-stat">
              <div class="cache-level-badge l4">L4</div>
              <div class="cache-stat__value">{{ (cacheStats.l4_hit_rate * 100).toFixed(1) }}%</div>
              <div class="cache-stat__label">持久化缓存</div>
              <el-progress 
                :percentage="cacheStats.l4_hit_rate * 100" 
                :stroke-width="8"
                color="#722ed1"
              />
            </div>
          </el-col>
        </el-row>
        
        <div class="cache-summary">
          <div class="cache-summary__item">
            <span class="label">总缓存键数</span>
            <span class="value">{{ cacheStats.total_keys.toLocaleString() }}</span>
          </div>
          <div class="cache-summary__item">
            <span class="label">内存占用</span>
            <span class="value">{{ cacheStats.memory_used }}</span>
          </div>
          <div class="cache-summary__item">
            <span class="label">综合命中率</span>
            <span class="value highlight">{{ avgHitRate }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 性能指标 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>⚡ 响应时间</h3>
          </div>
          <div class="dashboard-card__body">
            <div class="performance-metric">
              <div class="metric-value">{{ systemStats.avg_response_time }} ms</div>
              <div class="metric-label">平均响应时间</div>
            </div>
            <G2PlotChart
              type="line"
              :data="responseTimeData"
              :config="responseTimeConfig"
              height="200px"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="dashboard-card">
          <div class="dashboard-card__header">
            <h3>📊 系统信息</h3>
          </div>
          <div class="dashboard-card__body">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="运行时长">{{ systemStats.uptime }}</el-descriptions-item>
              <el-descriptions-item label="Python 版本">3.10.12</el-descriptions-item>
              <el-descriptions-item label="FastAPI 版本">0.104.1</el-descriptions-item>
              <el-descriptions-item label="数据库连接池">10 / 20</el-descriptions-item>
              <el-descriptions-item label="Redis 状态">
                <el-tag type="success" size="small">已连接</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="PostgreSQL 状态">
                <el-tag type="success" size="small">已连接</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh, Monitor, Cpu, Coin, Connection } from '@element-plus/icons-vue'
import G2PlotChart from '@/components/charts/G2PlotChart.vue'

// State
const systemStats = ref({
  cpu_usage: 45,
  memory_usage: 62,
  disk_usage: 38,
  active_connections: 12,
  avg_response_time: 85,
  uptime: '5天 12小时 36分钟'
})

const cacheStats = ref({
  l1_hit_rate: 0.95,
  l2_hit_rate: 0.87,
  l3_hit_rate: 0.72,
  l4_hit_rate: 0.65,
  total_keys: 15680,
  memory_used: '256 MB'
})

const responseTimeData = ref([
  { time: '10:00', value: 78 },
  { time: '10:05', value: 82 },
  { time: '10:10', value: 95 },
  { time: '10:15', value: 88 },
  { time: '10:20', value: 72 },
  { time: '10:25', value: 85 },
  { time: '10:30', value: 79 }
])

const responseTimeConfig = {
  xField: 'time',
  yField: 'value',
  smooth: true,
  point: {
    size: 3,
    shape: 'circle'
  },
  yAxis: {
    label: {
      formatter: (v: string) => v + ' ms'
    }
  }
}

let refreshTimer: number

// Computed
const avgHitRate = computed(() => {
  const avg = (cacheStats.value.l1_hit_rate + cacheStats.value.l2_hit_rate + 
               cacheStats.value.l3_hit_rate + cacheStats.value.l4_hit_rate) / 4
  return (avg * 100).toFixed(1)
})

// Methods
const getProgressColor = (percentage: number) => {
  if (percentage < 60) return '#52c41a'
  if (percentage < 80) return '#faad14'
  return '#ff4d4f'
}

const refreshData = () => {
  // 模拟数据刷新
  systemStats.value.cpu_usage = Math.floor(Math.random() * 30 + 35)
  systemStats.value.memory_usage = Math.floor(Math.random() * 20 + 55)
  systemStats.value.active_connections = Math.floor(Math.random() * 10 + 8)
  systemStats.value.avg_response_time = Math.floor(Math.random() * 40 + 60)
}

// Lifecycle
onMounted(() => {
  // 每 30 秒自动刷新
  refreshTimer = window.setInterval(refreshData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style lang="scss" scoped>
.system-monitor {
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
  }
  
  .stats-row {
    margin-bottom: 16px;
  }
  
  .monitor-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    padding: 20px;
    text-align: center;
    
    &__header {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      margin-bottom: 16px;
      
      span {
        font-size: 14px;
        color: #606266;
      }
    }
    
    &__body {
      .big-number {
        font-size: 36px;
        font-weight: 700;
        color: #722ed1;
      }
      
      .sub-text {
        font-size: 12px;
        color: #909399;
        margin-top: 8px;
      }
    }
  }
  
  .cache-stat {
    text-align: center;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
    
    &__value {
      font-size: 28px;
      font-weight: 700;
      color: #303133;
      margin: 12px 0 4px;
    }
    
    &__label {
      font-size: 13px;
      color: #909399;
      margin-bottom: 12px;
    }
  }
  
  .cache-level-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 12px;
    
    &.l1 { background: #f6ffed; color: #52c41a; }
    &.l2 { background: #e6f7ff; color: #1890ff; }
    &.l3 { background: #fffbe6; color: #faad14; }
    &.l4 { background: #f9f0ff; color: #722ed1; }
  }
  
  .cache-summary {
    display: flex;
    justify-content: center;
    gap: 48px;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e4e7ed;
    
    &__item {
      text-align: center;
      
      .label {
        display: block;
        font-size: 13px;
        color: #909399;
        margin-bottom: 8px;
      }
      
      .value {
        font-size: 20px;
        font-weight: 600;
        color: #303133;
        
        &.highlight {
          color: #1890ff;
        }
      }
    }
  }
  
  .performance-metric {
    text-align: center;
    margin-bottom: 16px;
    
    .metric-value {
      font-size: 32px;
      font-weight: 700;
      color: #1890ff;
    }
    
    .metric-label {
      font-size: 13px;
      color: #909399;
    }
  }
}
</style>


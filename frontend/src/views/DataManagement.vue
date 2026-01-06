<template>
  <div class="data-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>📂 数据源选择</h2>
      <div class="current-data-label">
        当前数据: <span class="data-source">{{ currentDataSource }}</span>
      </div>
    </div>
    
    <!-- 主Tab容器 -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- Tab 1: 数据库数据 -->
        <el-tab-pane label="🗄️ 数据库数据" name="database">
          <div class="tab-content">
            <el-alert
              type="info"
              :closable="false"
              class="mb-4"
            >
              <template #title>
                <el-icon><Connection /></el-icon>
                从PostgreSQL数据库加载订单数据
              </template>
            </el-alert>
            
            <!-- 筛选条件 -->
            <el-row :gutter="16" class="filter-row">
              <el-col :span="8">
                <div class="filter-item">
                  <label>🏪 选择门店:</label>
                  <el-select
                    v-model="selectedStore"
                    placeholder="全部门店"
                    clearable
                    filterable
                    :loading="storesLoading"
                    class="w-full"
                  >
                    <el-option
                      v-for="store in stores"
                      :key="store.value"
                      :label="store.label"
                      :value="store.value"
                    />
                  </el-select>
                </div>
              </el-col>
              <el-col :span="10">
                <div class="filter-item">
                  <label>📅 统计日期:</label>
                  <el-date-picker
                    v-model="dateRange"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    value-format="YYYY-MM-DD"
                    :shortcuts="dateShortcuts"
                    class="w-full"
                  />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="filter-item">
                  <label>&nbsp;</label>
                  <el-button
                    type="primary"
                    :loading="loadingData"
                    @click="loadFromDatabase"
                    class="w-full"
                  >
                    <el-icon><Download /></el-icon>
                    加载数据
                  </el-button>
                </div>
              </el-col>
            </el-row>
            
            <!-- 缓存状态 -->
            <el-alert
              v-if="cacheStatus"
              :type="cacheStatus.type"
              :title="cacheStatus.message"
              :closable="false"
              class="mt-4"
            />
            
            <!-- 快捷日期选择 -->
            <div class="quick-dates mt-4">
              <span class="quick-dates-label">📆 快捷选择:</span>
              <el-button-group size="small">
                <el-button @click="setQuickDate('yesterday')">昨日</el-button>
                <el-button @click="setQuickDate('today')">今日</el-button>
                <el-button @click="setQuickDate('lastWeek')">上周</el-button>
                <el-button @click="setQuickDate('thisWeek')">本周</el-button>
                <el-button @click="setQuickDate('lastMonth')">上月</el-button>
                <el-button @click="setQuickDate('thisMonth')">本月</el-button>
                <el-button @click="setQuickDate('last7Days')">过去7天</el-button>
                <el-button @click="setQuickDate('last30Days')">过去30天</el-button>
              </el-button-group>
            </div>
            
            <!-- 数据库统计 -->
            <div v-if="dbStats" class="db-stats mt-4">
              <el-row :gutter="16">
                <el-col :span="6">
                  <div class="stat-card">
                    <div class="stat-icon">📊</div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatNumber(dbStats.total_orders) }}</div>
                      <div class="stat-label">订单总数</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-card">
                    <div class="stat-icon">🏪</div>
                    <div class="stat-content">
                      <div class="stat-value">{{ dbStats.total_stores }}</div>
                      <div class="stat-label">门店数量</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-card">
                    <div class="stat-icon">📦</div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatNumber(dbStats.total_products) }}</div>
                      <div class="stat-label">商品种类</div>
                    </div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-card">
                    <div class="stat-icon">🕐</div>
                    <div class="stat-content">
                      <div class="stat-value">{{ dbStats.data_freshness }}</div>
                      <div class="stat-label">数据新鲜度</div>
                    </div>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <!-- 加载状态 -->
            <div v-if="loadResult" class="load-result mt-4">
              <el-alert
                :type="loadResult.success ? 'success' : 'error'"
                :title="loadResult.message"
                :closable="false"
              />
            </div>
          </div>
        </el-tab-pane>
        
        <!-- Tab 2: 上传新数据 -->
        <el-tab-pane label="📤 上传新数据" name="upload">
          <div class="tab-content">
            <el-alert
              type="info"
              :closable="false"
              class="mb-4"
            >
              <template #title>
                <el-icon><Upload /></el-icon>
                <strong>💾 数据将自动保存到数据库</strong>
              </template>
              <template #default>
                上传的数据会自动导入PostgreSQL数据库，支持多人共享访问，下次可直接从数据库加载。
                <br>
                <span class="text-warning">⚠️ 如果门店已存在数据，将自动覆盖。</span>
              </template>
            </el-alert>
            
            <!-- 上传区域 -->
            <el-upload
              ref="uploadRef"
              class="upload-area"
              drag
              :auto-upload="false"
              :limit="5"
              multiple
              accept=".xlsx,.xls"
              :on-change="handleFileChange"
              :on-exceed="handleExceed"
              :file-list="fileList"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">
                <strong>拖拽文件到这里 或 点击选择文件</strong>
              </div>
              <div class="upload-hint">
                支持 .xlsx / .xls 格式，可同时上传多个文件
              </div>
              <div class="upload-database-hint">
                💾 数据将自动保存到数据库，支持多人共享访问
              </div>
            </el-upload>
            
            <!-- 上传按钮 -->
            <div class="upload-actions mt-4" v-if="fileList.length > 0">
              <el-button
                type="primary"
                size="large"
                :loading="uploading"
                @click="uploadFiles"
              >
                <el-icon><Upload /></el-icon>
                上传并导入数据库 ({{ fileList.length }}个文件)
              </el-button>
              <el-button @click="clearFiles">清空文件</el-button>
            </div>
            
            <!-- 上传状态 -->
            <div v-if="uploadStatus" class="upload-status mt-4">
              <el-alert
                :type="uploadStatus.type"
                :closable="false"
              >
                <template #title>{{ uploadStatus.title }}</template>
                <template #default v-if="uploadStatus.details">
                  <div v-for="(detail, idx) in uploadStatus.details" :key="idx">
                    {{ detail }}
                  </div>
                </template>
              </el-alert>
            </div>
            
            <!-- 数据格式要求 -->
            <el-collapse class="format-guide mt-4">
              <el-collapse-item title="📋 订单数据格式要求">
                <div class="format-content">
                  <h4>📋 必需字段：</h4>
                  <ul>
                    <li><strong>订单ID</strong>: 订单唯一标识</li>
                    <li><strong>商品名称</strong>: 商品名称</li>
                    <li><strong>商品实售价</strong>: 商品售价</li>
                    <li><strong>销量</strong>: 商品数量</li>
                    <li><strong>下单时间</strong>: 订单时间</li>
                    <li><strong>门店名称</strong>: 门店标识</li>
                    <li><strong>渠道</strong>: 销售渠道（如美团、饿了么）</li>
                  </ul>
                  <h4 class="mt-3">✨ 推荐字段（用于完整分析）：</h4>
                  <ul>
                    <li>物流配送费、平台佣金、配送距离</li>
                    <li>美团一级分类、美团三级分类</li>
                    <li>收货地址、配送费减免、满减、商品减免、代金券</li>
                    <li>用户支付配送费、订单零售额、打包费</li>
                  </ul>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-tab-pane>
        
        <!-- Tab 3: 数据管理 -->
        <el-tab-pane label="🗂️ 数据管理" name="management">
          <div class="tab-content">
            <el-alert
              type="info"
              :closable="false"
              class="mb-4"
            >
              <template #title>
                <el-icon><Setting /></el-icon>
                <strong>📊 数据库空间管理</strong>
              </template>
              定期清理历史数据，释放数据库空间，优化看板性能
            </el-alert>
            
            <!-- 数据库管理统计 -->
            <div class="management-stats mb-4" v-if="dbStats">
              <el-descriptions :column="4" border>
                <el-descriptions-item label="数据库状态">
                  <el-tag :type="dbStats.database_status === '已连接' ? 'success' : 'danger'">
                    {{ dbStats.database_status }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="Redis缓存">
                  <el-tag :type="dbStats.redis_status === '已连接' ? 'success' : 'warning'">
                    {{ dbStats.redis_status }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="订单总量">
                  {{ formatNumber(dbStats.total_orders) }} 条
                </el-descriptions-item>
                <el-descriptions-item label="门店数量">
                  {{ dbStats.total_stores }} 家
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <el-row :gutter="16">
              <!-- 按门店清理 -->
              <el-col :span="12">
                <el-card class="management-card">
                  <template #header>
                    <div class="card-header">
                      <el-icon><Shop /></el-icon>
                      <strong>按门店清理</strong>
                    </div>
                  </template>
                  
                  <div class="store-cleanup">
                    <el-form label-width="100px">
                      <el-form-item label="选择门店">
                        <el-select
                          v-model="cleanupStore"
                          placeholder="选择门店"
                          filterable
                          :loading="storesLoading"
                          class="w-full"
                        >
                          <el-option
                            v-for="store in stores"
                            :key="store.value"
                            :label="store.label"
                            :value="store.value"
                          />
                        </el-select>
                      </el-form-item>
                    </el-form>
                    
                    <!-- 门店统计预览 -->
                    <div v-if="storePreview" class="store-preview mb-3">
                      <el-descriptions :column="1" border size="small">
                        <el-descriptions-item label="门店名称">{{ storePreview.store_name }}</el-descriptions-item>
                        <el-descriptions-item label="订单数量">{{ formatNumber(storePreview.order_count) }} 条</el-descriptions-item>
                        <el-descriptions-item label="数据范围">
                          {{ storePreview.date_range.start || '无' }} ~ {{ storePreview.date_range.end || '无' }}
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                    
                    <div class="cleanup-actions">
                      <el-button
                        type="info"
                        :disabled="!cleanupStore"
                        :loading="previewLoading"
                        @click="previewStoreData"
                      >
                        <el-icon><View /></el-icon>
                        查看门店数据
                      </el-button>
                      <el-button
                        type="danger"
                        :disabled="!cleanupStore"
                        :loading="deletingStore"
                        @click="confirmDeleteStore"
                      >
                        <el-icon><Delete /></el-icon>
                        删除门店数据
                      </el-button>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <!-- 缓存管理 -->
              <el-col :span="12">
                <el-card class="management-card">
                  <template #header>
                    <div class="card-header">
                      <el-icon><Cpu /></el-icon>
                      <strong>缓存管理</strong>
                    </div>
                  </template>
                  
                  <div class="cache-management">
                    <p class="cache-desc">四级缓存架构可显著提升查询性能。如数据不一致，可清除缓存重建。</p>
                    
                    <div class="cache-levels">
                      <div class="cache-level">
                        <span class="level-name">L1 - 请求级缓存</span>
                        <span class="level-ttl">TTL: 60秒</span>
                        <el-button size="small" @click="clearCache(1)">清除</el-button>
                      </div>
                      <div class="cache-level">
                        <span class="level-name">L2 - 会话级缓存</span>
                        <span class="level-ttl">TTL: 5分钟</span>
                        <el-button size="small" @click="clearCache(2)">清除</el-button>
                      </div>
                      <div class="cache-level">
                        <span class="level-name">L3 - Redis缓存</span>
                        <span class="level-ttl">TTL: 30分钟</span>
                        <el-button size="small" @click="clearCache(3)">清除</el-button>
                      </div>
                      <div class="cache-level">
                        <span class="level-name">L4 - 持久化缓存</span>
                        <span class="level-ttl">TTL: 24小时</span>
                        <el-button size="small" @click="clearCache(4)">清除</el-button>
                      </div>
                    </div>
                    
                    <div class="cache-actions mt-3">
                      <el-button type="warning" @click="clearAllCache">
                        <el-icon><Delete /></el-icon>
                        清除全部缓存
                      </el-button>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
            
            <!-- 数据库优化 -->
            <el-card class="management-card mt-4">
              <div class="db-optimize">
                <el-row align="middle">
                  <el-col :span="16">
                    <h4>
                      <el-icon><Operation /></el-icon>
                      数据库优化
                    </h4>
                    <p class="optimize-desc">清理空间碎片，重建索引，提升性能</p>
                  </el-col>
                  <el-col :span="8" class="text-right">
                    <el-button
                      type="success"
                      :loading="optimizing"
                      @click="optimizeDatabase"
                    >
                      <el-icon><Setting /></el-icon>
                      优化数据库
                    </el-button>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile, type UploadInstance } from 'element-plus'
import {
  Connection, Download, Upload, UploadFilled, Setting, Shop,
  View, Delete, Cpu, Operation
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import { dataApi, type Store, type StoreStats } from '@/api/data'
import type { DataStats } from '@/api/types'

// State
const activeTab = ref('database')
const selectedStore = ref<string>('')
const dateRange = ref<[string, string] | null>(null)
const stores = ref<Store[]>([])
const storesLoading = ref(false)
const loadingData = ref(false)
const dbStats = ref<DataStats | null>(null)
const loadResult = ref<{ success: boolean; message: string } | null>(null)
const cacheStatus = ref<{ type: 'success' | 'info' | 'warning'; message: string } | null>(null)
const currentDataSource = ref('数据库数据')

// 上传相关
const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)
const uploadStatus = ref<{ type: string; title: string; details?: string[] } | null>(null)

// 数据管理相关
const cleanupStore = ref<string>('')
const storePreview = ref<StoreStats | null>(null)
const previewLoading = ref(false)
const deletingStore = ref(false)
const optimizing = ref(false)

// 快捷日期选项
const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = new Date()
      return [today, today]
    }
  },
  {
    text: '昨天',
    value: () => {
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)
      return [yesterday, yesterday]
    }
  },
  {
    text: '过去7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 7)
      return [start, end]
    }
  },
  {
    text: '过去30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 30)
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const now = new Date()
      const start = new Date(now.getFullYear(), now.getMonth(), 1)
      return [start, now]
    }
  }
]

// Computed
const formatNumber = (num: number | undefined) => {
  if (num === undefined || num === null) return '0'
  return num.toLocaleString()
}

// Methods
const setQuickDate = (type: string) => {
  const today = dayjs()
  let start: dayjs.Dayjs
  let end: dayjs.Dayjs = today
  
  switch (type) {
    case 'yesterday':
      start = today.subtract(1, 'day')
      end = start
      break
    case 'today':
      start = today
      break
    case 'lastWeek':
      start = today.subtract(1, 'week').startOf('week')
      end = today.subtract(1, 'week').endOf('week')
      break
    case 'thisWeek':
      start = today.startOf('week')
      break
    case 'lastMonth':
      start = today.subtract(1, 'month').startOf('month')
      end = today.subtract(1, 'month').endOf('month')
      break
    case 'thisMonth':
      start = today.startOf('month')
      break
    case 'last7Days':
      start = today.subtract(7, 'day')
      break
    case 'last30Days':
      start = today.subtract(30, 'day')
      break
    default:
      start = today
  }
  
  dateRange.value = [start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD')]
}

const fetchStores = async () => {
  storesLoading.value = true
  try {
    const res = await dataApi.getStores()
    if (res.success) {
      stores.value = res.data
    }
  } catch (error) {
    console.error('获取门店列表失败:', error)
  } finally {
    storesLoading.value = false
  }
}

const fetchStats = async () => {
  try {
    dbStats.value = await dataApi.getStats()
  } catch (error) {
    console.error('获取统计失败:', error)
    ElMessage.error('获取数据统计失败')
  }
}

const loadFromDatabase = async () => {
  loadingData.value = true
  loadResult.value = null
  
  try {
    const res = await dataApi.loadFromDatabase({
      store_name: selectedStore.value || undefined,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    })
    
    loadResult.value = {
      success: res.success,
      message: res.message
    }
    
    if (res.success) {
      currentDataSource.value = selectedStore.value || '全部门店'
      cacheStatus.value = {
        type: 'success',
        message: '数据已加载到缓存'
      }
      ElMessage.success(res.message)
    }
  } catch (error: any) {
    loadResult.value = {
      success: false,
      message: error.message || '加载失败'
    }
    ElMessage.error('加载数据失败')
  } finally {
    loadingData.value = false
  }
}

// 上传相关方法
const handleFileChange = (file: UploadFile, files: UploadFile[]) => {
  fileList.value = files
}

const handleExceed = () => {
  ElMessage.warning('最多同时上传5个文件')
}

const clearFiles = () => {
  fileList.value = []
  uploadRef.value?.clearFiles()
}

const uploadFiles = async () => {
  if (fileList.value.length === 0) return
  
  uploading.value = true
  uploadStatus.value = null
  
  const results: string[] = []
  let successCount = 0
  let failCount = 0
  
  for (const file of fileList.value) {
    if (!file.raw) continue
    
    try {
      const res = await dataApi.uploadOrders(file.raw, { mode: 'replace' })
      if (res.success) {
        successCount++
        results.push(`✅ ${file.name}: 成功导入 ${res.rows_inserted} 条数据`)
      } else {
        failCount++
        results.push(`❌ ${file.name}: 上传失败`)
      }
    } catch (error: any) {
      failCount++
      results.push(`❌ ${file.name}: ${error.message || '上传失败'}`)
    }
  }
  
  uploading.value = false
  
  uploadStatus.value = {
    type: failCount === 0 ? 'success' : (successCount === 0 ? 'error' : 'warning'),
    title: `上传完成: ${successCount}成功, ${failCount}失败`,
    details: results
  }
  
  if (successCount > 0) {
    clearFiles()
    fetchStats()
    fetchStores()
  }
}

// 数据管理相关方法
const previewStoreData = async () => {
  if (!cleanupStore.value) return
  
  previewLoading.value = true
  try {
    storePreview.value = await dataApi.getStoreStats(cleanupStore.value)
  } catch (error) {
    ElMessage.error('获取门店数据失败')
  } finally {
    previewLoading.value = false
  }
}

const confirmDeleteStore = async () => {
  if (!cleanupStore.value) return
  
  await ElMessageBox.confirm(
    `确定要删除门店 "${cleanupStore.value}" 的所有数据吗？此操作不可恢复！`,
    '确认删除',
    { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
  )
  
  deletingStore.value = true
  try {
    const res = await dataApi.deleteStoreData(cleanupStore.value)
    if (res.success) {
      ElMessage.success(res.message)
      cleanupStore.value = ''
      storePreview.value = null
      fetchStats()
      fetchStores()
    }
  } catch (error) {
    ElMessage.error('删除失败')
  } finally {
    deletingStore.value = false
  }
}

const clearCache = async (level: 1 | 2 | 3 | 4) => {
  try {
    const res = await dataApi.clearCache(level)
    ElMessage.success(res.message || `L${level} 缓存已清除`)
  } catch (error) {
    ElMessage.error('清除缓存失败')
  }
}

const clearAllCache = async () => {
  await ElMessageBox.confirm('确定要清除所有缓存吗？', '确认', { type: 'warning' })
  
  try {
    const res = await dataApi.clearCache()
    ElMessage.success(res.message || '所有缓存已清除')
  } catch (error) {
    ElMessage.error('清除缓存失败')
  }
}

const optimizeDatabase = async () => {
  optimizing.value = true
  try {
    const res = await dataApi.optimizeDatabase()
    ElMessage.success(res.message || '数据库优化完成')
  } catch (error) {
    ElMessage.error('优化失败')
  } finally {
    optimizing.value = false
  }
}

// Watch
watch(cleanupStore, () => {
  storePreview.value = null
})

// Lifecycle
onMounted(() => {
  fetchStats()
  fetchStores()
})
</script>

<style lang="scss" scoped>
.data-management {
  padding: 20px;
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      font-size: 24px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
    
    .current-data-label {
      color: #909399;
      
      .data-source {
        color: #409eff;
        font-weight: 500;
      }
    }
  }
  
  .main-card {
    :deep(.el-card__body) {
      padding: 0;
    }
  }
  
  .tab-content {
    padding: 20px;
  }
  
  .filter-row {
    .filter-item {
      label {
        display: block;
        margin-bottom: 8px;
        color: #606266;
        font-weight: 500;
      }
    }
  }
  
  .w-full {
    width: 100%;
  }
  
  .quick-dates {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .quick-dates-label {
      color: #606266;
      font-weight: 500;
    }
  }
  
  .db-stats {
    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
      border-radius: 8px;
      
      .stat-icon {
        font-size: 32px;
        margin-right: 16px;
      }
      
      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: #303133;
        }
        
        .stat-label {
          font-size: 14px;
          color: #909399;
        }
      }
    }
  }
  
  // 上传区域
  .upload-area {
    :deep(.el-upload-dragger) {
      padding: 60px 40px;
      border: 2px dashed #dcdfe6;
      transition: all 0.3s;
      
      &:hover {
        border-color: #409eff;
        background: linear-gradient(135deg, #f8f9ff 0%, #e8ebff 100%);
      }
    }
    
    .upload-icon {
      font-size: 48px;
      color: #909399;
      margin-bottom: 16px;
    }
    
    .upload-text {
      font-size: 16px;
      color: #606266;
      margin-bottom: 8px;
    }
    
    .upload-hint {
      font-size: 13px;
      color: #909399;
    }
    
    .upload-database-hint {
      font-size: 13px;
      color: #67c23a;
      margin-top: 8px;
    }
  }
  
  .upload-actions {
    text-align: center;
  }
  
  .format-guide {
    .format-content {
      h4 {
        font-size: 14px;
        color: #303133;
        margin: 0 0 8px;
      }
      
      ul {
        margin: 0;
        padding-left: 20px;
        
        li {
          font-size: 13px;
          color: #606266;
          line-height: 1.8;
        }
      }
    }
  }
  
  // 管理卡片
  .management-card {
    .card-header {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .store-preview {
      margin-top: 16px;
    }
    
    .cleanup-actions {
      display: flex;
      gap: 12px;
      margin-top: 16px;
    }
  }
  
  // 缓存管理
  .cache-management {
    .cache-desc {
      color: #606266;
      margin-bottom: 16px;
    }
    
    .cache-levels {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .cache-level {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background: #f5f7fa;
      border-radius: 8px;
      
      .level-name {
        flex: 1;
        font-weight: 500;
        color: #303133;
      }
      
      .level-ttl {
        color: #909399;
        font-size: 13px;
        margin-right: 16px;
      }
    }
    
    .cache-actions {
      text-align: center;
    }
  }
  
  // 数据库优化
  .db-optimize {
    h4 {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 8px;
      color: #303133;
    }
    
    .optimize-desc {
      margin: 0;
      color: #909399;
      font-size: 13px;
    }
  }
  
  .text-right {
    text-align: right;
  }
  
  .text-warning {
    color: #e6a23c;
    font-weight: 500;
  }
  
  .mt-3 {
    margin-top: 12px;
  }
  
  .mt-4 {
    margin-top: 16px;
  }
  
  .mb-3 {
    margin-bottom: 12px;
  }
  
  .mb-4 {
    margin-bottom: 16px;
  }
}
</style>

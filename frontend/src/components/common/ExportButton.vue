<template>
  <el-dropdown @command="handleExport" :disabled="loading">
    <el-button :loading="loading">
      <el-icon><Download /></el-icon>
      {{ loading ? '导出中...' : '导出' }}
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="csv">
          <el-icon><Document /></el-icon>
          导出 CSV
        </el-dropdown-item>
        <el-dropdown-item command="excel">
          <el-icon><Document /></el-icon>
          导出 Excel
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Download, ArrowDown, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

interface Props {
  exportFn: (format: 'csv' | 'excel') => Promise<Blob>
  filename?: string
}

const props = withDefaults(defineProps<Props>(), {
  filename: 'export'
})

const loading = ref(false)

const handleExport = async (format: 'csv' | 'excel') => {
  loading.value = true
  
  try {
    const blob = await props.exportFn(format)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${props.filename}.${format === 'excel' ? 'xlsx' : 'csv'}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>


<template>
  <el-dialog v-model="visible" title="任务历史" width="900px">
    <el-alert
      v-if="history.length === 0"
      type="info"
      description="暂无历史任务"
      show-icon
      style="margin-bottom: 20px"
    />
    <div v-else class="history-list">
      <div v-for="task in sortedHistory" :key="task.id" class="history-item">
        <div class="history-item-header">
          <span class="task-id" @click="copyId(task.id)">
            <el-icon style="margin-right: 4px"><Document /></el-icon>
            {{ task.id }}
          </span>
          <el-tag :type="getStatusType(task.status)" size="small">
            {{ getStatusText(task.status) }}
          </el-tag>
        </div>
        <div class="history-item-info">
          <span class="info-item">
            <el-icon><Clock /></el-icon>
            {{ formatTime(task.created_at) }}
          </span>
          <span class="info-item">
            <el-icon><TrendCharts /></el-icon>
            {{ task.progress }}%
          </span>
        </div>
        <div class="history-item-actions">
          <el-button size="small" @click="viewTask(task)">
            查看详情
          </el-button>
          <el-button
            v-if="task.status === 'completed'"
            size="small"
            type="success"
            @click="downloadTask(task)"
          >
            下载论文
          </el-button>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="clearHistory" type="danger" :disabled="history.length === 0">
        清空历史
      </el-button>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, Clock, TrendCharts } from '@element-plus/icons-vue'
import { taskApi, type Task } from '../api'

const STORAGE_KEY = 'code_to_paper_history'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'viewTask'])

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

const history = ref<Task[]>([])

const loadHistory = () => {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (data) {
      history.value = JSON.parse(data)
    }
  } catch (e) {
    console.error('Failed to load history:', e)
  }
}

const saveHistory = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
  } catch (e) {
    console.error('Failed to save history:', e)
  }
}

const sortedHistory = computed(() => {
  return [...history.value].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )
})

const addToHistory = (task: Task) => {
  const index = history.value.findIndex((t) => t.id === task.id)
  if (index >= 0) {
    history.value[index] = task
  } else {
    history.value.unshift(task)
    if (history.value.length > 50) {
      history.value = history.value.slice(0, 50)
    }
  }
  saveHistory()
}

const removeFromHistory = (taskId: string) => {
  history.value = history.value.filter((t) => t.id !== taskId)
  saveHistory()
}

const getStatusType = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'danger'
  return 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    parsing_code: '解析代码中',
    analyzing_experiment: '分析实验中',
    generating_paper: '生成论文中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

const formatTime = (time: string) => {
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

const copyId = (id: string) => {
  navigator.clipboard.writeText(id)
  ElMessage.success('任务ID已复制')
}

const viewTask = (task: Task) => {
  emit('viewTask', task)
  visible.value = false
}

const downloadTask = (task: Task) => {
  taskApi.download(task.id)
}

const clearHistory = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有历史任务吗？', '确认', {
      type: 'warning'
    })
    history.value = []
    saveHistory()
    ElMessage.success('已清空历史记录')
  } catch {
    // 用户取消
  }
}

defineExpose({
  addToHistory,
  removeFromHistory,
  loadHistory
})

loadHistory()
</script>

<style scoped>
.history-list {
  max-height: 60vh;
  overflow-y: auto;
}

.history-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: #fafafa;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-id {
  font-family: monospace;
  font-size: 14px;
  color: #409eff;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.task-id:hover {
  text-decoration: underline;
}

.history-item-info {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  color: #666;
  font-size: 13px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.history-item-actions {
  display: flex;
  gap: 8px;
}
</style>

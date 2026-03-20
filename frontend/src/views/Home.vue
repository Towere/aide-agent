<template>
  <el-card>
    <template #header>
      <span>创建论文生成任务</span>
    </template>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Git仓库" name="git">
        <el-form label-width="100px">
          <el-form-item label="仓库URL">
            <el-input v-model="gitUrl" placeholder="https://github.com/user/repo.git" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitGit" :loading="loading">
              开始生成
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="上传ZIP" name="zip">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".zip"
        >
          <el-button type="primary">选择ZIP文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              请上传包含代码的ZIP压缩文件
            </div>
          </template>
        </el-upload>
        <el-button
          type="primary"
          style="margin-top: 20px"
          :disabled="!selectedFile"
          :loading="loading"
          @click="submitZip"
        >
          开始生成
        </el-button>
      </el-tab-pane>
    </el-tabs>
  </el-card>

  <el-card v-if="currentTask" style="margin-top: 20px">
    <template #header>
      <span>任务状态</span>
    </template>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
      <el-descriptions-item label="状态">
        <el-tag :type="statusType">{{ statusText }}</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="进度" :span="2">
        <el-progress :percentage="currentTask.progress" :status="progressStatus" />
      </el-descriptions-item>
    </el-descriptions>

    <el-alert
      v-if="currentTask.error_message"
      type="error"
      :title="currentTask.error_message"
      style="margin-top: 20px"
      show-icon
    />

    <div v-if="currentTask.paper_content" style="margin-top: 20px">
      <el-button type="success" @click="downloadPaper">
        <el-icon><Download /></el-icon>
        下载论文
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { taskApi, type Task } from '../api'

const activeTab = ref('git')
const gitUrl = ref('')
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const currentTask = ref<Task | null>(null)
let pollTimer: number | null = null

const statusType = computed(() => {
  const s = currentTask.value?.status
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'danger'
  return 'info'
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    parsing_code: '解析代码中',
    analyzing_experiment: '分析实验中',
    generating_paper: '生成论文中',
    completed: '已完成',
    failed: '失败'
  }
  return map[currentTask.value?.status || ''] || currentTask.value?.status
})

const progressStatus = computed(() => {
  const s = currentTask.value?.status
  if (s === 'completed') return 'success'
  if (s === 'failed') return 'exception'
  return undefined
})

const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

const submitGit = async () => {
  if (!gitUrl.value) {
    ElMessage.warning('请输入Git仓库URL')
    return
  }
  loading.value = true
  try {
    currentTask.value = await taskApi.createByGit(gitUrl.value)
    ElMessage.success('任务创建成功')
    startPolling()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    loading.value = false
  }
}

const submitZip = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择ZIP文件')
    return
  }
  loading.value = true
  try {
    currentTask.value = await taskApi.createByZip(selectedFile.value)
    ElMessage.success('任务创建成功')
    startPolling()
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  } finally {
    loading.value = false
  }
}

const startPolling = () => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = window.setInterval(async () => {
    if (currentTask.value) {
      currentTask.value = await taskApi.get(currentTask.value.id)
      if (['completed', 'failed'].includes(currentTask.value.status)) {
        stopPolling()
      }
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const downloadPaper = () => {
  if (currentTask.value) {
    taskApi.download(currentTask.value.id)
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

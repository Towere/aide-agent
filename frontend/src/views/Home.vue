<template>
  <el-card>
    <template #header>
      <span>创建论文生成任务</span>
    </template>

    <el-form label-width="100px" style="margin-bottom: 20px">
      <el-form-item label="论文语言">
        <el-radio-group v-model="paperLanguage">
          <el-radio-button value="en">English</el-radio-button>
          <el-radio-button value="zh">中文</el-radio-button>
          <el-radio-button value="bilingual">双语对照</el-radio-button>
        </el-radio-group>
      </el-form-item>
    </el-form>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="Git仓库" name="git">
        <el-form label-width="100px">
          <el-form-item label="仓库URL">
            <el-input v-model="gitUrl" placeholder="https://github.com/user/repo.git" />
          </el-form-item>
          <el-form-item label="模板文件">
            <el-upload
              ref="templateUploadGitRef"
              :auto-upload="false"
              :on-change="handleTemplateChangeGit"
              :on-remove="handleTemplateRemoveGit"
              :limit="1"
              accept=".json"
            >
              <el-button>选择paper_template.json</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  可选：上传自定义paper_template.json模板文件
                </div>
              </template>
            </el-upload>
            <div v-if="selectedTemplateGit" class="selected-template">
              <el-icon><Document /></el-icon>
              <span>{{ selectedTemplateGit.name }}</span>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitGit" :loading="loading">
              开始生成
            </el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="上传ZIP" name="zip">
        <el-form label-width="100px">
          <el-form-item label="代码文件">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
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
            <div v-if="selectedFile" class="selected-file">
              <el-icon><Document /></el-icon>
              <span>{{ selectedFile.name }}</span>
            </div>
          </el-form-item>
          <el-form-item label="模板文件">
            <el-upload
              ref="templateUploadZipRef"
              :auto-upload="false"
              :on-change="handleTemplateChangeZip"
              :on-remove="handleTemplateRemoveZip"
              :limit="1"
              accept=".json"
            >
              <el-button>选择paper_template.json</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  可选：上传自定义paper_template.json模板文件
                </div>
              </template>
            </el-upload>
            <div v-if="selectedTemplateZip" class="selected-template">
              <el-icon><Document /></el-icon>
              <span>{{ selectedTemplateZip.name }}</span>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :disabled="!selectedFile"
              :loading="loading"
              @click="submitZip"
            >
              开始生成
            </el-button>
          </el-form-item>
        </el-form>
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
      <el-radio-group v-model="downloadFormat" style="margin-right: 16px">
        <el-radio-button value="md">Markdown</el-radio-button>
        <el-radio-button value="docx">Word</el-radio-button>
      </el-radio-group>
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
import { Download, Document } from '@element-plus/icons-vue'
import { taskApi, type Task } from '../api'

const activeTab = ref('git')
const gitUrl = ref('')
const selectedFile = ref<File | null>(null)
const selectedTemplateGit = ref<File | null>(null)
const selectedTemplateZip = ref<File | null>(null)
const downloadFormat = ref<'md' | 'docx'>('docx')
const paperLanguage = ref<'en' | 'zh' | 'bilingual'>('en')
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

const handleFileRemove = () => {
  selectedFile.value = null
}

const handleTemplateChangeGit = (file: any) => {
  selectedTemplateGit.value = file.raw
}

const handleTemplateRemoveGit = () => {
  selectedTemplateGit.value = null
}

const handleTemplateChangeZip = (file: any) => {
  selectedTemplateZip.value = file.raw
}

const handleTemplateRemoveZip = () => {
  selectedTemplateZip.value = null
}

const submitGit = async () => {
  if (!gitUrl.value) {
    ElMessage.warning('请输入Git仓库URL')
    return
  }
  loading.value = true
  try {
    currentTask.value = await taskApi.createByGit(
      gitUrl.value,
      selectedTemplateGit.value || undefined,
      paperLanguage.value
    )
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
    currentTask.value = await taskApi.createByZip(
      selectedFile.value,
      selectedTemplateZip.value || undefined,
      paperLanguage.value
    )
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
    taskApi.download(currentTask.value.id, downloadFormat.value)
  }
}

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.selected-file,
.selected-template {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  margin-top: 8px;
}
</style>

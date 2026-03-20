import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export interface Task {
  id: string
  status: 'pending' | 'parsing_code' | 'analyzing_experiment' | 'generating_paper' | 'completed' | 'failed'
  progress: number
  created_at: string
  updated_at: string
  paper_content?: string
  error_message?: string
}

export const taskApi = {
  async createByGit(url: string): Promise<Task> {
    const formData = new FormData()
    formData.append('input_type', 'git_url')
    formData.append('input_source', url)
    const { data } = await api.post('/tasks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  },

  async createByZip(file: File): Promise<Task> {
    const formData = new FormData()
    formData.append('input_type', 'zip_upload')
    formData.append('file', file)
    const { data } = await api.post('/tasks', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  },

  async get(taskId: string): Promise<Task> {
    const { data } = await api.get(`/tasks/${taskId}`)
    return data
  },

  download(taskId: string) {
    window.open(`/api/tasks/${taskId}/download`, '_blank')
  }
}

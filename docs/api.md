# API 文档

## 目录
- [基础信息](#基础信息)
- [认证](#认证)
- [通用响应格式](#通用响应格式)
- [API端点](#api端点)
- [错误码](#错误码)
- [示例代码](#示例代码)

## 基础信息

**Base URL**: `http://localhost:7348`

**API版本**: v1

**Content-Type**: `application/json` (除非另有说明)

**在线文档**: http://localhost:7348/docs (Swagger UI)

## 认证

当前版本无需认证，所有API端点公开访问。

## 通用响应格式

### 成功响应

```json
{
  "id": "uuid-string",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-03-25T10:00:00",
  "updated_at": "2026-03-25T10:00:00"
}
```

### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

## API端点

### 1. 健康检查

检查API服务状态。

```http
GET /health
```

**响应示例**:
```json
{
  "status": "healthy"
}
```

---

### 2. 根路径

获取API基本信息。

```http
GET /
```

**响应示例**:
```json
{
  "message": "Code to Paper API",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 3. 创建论文生成任务

创建一个新的论文生成任务。支持Git URL和ZIP文件上传两种方式。

```http
POST /api/tasks
Content-Type: multipart/form-data
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `input_type` | string | 是 | 输入类型: `git_url` 或 `zip_upload` |
| `input_source` | string | 否 | Git仓库URL (input_type=git_url时必填) |
| `file` | File | 否 | ZIP文件 (input_type=zip_upload时必填) |
| `template_file` | File | 否 | 自定义paper_template.json模板文件 (可选) |
| `language` | string | 否 | 论文语言: `en` (英文), `zh` (中文), `bilingual` (双语), 默认: `en` |

**请求示例 - Git URL方式**:

```bash
curl -X POST http://localhost:7348/api/tasks \
  -F "input_type=git_url" \
  -F "input_source=https://github.com/user/repo.git" \
  -F "language=en"
```

**请求示例 - ZIP上传方式**:

```bash
curl -X POST http://localhost:7348/api/tasks \
  -F "input_type=zip_upload" \
  -F "file=@/path/to/code.zip" \
  -F "language=zh"
```

**请求示例 - 带自定义模板**:

```bash
curl -X POST http://localhost:7348/api/tasks \
  -F "input_type=git_url" \
  -F "input_source=https://github.com/user/repo.git" \
  -F "template_file=@./paper_template.json" \
  -F "language=bilingual"
```

**成功响应 (200 OK)**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "created_at": "2026-03-25T10:00:00",
  "updated_at": "2026-03-25T10:00:00"
}
```

**错误响应**:

| HTTP状态码 | 说明 |
|-----------|------|
| 400 Bad Request | 参数错误 (缺少必填项、无效的语言选项、模板JSON格式错误等) |
| 503 Service Unavailable | Redis连接失败，任务队列不可用 |
| 500 Internal Server Error | 服务器内部错误 |

---

### 4. 获取任务详情

查询任务状态、进度和结果。

```http
GET /api/tasks/{task_id}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 任务ID (UUID) |

**请求示例**:

```bash
curl http://localhost:7348/api/tasks/550e8400-e29b-41d4-a716-446655440000
```

**成功响应 (200 OK)**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "generating_paper",
  "progress": 65,
  "created_at": "2026-03-25T10:00:00",
  "updated_at": "2026-03-25T10:05:30",
  "paper_content": null,
  "error_message": null
}
```

**任务完成时的响应**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "created_at": "2026-03-25T10:00:00",
  "updated_at": "2026-03-25T10:15:00",
  "paper_content": "# 论文标题\n\n## Abstract\n...",
  "error_message": null
}
```

**任务失败时的响应**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 30,
  "created_at": "2026-03-25T10:00:00",
  "updated_at": "2026-03-25T10:02:15",
  "paper_content": null,
  "error_message": "Git clone failed: Authentication failed"
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务ID (UUID) |
| `status` | string | 任务状态，见下方状态枚举 |
| `progress` | integer | 进度百分比 (0-100) |
| `created_at` | string | 创建时间 (ISO 8601) |
| `updated_at` | string | 更新时间 (ISO 8601) |
| `paper_content` | string/null | 论文内容 (Markdown)，完成时填充 |
| `error_message` | string/null | 错误信息，失败时填充 |

**任务状态枚举**:

| 状态值 | 说明 |
|--------|------|
| `pending` | 任务已创建，等待处理 |
| `parsing_code` | 正在解析代码仓库 |
| `analyzing_experiment` | 正在分析实验配置 |
| `generating_structure` | 正在生成论文结构 |
| `generating_paper` | 正在生成论文内容 |
| `optimizing_content` | 正在优化论文内容 |
| `generating_diagrams` | 正在生成架构图表 |
| `integrating_diagrams` | 正在集成图表 |
| `formatting_paper` | 正在格式化论文 |
| `completed` | 任务完成 |
| `failed` | 任务失败 |

**错误响应**:

| HTTP状态码 | 说明 |
|-----------|------|
| 404 Not Found | 任务不存在 |

---

### 5. 下载论文

下载生成的论文，支持Markdown和Word两种格式。

```http
GET /api/tasks/{task_id}/download?format={format}
```

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | 是 | 任务ID (UUID) |

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `format` | string | 否 | 下载格式: `md` (Markdown) 或 `docx` (Word), 默认: `md` |

**请求示例 - 下载Markdown**:

```bash
curl -o paper.md http://localhost:7348/api/tasks/550e8400-e29b-41d4-a716-446655440000/download
```

**请求示例 - 下载Word**:

```bash
curl -o paper.docx http://localhost:7348/api/tasks/550e8400-e29b-41d4-a716-446655440000/download?format=docx
```

**成功响应**:

- **Markdown格式**:
  - Content-Type: `text/markdown`
  - Content-Disposition: `attachment; filename="paper_{task_id}.md"`

- **Word格式**:
  - Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - Content-Disposition: `attachment; filename="paper_{task_id}.docx"`

**错误响应**:

| HTTP状态码 | 说明 |
|-----------|------|
| 404 Not Found | 任务不存在 |
| 400 Bad Request | 论文尚未生成或任务失败 |

---

## 数据模型

### TaskResponse

任务响应模型。

```typescript
interface TaskResponse {
  id: string;                    // UUID
  status: TaskStatus;           // 任务状态
  progress: number;             // 0-100
  created_at: string;           // ISO 8601
  updated_at: string;           // ISO 8601
  paper_content?: string | null; // Markdown内容
  error_message?: string | null; // 错误信息
}
```

### TaskStatus

任务状态枚举。

```typescript
type TaskStatus =
  | 'pending'
  | 'parsing_code'
  | 'analyzing_experiment'
  | 'generating_structure'
  | 'generating_paper'
  | 'optimizing_content'
  | 'generating_diagrams'
  | 'integrating_diagrams'
  | 'formatting_paper'
  | 'completed'
  | 'failed';
```

### InputType

输入类型枚举。

```typescript
type InputType = 'git_url' | 'zip_upload';
```

### PaperLanguage

论文语言枚举。

```typescript
type PaperLanguage = 'en' | 'zh' | 'bilingual';
```

---

## 错误码

| HTTP状态码 | 错误信息 | 说明 |
|-----------|---------|------|
| 400 | "Git URL required" | input_type=git_url但未提供input_source |
| 400 | "Zip file required" | input_type=zip_upload但未提供file |
| 400 | "无效的语言选项: {language}，可选值: en, zh, bilingual" | language参数无效 |
| 400 | "模板JSON格式错误: {detail}" | template_file不是有效的JSON |
| 400 | "Paper not available" | 尝试下载但论文尚未生成 |
| 404 | "Task not found" | 任务ID不存在 |
| 503 | "任务队列服务不可用，请稍后重试" | Redis连接失败 |
| 500 | "{exception message}" | 服务器内部错误 |

---

## 示例代码

### Python (requests)

```python
import requests
import time

BASE_URL = "http://localhost:7348"

# 1. 创建任务 (Git URL方式)
def create_task_git(git_url, language="en"):
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        data={
            "input_type": "git_url",
            "input_source": git_url,
            "language": language
        }
    )
    response.raise_for_status()
    return response.json()

# 2. 创建任务 (ZIP上传方式)
def create_task_zip(zip_path, language="en"):
    with open(zip_path, "rb") as f:
        files = {"file": f}
        data = {
            "input_type": "zip_upload",
            "language": language
        }
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            files=files,
            data=data
        )
    response.raise_for_status()
    return response.json()

# 3. 轮询任务状态
def poll_task(task_id, interval=2):
    while True:
        response = requests.get(f"{BASE_URL}/api/tasks/{task_id}")
        response.raise_for_status()
        task = response.json()

        status = task["status"]
        progress = task["progress"]
        print(f"Status: {status}, Progress: {progress}%")

        if status == "completed":
            return task
        elif status == "failed":
            raise Exception(f"Task failed: {task['error_message']}")

        time.sleep(interval)

# 4. 下载论文
def download_paper(task_id, format="md", output_path=None):
    response = requests.get(
        f"{BASE_URL}/api/tasks/{task_id}/download",
        params={"format": format}
    )
    response.raise_for_status()

    if not output_path:
        output_path = f"paper_{task_id}.{format}"

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path

# 完整流程示例
if __name__ == "__main__":
    # 创建任务
    task = create_task_git(
        "https://github.com/user/repo.git",
        language="en"
    )
    task_id = task["id"]
    print(f"Task created: {task_id}")

    # 等待完成
    task = poll_task(task_id)
    print("Task completed!")

    # 下载论文
    md_path = download_paper(task_id, format="md")
    print(f"Markdown saved to: {md_path}")

    docx_path = download_paper(task_id, format="docx")
    print(f"Word saved to: {docx_path}")
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const BASE_URL = 'http://localhost:7348';

// 创建任务 (Git URL)
export async function createTaskGit(gitUrl, language = 'en') {
  const formData = new FormData();
  formData.append('input_type', 'git_url');
  formData.append('input_source', gitUrl);
  formData.append('language', language);

  const response = await axios.post(`${BASE_URL}/api/tasks`, formData);
  return response.data;
}

// 创建任务 (ZIP上传)
export async function createTaskZip(file, language = 'en') {
  const formData = new FormData();
  formData.append('input_type', 'zip_upload');
  formData.append('file', file);
  formData.append('language', language);

  const response = await axios.post(`${BASE_URL}/api/tasks`, formData);
  return response.data;
}

// 获取任务状态
export async function getTask(taskId) {
  const response = await axios.get(`${BASE_URL}/api/tasks/${taskId}`);
  return response.data;
}

// 轮询任务直到完成
export async function pollTask(taskId, onProgress, interval = 2000) {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const task = await getTask(taskId);

        if (onProgress) {
          onProgress(task);
        }

        if (task.status === 'completed') {
          resolve(task);
        } else if (task.status === 'failed') {
          reject(new Error(task.error_message));
        } else {
          setTimeout(poll, interval);
        }
      } catch (error) {
        reject(error);
      }
    };
    poll();
  });
}

// 下载论文
export async function downloadPaper(taskId, format = 'md') {
  const response = await axios.get(
    `${BASE_URL}/api/tasks/${taskId}/download`,
    {
      params: { format },
      responseType: 'blob'
    }
  );

  // 创建下载链接
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `paper_${taskId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// 使用示例
/*
async function main() {
  // 创建任务
  const task = await createTaskGit('https://github.com/user/repo.git', 'en');
  console.log('Task created:', task.id);

  // 轮询进度
  await pollTask(task.id, (task) => {
    console.log(`Progress: ${task.progress}%, Status: ${task.status}`);
  });

  // 下载
  await downloadPaper(task.id, 'md');
  await downloadPaper(task.id, 'docx');
}
*/
```

### cURL

```bash
# 创建任务 (Git URL)
curl -X POST http://localhost:7348/api/tasks \
  -F "input_type=git_url" \
  -F "input_source=https://github.com/user/repo.git" \
  -F "language=en"

# 创建任务 (ZIP上传)
curl -X POST http://localhost:7348/api/tasks \
  -F "input_type=zip_upload" \
  -F "file=@./code.zip" \
  -F "language=zh"

# 查询任务状态
curl http://localhost:7348/api/tasks/{task_id}

# 下载Markdown
curl -o paper.md http://localhost:7348/api/tasks/{task_id}/download

# 下载Word
curl -o paper.docx "http://localhost:7348/api/tasks/{task_id}/download?format=docx"
```

---

## WebSocket (计划中)

实时进度推送功能计划在未来版本中支持。当前版本请使用轮询方式获取任务状态。

---

## 速率限制

当前版本未实施严格的速率限制，但请合理使用API资源。建议:

- 任务状态轮询间隔不低于2秒
- 并发任务数不超过Worker数量 (默认2个)

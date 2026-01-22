# 快速启动指南

## 🚀 5分钟快速开始

### 步骤1：安装后端依赖

```bash
conda activate nlp
cd backend
pip install -r requirements.txt
```

### 步骤2：启动后端服务

```bash
python run.py
```

看到以下信息表示启动成功：

```
 * Running on http://0.0.0.0:5000
```

### 步骤3：安装前端依赖（新终端）

```bash
cd frontend
npm install
```

### 步骤4：启动前端应用

```bash
npm start
```

浏览器会自动打开 http://localhost:3000

## 🔑 环境变量配置

### Suno API 配置（歌曲生成功能）

如果需要使用歌曲生成功能，需要配置 Suno API Key：

```bash
# Windows PowerShell
$env:SUNO_API_KEY="your-suno-api-key"

# Linux/Mac
export SUNO_API_KEY="your-suno-api-key"
```

或者创建 `.env` 文件（推荐）：

```bash
# 在 backend 目录下创建 .env 文件
cd backend
# Windows PowerShell
Set-Content -Path .env -Value "SUNO_API_KEY=your-suno-api-key"
# 或者使用记事本创建 .env 文件，内容为：
# SUNO_API_KEY=your-suno-api-key
# Linux/Mac
echo "SUNO_API_KEY=your-suno-api-key" > .env
```

**重要提示：**

- 如果环境变量已设置在系统变量中但仍无法读取，请：
  1. 在 `backend` 目录下创建 `.env` 文件（推荐方法）
  2. 重启后端服务（必须重启才能读取新的环境变量）
  3. 确认环境变量名称完全正确：`SUNO_API_KEY`（区分大小写）

**配置说明：**

- 请将 `your-suno-api-key` 替换为您的实际 API Key
- 如果需要在代码中直接使用，可以在 `backend/.env` 文件中设置
- 参考 `backend/.env.example` 文件查看配置格式
- **重要**：请勿将包含真实 API Key 的 `.env` 文件提交到版本控制系统

## 📝 测试功能

### 1. 基础分析测试

1. 访问 http://localhost:3000/analysis
2. 输入测试歌词：

```
我爱你
就像爱春天
你是我心中的
最美的风景
```

3. 点击"开始分析"
4. 查看分析结果

### 2. 创作助手测试

1. 访问 http://localhost:3000/generation
2. 选择"主题生成"标签
3. 选择主题：爱情，情感：积极，长度：4行
4. 点击"生成歌词"
5. 查看生成结果

### 3. 智能推荐测试

1. 访问 http://localhost:3000/recommendation
2. 输入歌词：

```
追逐梦想
永不放弃
坚持到底
成功在望
```

3. 点击"获取推荐"
4. 查看推荐结果

### 4. 歌曲生成测试（需要 Suno API Key）

#### 方式1：使用 API 直接调用（异步模式，推荐）

```bash
# 提交生成任务
curl -X POST http://localhost:5000/api/generation/song \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "我爱你\n就像爱春天\n你是我心中的\n最美的风景",
    "title": "春天的爱",
    "tags": "pop, cheerful, romantic",
    "async_mode": true
  }'

# 返回示例：
# {
#   "success": true,
#   "data": {
#     "task_id": "ta12345678-1234-1234-1234-123456789abc",
#     "status": "pending",
#     "message": "歌曲生成任务已提交，请使用 task_id 查询进度",
#     "query_url": "/api/generation/song/status?task_id=..."
#   }
# }

# 查询任务状态
curl "http://localhost:5000/api/generation/song/status?task_id=ta12345678-1234-1234-1234-123456789abc"
```

#### 方式2：同步模式（等待完成，可能需要较长时间）

```bash
curl -X POST http://localhost:5000/api/generation/song \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "我爱你\n就像爱春天\n你是我心中的\n最美的风景",
    "title": "春天的爱",
    "style": "流行",
    "async_mode": false,
    "max_wait_time": 300
  }'
```

#### 参数说明

- `lyrics` (必需): 歌词内容
- `title` (可选): 歌曲标题，如果不提供则从歌词第一行提取
- `tags` (可选): 风格标签，如 "pop, cheerful, summer"
- `style` (可选): 音乐风格（流行/摇滚/抒情/古风等），会自动转换为 tags
- `make_instrumental` (可选): 是否生成纯音乐，默认 false
- `async_mode` (可选): 是否异步模式，默认 true（推荐）
- `max_wait_time` (可选): 最大等待时间（秒），仅同步模式有效，默认 300

## ⚠️ 常见问题

### 问题1：后端启动失败

**错误**：`ModuleNotFoundError: No module named 'flask'`

**解决**：

```bash
pip install -r requirements.txt
```

### 问题2：前端启动失败

**错误**：`Cannot find module 'react'`

**解决**：

```bash
cd frontend
npm install
```

### 问题3：数据库错误

**错误**：`OperationalError: unable to open database file`

**解决**：

- 确保 `data` 目录存在
- 检查文件权限
- 手动创建目录：`mkdir -p data`

### 问题4：端口被占用

**错误**：`Address already in use`

**解决**：

- 后端：修改 `run.py` 中的端口号
- 前端：修改 `package.json` 中的代理地址

### 问题5：Suno API 歌曲生成失败

**错误**：`Suno API key is required` 或 `Failed to call Suno API`

**解决**：

1. 确保已设置 `SUNO_API_KEY` 环境变量
2. 检查 API Key 是否有效
3. 确认网络连接正常（需要访问 https://api.defapi.org）
4. 检查 API Key 是否有足够的额度

## 🎯 功能演示

### 完整工作流示例

1. **分析歌词** → 了解歌词的情感、主题、韵律
2. **生成歌词** → 基于分析结果生成相似风格歌词
3. **生成歌曲** → 使用 Suno API 将歌词转换为完整歌曲（需要 API Key）
4. **获取推荐** → 在知识图谱中推荐相关音乐
5. **查看历史** → 所有操作自动保存到历史记录

## 📚 更多信息

- 详细文档：查看 `README.md`
- 安装指南：查看 `INSTALL.md`
- 项目总结：查看 `PROJECT_SUMMARY.md`














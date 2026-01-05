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

## 🎯 功能演示

### 完整工作流示例

1. **分析歌词** → 了解歌词的情感、主题、韵律
2. **生成歌词** → 基于分析结果生成相似风格歌词
3. **获取推荐** → 在知识图谱中推荐相关音乐
4. **查看历史** → 所有操作自动保存到历史记录

## 📚 更多信息

- 详细文档：查看 `README.md`
- 安装指南：查看 `INSTALL.md`
- 项目总结：查看 `PROJECT_SUMMARY.md`








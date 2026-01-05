# 🎵 一体化音乐NLP应用系统

一个从基础分析到智能创作的全栈音乐NLP应用系统。

## 📋 项目结构

```
music/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/         # API路由
│   │   │   ├── analysis.py
│   │   │   ├── generation.py
│   │   │   ├── recommendation.py
│   │   │   └── user.py
│   │   ├── models/      # 数据模型
│   │   │   ├── user.py
│   │   │   └── analysis.py
│   │   ├── services/    # 业务逻辑
│   │   │   ├── analysis_service.py
│   │   │   ├── generation_service.py
│   │   │   └── recommendation_service.py
│   │   └── utils/       # 工具函数
│   ├── nlp_engine/      # NLP核心引擎
│   │   ├── sentiment/   # 情感分析
│   │   ├── theme/       # 主题提取
│   │   ├── rhythm/      # 韵律分析
│   │   ├── generation/  # 歌词生成
│   │   └── recommendation/  # 推荐系统
│   ├── requirements.txt
│   └── run.py
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # React组件
│   │   │   └── Layout/
│   │   ├── pages/       # 页面
│   │   │   ├── HomePage.js
│   │   │   ├── AnalysisPage.js
│   │   │   ├── GenerationPage.js
│   │   │   ├── RecommendationPage.js
│   │   │   └── HistoryPage.js
│   │   ├── services/    # API服务
│   │   │   └── api.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── public/
├── data/                # 数据存储
│   └── database.db      # SQLite数据库（自动创建）
├── start_backend.bat    # Windows后端启动脚本
├── start_frontend.bat   # Windows前端启动脚本
└── README.md
```

## ✨ 功能特性

### 📊 第一层：基础分析（入门级）
- **情感脉搏分析**：逐句情感检测、情感强度变化曲线、整体情感基调判断
- **主题解构**：自动提取关键词、主题聚类分析、生成主题词云
- **韵律初探**：基础押韵检测、押韵模式可视化、押韵质量评分
- **可视化报告**：情感时间线图表、情感分布雷达图、一键生成分析简报

### ✍️ 第二层：创作助手（中升级）
- **智能歌词生成**：给定主题/情绪生成歌词片段、上下文感知的下一句建议、完整副歌/主歌生成
- **创作优化工具**：押韵优化建议、风格转换、歌词润色与改写
- **结构分析**：歌曲结构识别、段落重复性分析、歌词节奏与音节分析
- **创作评估**：原创性检测、情感一致性检查、押韵流畅度评分

### 🎯 第三层：智能系统（高级版）
- **多模态音乐理解**：歌词-情感-旋律关联分析、用户评论语义整合
- **可解释推荐系统**：个性化歌曲推荐、推荐理由生成、相似度路径分析
- **音乐知识图谱**：歌手-风格-流派关系网络、歌词主题演化分析
- **深度洞察**：歌词中的文化价值观分析、热门歌曲"成功公式"解构

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+
- npm 或 yarn

### 后端启动

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 启动服务：
```bash
python run.py
```

后端服务将在 http://localhost:5000 启动

### 前端启动

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm start
```

前端应用将在 http://localhost:3000 启动

### 快速启动（Windows）

- 双击 `start_backend.bat` 启动后端
- 双击 `start_frontend.bat` 启动前端

### 快速启动（Linux/Mac）

```bash
chmod +x start_backend.sh start_frontend.sh
./start_backend.sh  # 终端1
./start_frontend.sh  # 终端2
```

## 🛠️ 技术栈

### 后端
- **框架**：Flask 2.3.3
- **数据库**：SQLAlchemy + SQLite
- **NLP库**：
  - jieba（中文分词）
  - snownlp（情感分析）
  - scikit-learn（相似度计算）
- **其他**：Flask-CORS, numpy, pandas

### 前端
- **框架**：React 18.2.0
- **UI库**：Ant Design 5.12.0
- **图表**：ECharts 5.4.3
- **词云**：react-wordcloud
- **路由**：React Router 6.8.0

## 📖 API文档

### 分析API
- `POST /api/analysis/analyze` - 完整分析歌词
- `POST /api/analysis/sentiment` - 情感分析
- `POST /api/analysis/theme` - 主题分析
- `POST /api/analysis/rhythm` - 韵律分析
- `GET /api/analysis/history` - 获取分析历史

### 生成API
- `POST /api/generation/by-theme` - 根据主题生成
- `POST /api/generation/by-context` - 基于上下文生成
- `POST /api/generation/full-song` - 生成完整歌曲
- `POST /api/generation/optimize-rhyme` - 押韵优化
- `POST /api/generation/convert-style` - 风格转换
- `POST /api/generation/evaluate` - 创作评估

### 推荐API
- `POST /api/recommendation/recommend` - 推荐歌曲
- `GET /api/recommendation/knowledge-graph` - 获取知识图谱
- `GET /api/recommendation/preferences` - 获取用户偏好
- `PUT /api/recommendation/preferences` - 更新用户偏好

## 📝 使用示例

### 分析歌词
```javascript
// 前端调用
const response = await analysisAPI.analyze(lyrics);
console.log(response.data);
```

### 生成歌词
```javascript
// 根据主题生成
const response = await generationAPI.generateByTheme('爱情', '积极', 4);
console.log(response.data.lyrics);
```

### 获取推荐
```javascript
// 推荐相似歌曲
const response = await recommendationAPI.recommend(lyrics, 5);
console.log(response.data.recommendations);
```

## 🔧 配置说明

### 后端配置
- 数据库路径：`data/database.db`（自动创建）
- 端口：5000（可在 `run.py` 中修改）
- CORS：已启用，允许跨域请求

### 前端配置
- API代理：`package.json` 中配置了代理到 `http://localhost:5000`
- 端口：3000（React默认）

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请提交 Issue。


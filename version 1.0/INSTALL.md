# 安装指南

## 环境要求

- Python 3.8+
- Node.js 14+
- npm 或 yarn

## 后端安装

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 初始化数据库：
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

5. 启动服务：
```bash
python run.py
```

后端服务将在 http://localhost:5000 启动

## 前端安装

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm start
```

前端应用将在 http://localhost:3000 启动

## 快速启动

### Windows
- 双击 `start_backend.bat` 启动后端
- 双击 `start_frontend.bat` 启动前端

### Linux/Mac
```bash
chmod +x start_backend.sh start_frontend.sh
./start_backend.sh  # 终端1
./start_frontend.sh  # 终端2
```

## 注意事项

1. 确保后端服务先启动
2. 前端会自动代理到后端API
3. 首次运行会自动创建数据库文件








# FreedomForge

> **Forge Your Tools. Own Your Freedom.**  
> 一个属于你的个人自动化中枢 —— 集脚本管理、任务调度、量化实验于一体的专属工具平台。

![FreedomForge Banner](https://via.placeholder.com/1200x300/0f172a/00f5d4?text=FreedomForge+-+Your+Personal+Automation+Hub)
> *（未来可替换为真实截图）*

## 🌟 核心理念

- **自主可控**：所有代码运行在本地，数据永不外泄  
- **极简高效**：一键执行常用 Python 脚本，告别命令行记忆负担  
- **无限扩展**：从文件整理到量化回测，模块化设计支持任意功能接入  
- **颜值即正义**：现代化 UI + 暗色主题，长时间使用不疲劳

## 🧰 当前功能

- ✅ **用户认证系统**  
  - 基于 JWT 的安全登录（FastAPI 后端）
  - 密码哈希存储（bcrypt）
- ✅ **脚本管理中心（开发中）**  
  - 浏览 `scripts/` 目录下的所有 `.py` 文件
  - 一键执行 & 查看日志
- 🔜 **量化交易沙盒（规划中）**  
  - 回测框架集成
  - 实时信号监控

## 📂 项目结构
FreedomForge/
├── backend/ # FastAPI 服务端
│ ├── main.py # API 入口（含 /token, /users/me）
│ ├── database.py # SQLite 用户数据库
│ └── scripts/ # ← 你的 Python 脚本放这里！
├── frontend/ # Naive UI Admin 前端
│ ├── src/api/ # API 请求封装
│ ├── src/views/ # 页面组件
│ └── ...
├── docs/ # 设计文档 & 使用指南
└── README.md # 本文件


## 🚀 快速启动

### 前置要求
- Node.js ≥ v18 ([下载](https://nodejs.org/))
- Python ≥ 3.8
- pnpm（已配置全局路径至非系统盘）

### 启动后端
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 启动前端
```bash
cd frontend
pnpm install
pnpm dev
```

✅ 访问 [http://localhost:9527](http://localhost:9527)  
默认账号：`admin` / 密码：`123456`

## 🔒 **安全说明**  
- 所有用户密码经 **bcrypt 哈希** 存储  
- JWT Token 有效期 24 小时  
- 生产部署时务必修改 `SECRET_KEY`

## 🤝 **贡献与扩展**  
本项目为 **个人工具集**，但欢迎：  
- 提交 Issue 报告 Bug  
- Fork 后定制自己的模块  
- 在 `scripts/` 目录添加你的 Python 脚本  

💡 **命名规范**：脚本文件请以 `功能_描述.py` 命名（如 `file_move_mp4.py`）

## 📜 **许可证**  
MIT License - 自由使用，但请保留作者署名。

> **Made with ❤️ by Freedom**  
> *“The best tool is the one you build for yourself.”*
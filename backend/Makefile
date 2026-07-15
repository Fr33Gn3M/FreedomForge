# backend/Makefile
# 输入 make 或 make help 查看所有可用命令
# 效果类似前端 package.json 的 scripts

.PHONY: help install run dev db-reset clean

# 默认显示帮助
help:
	@echo ""
	@echo "  FreedomForge 后端命令面板"
	@echo "  =========================="
	@echo ""
	@echo "  make install    安装 Python 依赖"
	@echo "  make run        启动服务 (生产模式)"
	@echo "  make dev        启动服务 (开发模式，热重载)"
	@echo "  make db-reset   重置数据库"
	@echo "  make clean      清理缓存文件"
	@echo ""

# 安装依赖
install:
	pip install -r requirements.txt

# 生产模式启动
run:
	python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 开发模式启动（修改代码自动重启）
dev:
	python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 重置 SQLite 数据库
db-reset:
	@rm -f data/users.db
	@echo "数据库已删除，重启服务后自动重建"

# 清理 Python 缓存
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "缓存已清理"

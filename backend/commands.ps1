# backend/commands.ps1
# 用法: .\commands.ps1 <命令>
# 效果类似前端 package.json 的 scripts

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

switch ($Command) {
    "help" {
        Write-Host ""
        Write-Host "  FreedomForge 后端命令面板" -ForegroundColor Cyan
        Write-Host "  ==========================="
        Write-Host ""
        Write-Host "  .\commands.ps1 install    安装 Python 依赖"
        Write-Host "  .\commands.ps1 run        启动服务 (生产模式)"
        Write-Host "  .\commands.ps1 dev        启动服务 (开发模式，热重载)"
        Write-Host "  .\commands.ps1 open       浏览器打开 API 文档"
        Write-Host "  .\commands.ps1 db-reset   重置数据库"
        Write-Host "  .\commands.ps1 clean      清理缓存文件"
        Write-Host ""
    }
    "install" {
        pip install -r requirements.txt
    }
    "run" {
        python -m uvicorn main:app --host 127.0.0.1 --port 8000
    }
    "dev" {
        python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
    }
    "open" {
        Start-Process "http://127.0.0.1:8000/docs"
    }
    "db-reset" {
        Remove-Item -Path "data/users.db" -ErrorAction SilentlyContinue
        Write-Host "数据库已删除，重启服务后自动重建"
    }
    "clean" {
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "缓存已清理"
    }
    default {
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Write-Host "输入 .\commands.ps1 查看可用命令"
    }
}

# backend/commands.ps1
# Usage: .\commands.ps1 <command>

# Fix Chinese garbled text on Windows PowerShell
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

switch ($Command) {
    "help" {
        Write-Host ""
        Write-Host "  FreedomForge Backend Commands" -ForegroundColor Cyan
        Write-Host "  =============================="
        Write-Host ""
        Write-Host "  .\commands.ps1 install    Install Python deps"
        Write-Host "  .\commands.ps1 run        Start server (production)"
        Write-Host "  .\commands.ps1 dev        Start server (dev + hot reload)"
        Write-Host "  .\commands.ps1 open       Open API docs in browser"
        Write-Host "  .\commands.ps1 db-reset   Reset SQLite database"
        Write-Host "  .\commands.ps1 clean      Clean __pycache__"
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
        Write-Host "Database deleted. Restart server to recreate."
    }
    "clean" {
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "Cache cleaned."
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run .\commands.ps1 to see available commands"
    }
}

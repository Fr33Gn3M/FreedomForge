# backend/quant/models.py — Pydantic 数据模型
from pydantic import BaseModel, Field
from typing import Optional


# ====== 行情数据 ======

class SymbolInfo(BaseModel):
    symbol: str
    base: str
    quote: str
    price: float
    change_24h: float = 0
    volume_24h: float = 0


class KlineRequest(BaseModel):
    symbol: str = "BTC-USDT-SWAP"
    timeframe: str = "1h"       # 1m, 5m, 15m, 30m, 1h, 4h, 1d
    start: Optional[str] = None  # ISO date string
    end: Optional[str] = None
    limit: int = 100


# ====== 策略管理 ======

class StrategyInfo(BaseModel):
    id: str                     # 文件名（不含 .py）
    name: str
    description: str = ""
    params: dict = {}
    file_path: str = ""


class StrategySaveRequest(BaseModel):
    content: str                # Python 文件内容


# ====== 回测 ======

class BacktestRequest(BaseModel):
    strategy: str               # 策略 ID
    params: dict = {}           # 策略参数
    symbol: str = "BTC-USDT-SWAP"
    timeframe: str = "1h"
    start_date: str             # "2026-01-01"
    end_date: str               # "2026-06-30"
    initial_cash: float = 10000
    commission: float = 0.001


class BacktestResult(BaseModel):
    id: str
    status: str = "running"     # running | done | error
    total_return: float = 0
    annual_return: float = 0
    sharpe_ratio: float = 0
    max_drawdown: float = 0
    win_rate: float = 0
    total_trades: int = 0
    profit_factor: float = 0
    equity_curve: list = []     # [{date, value}, ...]
    trades: list = []           # [{date, action, price, pnl}, ...]


# ====== 信号 ======

class SignalData(BaseModel):
    id: Optional[str] = None
    strategy: str
    symbol: str
    action: str                 # buy | sell | hold
    price: float
    amount: float
    reason: str = ""
    status: str = "pending"     # pending | approved | rejected | executed
    created_at: Optional[str] = None


class SignalStartRequest(BaseModel):
    strategy: str
    symbol: str
    timeframe: str = "1h"
    params: dict = {}

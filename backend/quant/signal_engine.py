# backend/quant/signal_engine.py — 信号生成引擎 + 风控
import asyncio
import json
import uuid
from datetime import datetime

import pandas as pd

from .strategy_loader import StrategyLoader


class RiskManager:
    """风控规则管理器"""

    def __init__(self, config: dict | None = None):
        self.config = config or {
            "max_position_pct": 0.2,       # 单笔最大仓位 20%
            "max_daily_trades": 10,         # 每日最大交易次数
            "max_loss_pct": 0.02,           # 单笔最大亏损 2%
            "max_consecutive_losses": 3,    # 连续亏损暂停次数
            "cooldown_minutes": 60,         # 暂停时间（分钟）
        }
        self.daily_trades = 0
        self.consecutive_losses = 0
        self.last_trade_date = None
        self.cooldown_until = None

    def check(self, signal: dict, positions: list) -> bool:
        """
        检查信号是否通过风控
        返回 True = 通过, False = 拒绝
        """
        now = datetime.now()

        # 冷却期检查
        if self.cooldown_until and now < self.cooldown_until:
            return False

        # 每日重置
        today = now.date()
        if self.last_trade_date != today:
            self.daily_trades = 0
            self.last_trade_date = today

        # 每日次数限制
        if self.daily_trades >= self.config["max_daily_trades"]:
            return False

        # 连续亏损暂停
        if self.consecutive_losses >= self.config["max_consecutive_losses"]:
            self.cooldown_until = now + \
                pd.Timedelta(minutes=self.config["cooldown_minutes"]).to_pytimedelta()
            self.consecutive_losses = 0
            return False

        return True

    def record_trade(self, pnl: float):
        """记录交易结果"""
        self.daily_trades += 1
        if pnl > 0:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1


class SignalEngine:
    """实时信号引擎（简化版）"""

    def __init__(self, strategy_dir: str = "strategies"):
        self.loader = StrategyLoader(strategy_dir)
        self.risk = RiskManager()
        self.active_tasks: dict[str, asyncio.Task] = {}
        self.signal_queue: asyncio.Queue = asyncio.Queue()
        self.signal_log: list[dict] = []

    async def start(self, strategy_name: str, symbol: str,
                    timeframe: str = "1h", **params):
        """启动策略监控任务"""
        task_key = f"{strategy_name}:{symbol}"
        if task_key in self.active_tasks:
            return  # 已经在运行

        strategy_class, _ = self.loader.load_strategy(strategy_name)
        strategy = strategy_class(**params)

        async def monitor():
            while task_key in self.active_tasks:
                # 这里应该从实时数据源获取 K 线
                # 目前骨架阶段，暂用本地数据库数据
                from .market_data import MarketData
                md = MarketData()
                klines = md.get_klines(symbol, timeframe, limit=50)

                if not klines.empty:
                    signal = strategy.on_bar(klines)
                    if signal.get("action") in ("buy", "sell"):
                        signal_id = f"sig_{uuid.uuid4().hex[:8]}"
                        sig_data = {
                            "id": signal_id,
                            "strategy": strategy_name,
                            "symbol": symbol,
                            "action": signal["action"],
                            "price": signal.get("price", 0),
                            "amount": signal.get("amount", 0),
                            "reason": signal.get("reason", ""),
                            "status": "pending",
                            "created_at": datetime.now().isoformat(),
                        }
                        self.signal_log.append(sig_data)
                        await self.signal_queue.put(sig_data)

                await asyncio.sleep(60)  # 每分钟检查一次

        task = asyncio.create_task(monitor())
        self.active_tasks[task_key] = task

    async def stop(self, strategy_name: str, symbol: str):
        """停止策略监控"""
        task_key = f"{strategy_name}:{symbol}"
        if task_key in self.active_tasks:
            task = self.active_tasks.pop(task_key)
            task.cancel()

    async def signal_stream(self):
        """异步生成器，SSE 推送信号"""
        while True:
            signal = await self.signal_queue.get()
            yield f"data: {json.dumps(signal, ensure_ascii=False)}\n\n"

    def get_log(self, page: int = 1, page_size: int = 20) -> dict:
        """获取历史信号列表"""
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "total": len(self.signal_log),
            "list": self.signal_log[::-1][start:end],
        }

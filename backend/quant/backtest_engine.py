# backend/quant/backtest_engine.py — backtrader 回测引擎封装
import uuid
from datetime import datetime

import backtrader as bt
import pandas as pd

from .strategy_loader import StrategyLoader


class BacktestEngine:
    """Backtrader 回测引擎封装"""

    def __init__(self):
        self.results: dict[str, dict] = {}  # 内存中存储回测结果
        self.loader = StrategyLoader()

    def run(self, strategy_name: str, params: dict,
            klines: pd.DataFrame,
            initial_cash: float = 10000,
            commission: float = 0.001) -> str:
        """
        执行回测，返回结果 ID
        """
        bt_id = f"bt_{uuid.uuid4().hex[:8]}"
        self.results[bt_id] = {"id": bt_id, "status": "running"}

        try:
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(initial_cash)
            cerebro.broker.setcommission(commission=commission)

            # 加载 K 线数据到 backtrader
            if klines.empty:
                raise ValueError("K 线数据为空")

            data = bt.feeds.PandasData(dataname=klines)
            cerebro.adddata(data)

            # 动态加载策略
            strategy_class, _ = self.loader.load_strategy(strategy_name)

            # 创建一个适配 backtrader 的策略子类
            user_strategy = strategy_class

            class BtAdapter(bt.Strategy):
                _params = params

                def __init__(inner_self):
                    inner_self.user = user_strategy(**params)
                    inner_self.trade_log = []

                def next(inner_self):
                    # 构建当前 K 线 DataFrame
                    df = pd.DataFrame({
                        "open": [inner_self.data.open[0]],
                        "high": [inner_self.data.high[0]],
                        "low": [inner_self.data.low[0]],
                        "close": [inner_self.data.close[0]],
                        "volume": [inner_self.data.volume[0]],
                    })
                    signal = inner_self.user.on_bar(df)
                    if signal.get("action") == "buy":
                        inner_self.buy(size=signal.get("amount", 1))
                    elif signal.get("action") == "sell":
                        inner_self.sell(size=signal.get("amount", 1))

                def notify_trade(inner_self, trade):
                    if trade.isclosed:
                        inner_self.trade_log.append({
                            "date": inner_self.data.datetime.datetime().isoformat(),
                            "action": "buy" if trade.size > 0 else "sell",
                            "price": trade.price,
                            "pnl": trade.pnl,
                            "pnl_comm": trade.pnlcomm,
                        })

            cerebro.addstrategy(BtAdapter)

            start_value = cerebro.broker.getvalue()
            result = cerebro.run()
            end_value = cerebro.broker.getvalue()

            # 提取回测指标
            total_return = (end_value / start_value - 1) if start_value > 0 else 0
            trades = []
            for r in result:
                if hasattr(r, "trade_log"):
                    trades = r.trade_log

            # 简单计算指标
            wins = [t for t in trades if t["pnl"] > 0]
            win_rate = len(wins) / len(trades) if trades else 0

            # 权益曲线（简化：用每次交易后的值）
            equity = [{"date": klines.index[0].isoformat() if hasattr(klines.index[0], 'isoformat') else str(klines.index[0]),
                       "value": start_value}]

            total_profit = sum(t["pnl"] for t in trades)
            total_loss = abs(sum(t["pnl"] for t in trades if t["pnl"] < 0)) or 1
            profit_factor = total_profit / total_loss if total_loss else 0

            # 最大回撤（简化）
            peak = start_value
            max_dd = 0.0
            running = start_value + sum(t["pnl"] for t in trades)
            # 粗略估计
            for t in trades:
                running = start_value + sum(x["pnl"] for x in trades[:trades.index(t) + 1])
                peak = max(peak, running)
                dd = (peak - running) / peak if peak > 0 else 0
                max_dd = max(max_dd, dd)

            self.results[bt_id] = {
                "id": bt_id,
                "status": "done",
                "total_return": round(total_return, 4),
                "annual_return": 0,  # TODO: 按实际天数计算
                "sharpe_ratio": 0,    # TODO: 实现夏普比率计算
                "max_drawdown": round(max_dd, 4),
                "win_rate": round(win_rate, 4),
                "total_trades": len(trades),
                "profit_factor": round(profit_factor, 2),
                "equity_curve": equity,
                "trades": trades,
            }
        except Exception as e:
            self.results[bt_id] = {"id": bt_id, "status": "error", "error": str(e)}

        return bt_id

    def get_result(self, bt_id: str) -> dict | None:
        """获取回测结果"""
        return self.results.get(bt_id)

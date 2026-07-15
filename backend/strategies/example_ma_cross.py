"""
策略名: 双均线交叉
描述: 快线上穿慢线买入（金叉），下穿卖出（死叉）
参数:
  - fast_period: 快线周期 (默认 5)
  - slow_period: 慢线周期 (默认 20)
  - stop_loss_pct: 止损比例 (默认 0.05)
"""

import pandas as pd


class StrategyConfig:
    name = "双均线交叉"
    description = "快线上穿慢线买入（金叉），下穿卖出（死叉）"
    params = {
        "fast_period": {
            "type": "int", "default": 5, "min": 2, "max": 200,
            "label": "快线周期",
        },
        "slow_period": {
            "type": "int", "default": 20, "min": 5, "max": 500,
            "label": "慢线周期",
        },
        "stop_loss_pct": {
            "type": "float", "default": 0.05, "min": 0.01, "max": 0.5,
            "label": "止损比例",
        },
    }


class Strategy:
    """双均线交叉策略"""

    def __init__(self, fast_period: int = 5, slow_period: int = 20,
                 stop_loss_pct: float = 0.05):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_loss_pct = stop_loss_pct
        self.last_entry_price = 0

    def on_bar(self, klines: pd.DataFrame) -> dict:
        """
        每根 K 线调用一次

        参数:
            klines: DataFrame，列 [open, high, low, close, volume]
                    index 为时间戳

        返回:
            {"action": "buy"|"sell"|"hold", "price": float, "amount": float, "reason": str}
        """
        if len(klines) < self.slow_period + 1:
            return {"action": "hold", "price": 0, "amount": 0, "reason": "数据不足"}

        close = klines["close"]
        fast_ma = close.rolling(self.fast_period).mean()
        slow_ma = close.rolling(self.slow_period).mean()

        current_price = close.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]
        curr_fast = fast_ma.iloc[-1]
        curr_slow = slow_ma.iloc[-1]

        # 止损逻辑：如果持有多仓且价格跌破入场价 * (1 - stop_loss_pct)
        if self.last_entry_price > 0 and current_price < self.last_entry_price * (1 - self.stop_loss_pct):
            self.last_entry_price = 0
            return {"action": "sell", "price": current_price, "amount": 1,
                    "reason": f"止损触发（-{self.stop_loss_pct * 100:.1f}%）"}

        # 金叉：快线上穿慢线
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            self.last_entry_price = current_price
            return {"action": "buy", "price": current_price, "amount": 1,
                    "reason": f"金叉（MA{self.fast_period} ↑ MA{self.slow_period}）"}

        # 死叉：快线下穿慢线
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            self.last_entry_price = 0
            return {"action": "sell", "price": current_price, "amount": 1,
                    "reason": f"死叉（MA{self.fast_period} ↓ MA{self.slow_period}）"}

        return {"action": "hold", "price": 0, "amount": 0, "reason": ""}

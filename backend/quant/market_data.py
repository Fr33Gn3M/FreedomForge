# backend/quant/market_data.py — 行情数据拉取与本地存储
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


class MarketData:
    """行情数据管理器"""

    def __init__(self, db_path: str = "data/market.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS klines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL, high REAL, low REAL, close REAL, volume REAL,
                UNIQUE(symbol, timeframe, timestamp)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_klines_symbol_time "
                     "ON klines(symbol, timeframe, timestamp)")
        conn.commit()
        conn.close()

    def save_klines(self, symbol: str, timeframe: str, rows: list[dict]):
        """保存 K 线数据（去重）"""
        if not rows:
            return
        conn = sqlite3.connect(self.db_path)
        for row in rows:
            ts = int(row.get("timestamp", row.get("ts", 0)))
            if ts > 1_000_000_000_000:
                ts //= 1000
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO klines (symbol, timeframe, timestamp, open, high, low, close, volume) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (
                        symbol, timeframe, ts,
                        float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"]),
                        float(row["volume"]),
                    ),
                )
            except (KeyError, ValueError):
                continue
        conn.commit()
        conn.close()

    def get_klines(self, symbol: str, timeframe: str = "1h",
                   start: Optional[str] = None, end: Optional[str] = None,
                   limit: int = 500) -> pd.DataFrame:
        """从本地数据库读取 K 线，返回 DataFrame"""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT timestamp, open, high, low, close, volume FROM klines WHERE symbol=? AND timeframe=?"
        params = [symbol, timeframe]

        if start:
            start_ts = int(pd.Timestamp(start).timestamp())
            query += " AND timestamp >= ?"
            params.append(start_ts)
        if end:
            end_ts = int(pd.Timestamp(end).timestamp())
            query += " AND timestamp <= ?"
            params.append(end_ts)

        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df.set_index("timestamp", inplace=True)
        return df

    def get_symbols(self) -> list[dict]:
        """返回本地已缓存的交易对列表（唯一值）"""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT DISTINCT symbol FROM klines ORDER BY symbol"
        ).fetchall()
        conn.close()
        return [{"symbol": r[0]} for r in rows]

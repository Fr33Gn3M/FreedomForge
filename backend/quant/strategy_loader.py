# backend/quant/strategy_loader.py — 策略动态加载器
import importlib
import inspect
import re
import sys
from pathlib import Path
from typing import Any


class StrategyLoader:
    """动态加载 strategies/ 目录下的 Python 策略文件"""

    def __init__(self, strategy_dir: str = "strategies"):
        self.dir = Path(strategy_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        # 确保目录在 sys.path 中（用于 import）
        if str(self.dir.parent) not in sys.path:
            sys.path.insert(0, str(self.dir.parent))

    def list_strategies(self) -> list[dict]:
        """列出所有策略文件及其元信息"""
        strategies = []
        for f in sorted(self.dir.glob("*.py")):
            if f.name.startswith("_"):
                continue
            info = self._parse_file_info(f)
            strategies.append(info)
        return strategies

    def get_strategy_content(self, name: str) -> str:
        """读取策略文件原始内容"""
        filepath = self.dir / f"{name}.py"
        if not filepath.exists():
            return ""
        return filepath.read_text(encoding="utf-8")

    def save_strategy(self, name: str, content: str):
        """保存（新建或覆盖）策略文件"""
        filepath = self.dir / f"{name}.py"
        filepath.write_text(content, encoding="utf-8")

    def load_strategy(self, name: str) -> tuple[Any, Any]:
        """动态加载策略模块，返回 (Strategy类, StrategyConfig类)"""
        # 移除旧缓存
        module_key = f"strategies.{name}"
        if module_key in sys.modules:
            del sys.modules[module_key]

        module = importlib.import_module(f"strategies.{name}")
        strategy_class = getattr(module, "Strategy", None)
        config_class = getattr(module, "StrategyConfig", None)

        if strategy_class is None:
            raise ValueError(f"策略文件 {name}.py 中未找到 Strategy 类")

        return strategy_class, config_class

    def _parse_file_info(self, filepath: Path) -> dict:
        """读取策略文件头部注释，提取元信息"""
        content = filepath.read_text(encoding="utf-8")
        name = filepath.stem
        description = ""
        params = {}

        # 解析 docstring 头部注释
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("策略名"):
                name = line.split(":")[-1].strip()
            elif line.startswith("描述"):
                description = line.split(":")[-1].strip()
            elif line.startswith("参数") or line.startswith("-"):
                # 尝试从注释中提取参数信息（简化处理）
                pass

        # 尝试导入获取更精确的 Config
        try:
            _, config_class = self.load_strategy(filepath.stem)
            if config_class:
                name = getattr(config_class, "name", name)
                description = getattr(config_class, "description", description)
                params = getattr(config_class, "params", {})
        except Exception:
            pass

        return {
            "id": filepath.stem,
            "name": name,
            "description": description,
            "params": params,
            "file_path": str(filepath),
        }

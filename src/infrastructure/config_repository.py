import json
from decimal import Decimal
from pathlib import Path

_DEFAULT_TAX_RATE = "0.20315"


class ConfigRepository:
    def __init__(self, config_path: str = "config.json"):
        self._path = Path(config_path)

    def get_tax_rate(self) -> Decimal:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            return Decimal(str(data.get("capital_gains_tax_rate", _DEFAULT_TAX_RATE)))
        return Decimal(_DEFAULT_TAX_RATE)

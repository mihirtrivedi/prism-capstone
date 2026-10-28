"""Configuration loader for Prism Gateway.
Loads data/gateway_config.sample.json, data/model_pricing.json, and data/seed_keys.json.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Root directory of prism-capstone
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class Config:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.gateway_config: Dict[str, Any] = {}
        self.model_pricing: Dict[str, Dict[str, float]] = {}
        self.seed_keys: Dict[str, Any] = {}
        self.providers: Dict[str, Dict[str, str]] = {}
        self.aliases: Dict[str, Any] = {}
        self.retry_config: Dict[str, Any] = {}
        self.load()

    def load(self):
        with open(self.data_dir / "gateway_config.sample.json", "r", encoding="utf-8") as f:
            self.gateway_config = json.load(f)

        with open(self.data_dir / "model_pricing.json", "r", encoding="utf-8") as f:
            self.model_pricing = json.load(f)

        with open(self.data_dir / "seed_keys.json", "r", encoding="utf-8") as f:
            self.seed_keys = json.load(f)

        # Index providers by name
        self.providers = {p["name"]: p for p in self.gateway_config.get("providers", [])}

        # Index model aliases
        self.aliases = self.gateway_config.get("model_aliases", {})

        # Retry settings
        self.retry_config = self.gateway_config.get("retry", {
            "max_attempts": 3,
            "initial_backoff_ms": 200,
            "backoff_multiplier": 2
        })

    def get_pricing(self, model: str) -> Optional[Dict[str, float]]:
        return self.model_pricing.get(model)

    def get_provider(self, name: str) -> Optional[Dict[str, str]]:
        return self.providers.get(name)

    def get_alias_chain(self, alias_or_model: str) -> List[str]:
        """Resolves alias or model name to an ordered chain of provider models."""
        if alias_or_model in self.aliases:
            route = self.aliases[alias_or_model]
            if "primary" in route:
                return [route["primary"]] + list(route.get("fallbacks", []))
        # If it's directly a model name:
        return [alias_or_model]


config = Config()


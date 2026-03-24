"""Keitaro Instance Registry.

Manages multiple Keitaro tracker instances.
Supports loading from environment variables (single instance)
or JSON config file (multiple instances).

Single instance config (env vars):
    KEITARO_URL=https://tracker.example.com
    KEITARO_API_KEY=your-api-key

Multiple instances config (JSON file at KEITARO_CONFIG_FILE):
    [
        {"name": "prod", "url": "https://prod.tracker.com", "api_key": "key1", "description": "Production"},
        {"name": "test", "url": "https://test.tracker.com", "api_key": "key2", "description": "Testing"}
    ]
"""

import json
import os

from keitaro_mcp.client import KeitaroClient


class InstanceRegistry:
    """Registry of multiple Keitaro tracker instances."""

    def __init__(self):
        self._instances: dict[str, KeitaroClient] = {}
        self._metadata: dict[str, dict] = {}

    def register(
        self,
        name: str,
        base_url: str,
        api_key: str,
        description: str = "",
        timeout: int = 30,
    ) -> KeitaroClient:
        """Register a Keitaro tracker instance."""
        client = KeitaroClient(base_url, api_key, timeout)
        self._instances[name] = client
        self._metadata[name] = {
            "name": name,
            "url": base_url,
            "description": description,
        }
        return client

    def get(self, name: str) -> KeitaroClient:
        """Get client by instance name."""
        if name not in self._instances:
            raise KeyError(
                f"Instance '{name}' not registered. Available: {list(self._instances.keys())}"
            )
        return self._instances[name]

    def resolve(self, args: dict) -> KeitaroClient:
        """Resolve client from tool arguments. Auto-selects if only one registered."""
        name = args.get("instance")
        if not name:
            names = list(self._instances.keys())
            if len(names) == 1:
                return self._instances[names[0]]
            if len(names) == 0:
                raise ValueError(
                    "No Keitaro instances configured. "
                    "Set KEITARO_URL + KEITARO_API_KEY env vars, "
                    "or KEITARO_CONFIG_FILE pointing to a JSON config."
                )
            raise ValueError(
                f"Multiple instances registered. Specify 'instance': {names}"
            )
        return self.get(name)

    def list_names(self) -> list[str]:
        return list(self._instances.keys())

    def list_all(self) -> list[dict]:
        return list(self._metadata.values())

    def load_from_env(self) -> int:
        """Load single instance from KEITARO_URL + KEITARO_API_KEY env vars.

        Returns count loaded (0 or 1).
        """
        url = os.environ.get("KEITARO_URL", "")
        api_key = os.environ.get("KEITARO_API_KEY", "")
        if not url or not api_key:
            return 0
        name = os.environ.get("KEITARO_INSTANCE_NAME", "default")
        description = os.environ.get("KEITARO_DESCRIPTION", "")
        self.register(name, url, api_key, description)
        return 1

    def load_from_file(self, path: str) -> int:
        """Load instances from JSON config file. Returns count loaded."""
        try:
            with open(path) as f:
                instances = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Config file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {path}: {e}")

        if not isinstance(instances, list):
            raise ValueError(f"Config file must contain a JSON array, got {type(instances).__name__}")

        for i, inst in enumerate(instances):
            for key in ("name", "url", "api_key"):
                if key not in inst:
                    raise ValueError(f"Instance #{i} missing required field '{key}' in {path}")
            self.register(
                name=inst["name"],
                base_url=inst["url"],
                api_key=inst["api_key"],
                description=inst.get("description", ""),
                timeout=inst.get("timeout", 30),
            )
        return len(instances)

# === Standard Library Imports ===
from typing import Dict, Any, Optional

# === Local Imports ===
from .interfaces import IPluginLoader, IPlugin, IPluginRegistry

class PluginLoader(IPluginLoader):
    """플러그인 로더 구현"""

    def __init__(self, registry: IPluginRegistry):
        self.registry = registry
        self.loaded_plugins: Dict[str, IPlugin] = {}

    def load_plugin(self, plugin_type: str) -> Optional[IPlugin]:
        """플러그인 로드"""
        if plugin_type in self.loaded_plugins:
            return self.loaded_plugins[plugin_type]

        factory = self.registry.get_factory(plugin_type)
        if not factory:
            return None

        # 설정을 포함한 플러그인 생성
        config = {'enabled': True, 'priority': 1}  # 기본 설정
        plugin = factory.create_plugin(plugin_type, config)
        if plugin:
            self.loaded_plugins[plugin_type] = plugin
        return plugin

    def unload_plugin(self, plugin_type: str) -> bool:
        """플러그인 언로드"""
        if plugin_type not in self.loaded_plugins:
            return False

        plugin = self.loaded_plugins[plugin_type]
        try:
            plugin.shutdown()
            del self.loaded_plugins[plugin_type]
            return True
        except Exception:
            return False

    def get_loaded_plugins(self) -> Dict[str, IPlugin]:
        """로드된 플러그인 목록"""
        return self.loaded_plugins.copy()

    def is_loaded(self, plugin_type: str) -> bool:
        """플러그인 로드 상태 확인"""
        return plugin_type in self.loaded_plugins
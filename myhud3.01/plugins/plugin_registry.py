# === Standard Library Imports ===
from typing import Dict, List

# === Local Imports ===
from .interfaces import IPluginRegistry, IPluginFactory

class PluginRegistry(IPluginRegistry):
    """플러그인 레지스트리 구현"""

    def __init__(self):
        self._factories: Dict[str, IPluginFactory] = {}

    def register_plugin(self, plugin_type: str, factory: IPluginFactory) -> bool:
        """플러그인 등록"""
        if not isinstance(factory, IPluginFactory):
            return False
        self._factories[plugin_type] = factory
        return True

    def unregister_plugin(self, plugin_type: str) -> bool:
        """플러그인 등록 해제"""
        if plugin_type in self._factories:
            del self._factories[plugin_type]
            return True
        return False

    def get_factory(self, plugin_type: str) -> IPluginFactory:
        """팩토리 조회"""
        return self._factories.get(plugin_type)

    def get_plugin_types(self) -> List[str]:
        """등록된 플러그인 타입 목록"""
        return list(self._factories.keys())

    def has_plugin(self, plugin_type: str) -> bool:
        """플러그인 존재 확인"""
        return plugin_type in self._factories

    def clear(self):
        """모든 등록 해제"""
        self._factories.clear()
# === Standard Library Imports ===
from typing import Dict, Any, Optional, Type

# === Local Imports ===
from .interfaces import IPluginFactory, IPlugin

class PluginFactory(IPluginFactory):
    """플러그인 팩토리 구현"""

    def __init__(self):
        self._plugin_classes: Dict[str, Type[IPlugin]] = {}

    def register_plugin_class(self, plugin_type: str, plugin_class: Type[IPlugin]) -> None:
        """플러그인 클래스 등록"""
        self._plugin_classes[plugin_type] = plugin_class

    def create_plugin(self, plugin_type: str, config: Dict[str, Any]) -> Optional[IPlugin]:
        """플러그인 인스턴스 생성"""
        # 입력 유효성 검사
        if not isinstance(plugin_type, str) or not plugin_type.strip():
            return None
        if not isinstance(config, dict):
            return None

        if plugin_type not in self._plugin_classes:
            return None

        plugin_class = self._plugin_classes[plugin_type]
        plugin = plugin_class()

        if plugin.initialize(config):
            return plugin

        return None

    def get_registered_types(self) -> list[str]:
        """등록된 플러그인 타입 목록"""
        return list(self._plugin_classes.keys())
# === Standard Library Imports ===
from typing import Dict, Any

# === Local Imports ===
from .interfaces import IPluginLifecycleManager, IPlugin, IPluginLoader

class PluginLifecycleManager(IPluginLifecycleManager):
    """플러그인 생명주기 관리자 구현"""

    def __init__(self, loader: IPluginLoader):
        self.loader = loader
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.active_plugins: Dict[str, IPlugin] = {}

    def initialize_plugins(self, configs: Dict[str, Dict[str, Any]]) -> bool:
        """플러그인 초기화"""
        # 입력 유효성 검사
        if not isinstance(configs, dict):
            return False
        if not all(isinstance(k, str) and isinstance(v, dict) for k, v in configs.items()):
            return False

        self.plugin_configs = configs.copy()
        return True

    def start_plugins(self) -> bool:
        """플러그인 시작"""
        try:
            for plugin_type, config in self.plugin_configs.items():
                plugin = self.loader.load_plugin(plugin_type)
                if plugin:
                    # 동기 start 호출
                    if plugin.start():
                        self.active_plugins[plugin_type] = plugin
                    else:
                        # 실패 시 롤백
                        self._rollback_started_plugins()
                        return False
                else:
                    # 실패 시 롤백
                    self._rollback_started_plugins()
                    return False
            return True
        except Exception:
            self._rollback_started_plugins()
            return False

    def stop_plugins(self) -> bool:
        """플러그인 중지"""
        try:
            for plugin in self.active_plugins.values():
                plugin.stop()
            self.active_plugins.clear()
            return True
        except Exception:
            return False

    def shutdown_plugins(self) -> bool:
        """플러그인 종료"""
        try:
            self.stop_plugins()
            for plugin_type in list(self.active_plugins.keys()):
                self.loader.unload_plugin(plugin_type)
            self.plugin_configs.clear()
            return True
        except Exception:
            return False

    def add_plugin_config(self, plugin_type: str, config: Dict[str, Any]) -> bool:
        """플러그인 설정 추가"""
        self.plugin_configs[plugin_type] = config
        return True

    def remove_plugin_config(self, plugin_type: str) -> bool:
        """플러그인 설정 제거"""
        if plugin_type in self.plugin_configs:
            del self.plugin_configs[plugin_type]
            return True
        return False

    def get_active_plugins(self) -> Dict[str, IPlugin]:
        """활성 플러그인 목록"""
        return self.active_plugins.copy()

    def is_plugin_active(self, plugin_type: str) -> bool:
        """플러그인 활성 상태 확인"""
        return plugin_type in self.active_plugins

    def _rollback_started_plugins(self):
        """시작된 플러그인 롤백"""
        for plugin in self.active_plugins.values():
            try:
                plugin.stop()
            except Exception:
                pass
        self.active_plugins.clear()
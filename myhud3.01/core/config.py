# === Standard Library Imports ===
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

# === Constants ===
SCRIPT_DIR = Path(__file__).parent
DB_FILE = SCRIPT_DIR / "player_data.json"
POS_FILE = SCRIPT_DIR / "hud_positions.json"
CONFIG_FILE = SCRIPT_DIR / "hud_config.json"

# === Default Configuration ===
DEFAULT_CONFIG: Dict[str, Any] = {
    # 기존 HUD 설정
    'scan_interval_ms': 20000,
    'use_gpu': False,
    'enable_logging': True,
    'hud_width': 120,
    'hud_height': 119,
    'auto_save_interval': 300000,
    'max_memo_lines': 3,
    'theme': 'dark',
    'shortcuts': {
        'fish': '1',
        'tag': '2',
        'nit': '3',
        'lag': '4',
        'maniac': '5',
        'weird': '6',
        'unknown': '7',
        'toggle_move': 'L',
        'range': 'R',
        'toggle_scan': 'Space'
    },

    # OBS 아키텍처 설정
    'plugin_dir': 'plugins',
    'cache_enabled': True,
    'data_dir': 'data',
    'plugins': {
        'hud_plugin': {
            'enabled': True,
            'priority': 1
        },
        'ocr_plugin': {
            'enabled': True,
            'priority': 2,
            'scan_interval': 1.0
        },
        'data_store_plugin': {
            'enabled': True,
            'priority': 3,
            'auto_save': True
        }
    },

    # 데이터 플로우 설정
    'data_flow': {
        'routes': {
            'ocr_scanner': ['hud_display', 'data_store'],
            'hud_display': ['data_store'],
            'player_hud': ['data_store']
        },
        'cache_size_limit': 1000,
        'event_buffer_size': 100
    },

    # 시스템 설정
    'system': {
        'log_level': 'INFO',
        'max_threads': 4,
        'shutdown_timeout': 10
    }
}

# 전역 설정 인스턴스
CONFIG = DEFAULT_CONFIG.copy()

class ConfigManager:
    """중앙 집중식 설정 관리자"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = DEFAULT_CONFIG.copy()
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config_file = Path(CONFIG_FILE)
            self._config = self.load_config()

    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스 반환"""
        return cls()

    def load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                    # 기본 설정과 파일 설정 병합
                    merged_config = self._deep_merge(DEFAULT_CONFIG.copy(), file_config)
                    logging.info(f"Config loaded from {self._config_file}")
                    return merged_config
            else:
                logging.info(f"Config file not found, using defaults")
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return DEFAULT_CONFIG.copy()

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """설정 저장"""
        try:
            if config is None:
                config = self._config

            # JSON 직렬화 검증
            json.dumps(config, ensure_ascii=False)

            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            logging.info(f"Config saved to {self._config_file}")
            return True

        except Exception as e:
            logging.error(f"Failed to save config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 조회"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """설정 값 변경"""
        try:
            self._config[key] = value
            return True
        except Exception as e:
            logging.error(f"Failed to set config {key}: {e}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """설정 섹션 조회"""
        return self._config.get(section, {})

    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """설정 섹션 업데이트"""
        try:
            if section not in self._config:
                self._config[section] = {}
            self._config[section].update(values)
            return True
        except Exception as e:
            logging.error(f"Failed to update section {section}: {e}")
            return False

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """플러그인 설정 조회"""
        plugins = self._config.get('plugins', {})
        return plugins.get(plugin_name, {})

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """플러그인 활성화 상태 확인"""
        plugin_config = self.get_plugin_config(plugin_name)
        return plugin_config.get('enabled', False)

    def get_data_flow_config(self) -> Dict[str, Any]:
        """데이터 플로우 설정 조회"""
        return self._config.get('data_flow', {})

    def get_system_config(self) -> Dict[str, Any]:
        """시스템 설정 조회"""
        return self._config.get('system', {})

    def reload_config(self) -> bool:
        """설정 다시 로드"""
        try:
            self._config = self.load_config()
            logging.info("Config reloaded")
            return True
        except Exception as e:
            logging.error(f"Failed to reload config: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """기본 설정으로 리셋"""
        try:
            self._config = DEFAULT_CONFIG.copy()
            logging.info("Config reset to defaults")
            return True
        except Exception as e:
            logging.error(f"Failed to reset config: {e}")
            return False

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """깊은 병합 (재귀적으로 딕셔너리 병합)"""
        result = base.copy()

        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_all_config(self) -> Dict[str, Any]:
        """전체 설정 조회"""
        return self._config.copy()

# 전역 설정 관리자 인스턴스
config_manager = ConfigManager()

# 하위 호환성을 위한 CONFIG 변수
CONFIG = config_manager.get_all_config()

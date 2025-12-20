# === Standard Library Imports ===
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import threading

# === Local Imports ===
from interfaces import IPlugin

class ConfigManager(IPlugin):
    """설정 관리자"""

    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_file: Optional[Path] = None
        self.lock = threading.RLock()
        self.is_running = False

    def get_name(self) -> str:
        return "Config Manager"

    def get_version(self) -> str:
        return "1.0.0"

    def get_description(self) -> str:
        return "중앙 집중식 설정 관리 시스템"

    def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            # 설정 파일 경로 설정
            config_dir = config.get('config_dir', '.')
            config_filename = config.get('config_filename', 'config.json')
            self.config_file = Path(config_dir) / config_filename

            # 기본 설정 로드
            self._load_default_config()

            # 파일에서 설정 로드
            if self.config_file.exists():
                self._load_from_file()

            # 초기화 시 제공된 설정으로 업데이트
            self.update_config(config)

            print(f"{self.get_name()} initialized")
            return True
        except Exception as e:
            print(f"Failed to initialize {self.get_name()}: {e}")
            return False

    def start(self) -> bool:
        try:
            self.is_running = True
            print(f"{self.get_name()} started")
            return True
        except Exception as e:
            print(f"Failed to start {self.get_name()}: {e}")
            return False

    def stop(self) -> bool:
        try:
            self.is_running = False
            # 설정 저장
            self.save_config()
            print(f"{self.get_name()} stopped")
            return True
        except Exception as e:
            print(f"Failed to stop {self.get_name()}: {e}")
            return False

    def shutdown(self) -> bool:
        try:
            self.stop()
            self.config.clear()
            print(f"{self.get_name()} shutdown")
            return True
        except Exception as e:
            print(f"Failed to shutdown {self.get_name()}: {e}")
            return False

    def is_active(self) -> bool:
        return self.is_running

    def get_config(self, key: Optional[str] = None) -> Any:
        """설정 값 조회"""
        with self.lock:
            if key is None:
                return self.config.copy()
            return self._get_nested_value(self.config, key.split('.'))

    def set_config(self, key: str, value: Any) -> bool:
        """설정 값 설정"""
        try:
            with self.lock:
                self._set_nested_value(self.config, key.split('.'), value)
                return True
        except Exception as e:
            print(f"Failed to set config {key}: {e}")
            return False

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """설정 일괄 업데이트"""
        try:
            with self.lock:
                self._deep_update(self.config, updates)
                return True
        except Exception as e:
            print(f"Failed to update config: {e}")
            return False

    def save_config(self) -> bool:
        """설정 파일에 저장"""
        try:
            with self.lock:
                if self.config_file:
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                    print(f"Config saved to {self.config_file}")
                    return True
                return False
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False

    def load_config(self) -> bool:
        """설정 파일에서 로드"""
        try:
            with self.lock:
                return self._load_from_file()
        except Exception as e:
            print(f"Failed to load config: {e}")
            return False

    def reset_config(self) -> bool:
        """기본 설정으로 리셋"""
        try:
            with self.lock:
                self._load_default_config()
                return True
        except Exception as e:
            print(f"Failed to reset config: {e}")
            return False

    def get_config_schema(self) -> Dict[str, Any]:
        """설정 스키마 반환"""
        return {
            "type": "object",
            "properties": {
                "app": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "debug": {"type": "boolean"}
                    }
                },
                "plugins": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "config": {"type": "object"}
                            }
                        }
                    }
                },
                "data_flow": {
                    "type": "object",
                    "properties": {
                        "cache_enabled": {"type": "boolean"},
                        "max_cache_size": {"type": "integer"}
                    }
                },
                "hud": {
                    "type": "object",
                    "properties": {
                        "width": {"type": "integer"},
                        "height": {"type": "integer"},
                        "opacity": {"type": "number"}
                    }
                },
                "ocr": {
                    "type": "object",
                    "properties": {
                        "scan_interval": {"type": "integer"},
                        "max_retries": {"type": "integer"}
                    }
                }
            }
        }

    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """설정 유효성 검증"""
        try:
            if config is None:
                config = self.config

            # 기본적인 유효성 검사
            if not isinstance(config, dict):
                return False

            # 필수 필드 검사
            required_sections = ['app', 'plugins', 'data_flow']
            for section in required_sections:
                if section not in config:
                    print(f"Missing required config section: {section}")
                    return False

            return True
        except Exception as e:
            print(f"Config validation error: {e}")
            return False

    def _load_default_config(self):
        """기본 설정 로드"""
        self.config = {
            "app": {
                "name": "Poker HUD",
                "version": "3.01",
                "debug": False
            },
            "plugins": {
                "player_hud_plugin": {
                    "enabled": True,
                    "config": {
                        "hud_width": 120,
                        "hud_height": 123
                    }
                },
                "ocr_plugin": {
                    "enabled": True,
                    "config": {
                        "scan_interval": 1000,
                        "max_retries": 3
                    }
                },
                "hud_plugin": {
                    "enabled": True,
                    "config": {}
                },
                "data_store_plugin": {
                    "enabled": True,
                    "config": {
                        "data_dir": "data"
                    }
                }
            },
            "data_flow": {
                "cache_enabled": True,
                "max_cache_size": 1000
            },
            "hud": {
                "width": 120,
                "height": 123,
                "opacity": 1.0,
                "theme": "default"
            },
            "ocr": {
                "scan_interval": 1000,
                "max_retries": 3,
                "retry_delay": 500
            },
            "data_store": {
                "data_dir": "data",
                "backup_enabled": True,
                "max_backups": 10
            }
        }

    def _load_from_file(self) -> bool:
        """파일에서 설정 로드"""
        try:
            if self.config_file and self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)

                # 파일 설정을 기본 설정에 병합
                self._deep_update(self.config, file_config)
                print(f"Config loaded from {self.config_file}")
                return True
            return False
        except Exception as e:
            print(f"Failed to load config from file: {e}")
            return False

    def _get_nested_value(self, data: Dict[str, Any], keys: list) -> Any:
        """중첩된 설정 값 조회"""
        try:
            for key in keys:
                if isinstance(data, dict):
                    data = data[key]
                else:
                    return None
            return data
        except (KeyError, TypeError):
            return None

    def _set_nested_value(self, data: Dict[str, Any], keys: list, value: Any):
        """중첩된 설정 값 설정"""
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]
        data[keys[-1]] = value

    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]):
        """깊은 병합 업데이트"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
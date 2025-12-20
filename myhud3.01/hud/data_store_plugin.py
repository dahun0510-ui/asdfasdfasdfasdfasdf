# === Standard Library Imports ===
from typing import Dict, Any, Optional
import json
import logging
import os
from pathlib import Path
import threading

# === Local Imports ===
from interfaces import IPlugin
from data_flow_manager import DataFlowManager
from config import DB_FILE, POS_FILE, CONFIG_FILE, DEFAULT_CONFIG

class DataStorePlugin(IPlugin):
    """데이터 저장소 플러그인 구현"""

    def __init__(self):
        self.name = "Data Store Plugin"
        self.version = "1.0.0"
        self.description = "데이터 저장소 플러그인"
        self.is_running = False
        self.data_flow_manager: Optional[DataFlowManager] = None

        # 데이터 저장소
        self.player_data: Dict[str, Any] = {}
        self.hud_positions: Dict[str, Any] = {}
        self.config_data: Dict[str, Any] = DEFAULT_CONFIG.copy()

        # 스레드 안전성
        self._lock = threading.RLock()
        self._auto_save_timer = None

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def get_description(self) -> str:
        return self.description

    def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            self.data_flow_manager = config.get('data_flow_manager')
            if not self.data_flow_manager:
                logging.error("DataFlowManager not provided in config")
                return False

            # 데이터 파일 로드
            self._load_all_data()

            # 이벤트 구독
            event_bus = self.data_flow_manager.get_event_bus()
            event_bus.subscribe("player_data_update", self._on_player_data_update)
            event_bus.subscribe("config_changed", self._on_config_changed)
            event_bus.subscribe("hud_update", self._on_hud_update)

            logging.info(f"{self.get_name()} initialized")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize {self.get_name()}: {e}")
            return False

    def start(self) -> bool:
        try:
            self.is_running = True

            # 자동 저장 타이머 설정 (5분마다)
            auto_save_interval = self.config_data.get('auto_save_interval', 300000)  # ms
            if auto_save_interval > 0:
                from PyQt6.QtCore import QTimer
                self._auto_save_timer = QTimer()
                self._auto_save_timer.timeout.connect(self._auto_save)
                self._auto_save_timer.start(auto_save_interval)

            logging.info(f"{self.get_name()} started")
            return True
        except Exception as e:
            logging.error(f"Failed to start {self.get_name()}: {e}")
            return False

    def stop(self) -> bool:
        try:
            self.is_running = False

            # 자동 저장 타이머 중지
            if self._auto_save_timer:
                self._auto_save_timer.stop()
                self._auto_save_timer = None

            # 최종 저장
            self._save_all_data()

            logging.info(f"{self.get_name()} stopped")
            return True
        except Exception as e:
            logging.error(f"Failed to stop {self.get_name()}: {e}")
            return False

    def shutdown(self) -> bool:
        try:
            self.stop()
            self.data_flow_manager = None
            logging.info(f"{self.get_name()} shutdown")
            return True
        except Exception as e:
            logging.error(f"Failed to shutdown {self.get_name()}: {e}")
            return False

    def is_active(self) -> bool:
        return self.is_running

    def save_player_data(self, player_id: str, data: Dict[str, Any]) -> bool:
        """플레이어 데이터 저장"""
        try:
            with self._lock:
                self.player_data[player_id] = data
                self._save_player_data()
            logging.info(f"Saved player data for {player_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to save player data for {player_id}: {e}")
            return False

    def load_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """플레이어 데이터 로드"""
        with self._lock:
            return self.player_data.get(player_id)

    def save_hud_positions(self, positions: Dict[str, Any]) -> bool:
        """HUD 위치 저장"""
        try:
            with self._lock:
                self.hud_positions.update(positions)
                self._save_hud_positions()
            logging.info("Saved HUD positions")
            return True
        except Exception as e:
            logging.error(f"Failed to save HUD positions: {e}")
            return False

    def load_hud_positions(self) -> Dict[str, Any]:
        """HUD 위치 로드"""
        with self._lock:
            return self.hud_positions.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """설정 저장"""
        try:
            with self._lock:
                self.config_data.update(config)
                self._save_config()
            logging.info("Saved configuration")
            return True
        except Exception as e:
            logging.error(f"Failed to save configuration: {e}")
            return False

    def load_config(self) -> Dict[str, Any]:
        """설정 로드"""
        with self._lock:
            return self.config_data.copy()

    def get_all_player_data(self) -> Dict[str, Any]:
        """모든 플레이어 데이터 반환"""
        with self._lock:
            return self.player_data.copy()

    def clear_player_data(self, player_id: Optional[str] = None) -> bool:
        """플레이어 데이터 클리어"""
        try:
            with self._lock:
                if player_id:
                    self.player_data.pop(player_id, None)
                else:
                    self.player_data.clear()
                self._save_player_data()
            logging.info(f"Cleared player data{' for ' + player_id if player_id else ''}")
            return True
        except Exception as e:
            logging.error(f"Failed to clear player data: {e}")
            return False

    def _load_all_data(self):
        """모든 데이터 로드"""
        try:
            self._load_player_data()
            self._load_hud_positions()
            self._load_config()
            logging.info("All data loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load data: {e}")

    def _save_all_data(self):
        """모든 데이터 저장"""
        try:
            self._save_player_data()
            self._save_hud_positions()
            self._save_config()
            logging.info("All data saved successfully")
        except Exception as e:
            logging.error(f"Failed to save data: {e}")

    def _load_player_data(self):
        """플레이어 데이터 파일 로드"""
        try:
            if DB_FILE.exists():
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.player_data = json.load(f)
            else:
                self.player_data = {}
        except Exception as e:
            logging.error(f"Failed to load player data: {e}")
            self.player_data = {}

    def _save_player_data(self):
        """플레이어 데이터 파일 저장"""
        try:
            DB_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.player_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save player data: {e}")

    def _load_hud_positions(self):
        """HUD 위치 파일 로드"""
        try:
            if POS_FILE.exists():
                with open(POS_FILE, 'r', encoding='utf-8') as f:
                    self.hud_positions = json.load(f)
            else:
                self.hud_positions = {}
        except Exception as e:
            logging.error(f"Failed to load HUD positions: {e}")
            self.hud_positions = {}

    def _save_hud_positions(self):
        """HUD 위치 파일 저장"""
        try:
            POS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(POS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.hud_positions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save HUD positions: {e}")

    def _load_config(self):
        """설정 파일 로드"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config_data.update(loaded_config)
            else:
                self.config_data = DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            self.config_data = DEFAULT_CONFIG.copy()

    def _save_config(self):
        """설정 파일 저장"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def _auto_save(self):
        """자동 저장"""
        try:
            if self.is_running:
                self._save_all_data()
                logging.debug("Auto-saved data")
        except Exception as e:
            logging.error(f"Auto-save failed: {e}")

    def _on_player_data_update(self, event):
        """플레이어 데이터 업데이트 이벤트 처리"""
        try:
            data = event.data
            if isinstance(data, dict) and "player_data" in data:
                player_data = data["player_data"]
                player_id = player_data.get("id", "unknown")
                self.save_player_data(player_id, player_data)
        except Exception as e:
            logging.error(f"Error handling player data update: {e}")

    def _on_config_changed(self, event):
        """설정 변경 이벤트 처리"""
        try:
            data = event.data
            if isinstance(data, dict):
                self.save_config(data)
        except Exception as e:
            logging.error(f"Error handling config change: {e}")

    def _on_hud_update(self, event):
        """HUD 업데이트 이벤트 처리"""
        try:
            data = event.data
            if isinstance(data, dict) and "positions" in data:
                self.save_hud_positions(data["positions"])
        except Exception as e:
            logging.error(f"Error handling HUD update: {e}")
# === Standard Library Imports ===
from typing import Dict, Any, Optional
import logging

# === Third-Party Imports ===
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# === Local Imports ===
from interfaces import IPlugin
from hud.player_hud import PlayerHUD
from data_flow_manager import DataFlowManager

class HUDPlugin(IPlugin):
    """HUD 플러그인 구현"""

    def __init__(self):
        self.name = "HUD Plugin"
        self.version = "1.0.0"
        self.description = "Poker HUD 플러그인"
        self.is_running = False
        self.data_flow_manager: Optional[DataFlowManager] = None
        self.hud_widgets: Dict[str, PlayerHUD] = {}
        self.app: Optional[QApplication] = None

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def get_description(self) -> str:
        return self.description

    def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            # 입력 유효성 검사
            if not isinstance(config, dict):
                logging.error("Invalid config type")
                return False

            self.data_flow_manager = config.get('data_flow_manager')
            if not self.data_flow_manager:
                logging.error("DataFlowManager not provided in config")
                return False

            # DataFlowManager 인터페이스 검증
            if not hasattr(self.data_flow_manager, 'get_event_bus'):
                logging.error("Invalid DataFlowManager: missing get_event_bus method")
                return False

            # QApplication 생성 (부수 효과 최소화)
            self.app = QApplication.instance()
            if not self.app:
                # QApplication이 없을 때만 생성 (한 번만)
                import sys
                self.app = QApplication(sys.argv if hasattr(sys, 'argv') else [])

            # 이벤트 구독
            event_bus = self.data_flow_manager.get_event_bus()
            if event_bus:
                event_bus.subscribe("hud_update", self._on_hud_update)
                event_bus.subscribe("player_data_update", self._on_player_data_update)

            logging.info(f"{self.get_name()} initialized")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize {self.get_name()}: {e}")
            return False

    def start(self) -> bool:
        if not self.data_flow_manager:
            return False

        try:
            self.is_running = True
            logging.info(f"{self.get_name()} started")
            return True
        except Exception as e:
            logging.error(f"Failed to start {self.get_name()}: {e}")
            return False

    def stop(self) -> bool:
        try:
            self.is_running = False
            # HUD 위젯들 숨기기
            for hud in self.hud_widgets.values():
                hud.hide()
            logging.info(f"{self.get_name()} stopped")
            return True
        except Exception as e:
            logging.error(f"Failed to stop {self.get_name()}: {e}")
            return False

    def shutdown(self) -> bool:
        try:
            self.stop()
            # HUD 위젯들 정리
            for hud in list(self.hud_widgets.keys()):
                self.remove_hud_widget(hud)
            self.hud_widgets.clear()
            self.data_flow_manager = None
            logging.info(f"{self.get_name()} shutdown")
            return True
        except Exception as e:
            logging.error(f"Failed to shutdown {self.get_name()}: {e}")
            return False

    def is_active(self) -> bool:
        return self.is_running

    def create_hud_widget(self, player_id: str, x: int, y: int, w: int, h: int,
                         config: Dict[str, Any]) -> bool:
        """HUD 위젯 생성"""
        try:
            if player_id in self.hud_widgets:
                logging.warning(f"HUD widget for {player_id} already exists")
                return False

            # PlayerHUD 생성
            hud = PlayerHUD(0, x, y, w, h, self.data_flow_manager, config)
            self.hud_widgets[player_id] = hud

            logging.info(f"Created HUD widget for {player_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to create HUD widget for {player_id}: {e}")
            return False

    def remove_hud_widget(self, player_id: str) -> bool:
        """HUD 위젯 제거"""
        try:
            if player_id not in self.hud_widgets:
                return False

            hud = self.hud_widgets[player_id]
            hud.hide()
            hud.deleteLater()
            del self.hud_widgets[player_id]

            logging.info(f"Removed HUD widget for {player_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to remove HUD widget for {player_id}: {e}")
            return False

    def update_hud_widget(self, player_id: str, data: Dict[str, Any]) -> bool:
        """HUD 위젯 업데이트"""
        try:
            if player_id not in self.hud_widgets:
                logging.warning(f"HUD widget for {player_id} not found")
                return False

            hud = self.hud_widgets[player_id]
            # PlayerHUD의 업데이트 메서드 호출 (실제 구현 필요)
            # hud.update_player_data(data)
            logging.info(f"Updated HUD widget for {player_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to update HUD widget for {player_id}: {e}")
            return False

    def get_hud_widgets(self) -> Dict[str, PlayerHUD]:
        """모든 HUD 위젯 반환"""
        return self.hud_widgets.copy()

    def _on_hud_update(self, event):
        """HUD 업데이트 이벤트 처리"""
        try:
            data = event.data
            if isinstance(data, dict) and "player_data" in data:
                player_data = data["player_data"]
                player_id = player_data.get("id", "unknown")
                self.update_hud_widget(player_id, player_data)
        except Exception as e:
            logging.error(f"Error handling HUD update: {e}")

    def _on_player_data_update(self, event):
        """플레이어 데이터 업데이트 이벤트 처리"""
        try:
            data = event.data
            if isinstance(data, dict) and "player_data" in data:
                player_data = data["player_data"]
                player_id = player_data.get("id", "unknown")
                self.update_hud_widget(player_id, player_data)
        except Exception as e:
            logging.error(f"Error handling player data update: {e}")
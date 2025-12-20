# === Standard Library Imports ===
import logging
from typing import Dict, Any

# === Third-Party Imports ===
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt6.QtCore import pyqtSignal

# === Local Imports ===
from .main_tab import MainTab
from .players_tab import PlayersTab
from .settings_tab import SettingsTab
from .scan_guide_tab import ScanGuideTab

class ControlPanel(QWidget):
    """컨트롤 패널 위젯"""

    # 시그널 정의
    scan_toggled = pyqtSignal(bool)      # 스캔 토글
    settings_changed = pyqtSignal(dict)  # 설정 변경
    player_selected = pyqtSignal(str)    # 플레이어 선택

    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.config = manager.config
        self.db = manager.db
        self.selected_player = None

        self.initUI()
        self.load_settings()

    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle("Poker HUD Control Panel")
        self.setFixedWidth(400)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        # 메인 탭
        self.main_tab = MainTab(self.manager, self)
        self.tab_widget.addTab(self.main_tab, "메인")

        # 플레이어 탭
        self.players_tab = PlayersTab(self.manager, self)
        self.tab_widget.addTab(self.players_tab, "플레이어")

        # 설정 탭
        self.settings_tab = SettingsTab(self.manager, self)
        self.tab_widget.addTab(self.settings_tab, "설정")

        # 스캔 가이드 탭
        self.scan_guide_tab = ScanGuideTab(self.manager, self)
        self.tab_widget.addTab(self.scan_guide_tab, "스캔 가이드")

        layout.addWidget(self.tab_widget)

        # 상태 표시줄
        self.status_label = QLabel("HUD 준비됨")
        self.status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        layout.addWidget(self.status_label)

    def load_settings(self):
        """설정 로드"""
        self.settings_tab.load_settings()

    def update_scan_status(self, is_scanning: bool):
        """스캔 상태 업데이트"""
        # 메인 탭의 상태 업데이트
        if hasattr(self.main_tab, 'scan_status_label'):
            if is_scanning:
                self.main_tab.scan_status_label.setText("스캔 중...")
                self.main_tab.scan_status_label.setStyleSheet("color: #27AE60;")
            else:
                self.main_tab.scan_status_label.setText("스캔 중지됨")
                self.main_tab.scan_status_label.setStyleSheet("color: #E74C3C;")

    def update_players_list(self):
        """플레이어 리스트 업데이트"""
        self.players_tab.update_players_list()

    def update_player_info(self):
        """선택된 플레이어 정보 업데이트"""
        self.players_tab.update_player_info()

    def show_player_detail(self, player_id: str):
        """플레이어 상세 정보 표시"""
        self.selected_player = player_id
        self.update_player_info()

        # 리스트에서 해당 아이템 선택
        for i in range(self.players_tab.players_list.count()):
            item = self.players_tab.players_list.item(i)
            if item.text().startswith(player_id):
                self.players_tab.players_list.setCurrentItem(item)
                break

    def on_range_saved(self, player_id: str, range_data: Dict[str, Any]):
        """레인지 저장 처리"""
        if player_id in self.db:
            self.db[player_id]['range'] = range_data
            self.manager.hud_actions.save_database()
            logging.info(f"플레이어 {player_id} 레인지 저장됨")

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 설정 자동 저장
        if hasattr(self.settings_tab, 'auto_save_check') and self.settings_tab.auto_save_check.isChecked():
            self.settings_tab.save_settings()
        event.accept()
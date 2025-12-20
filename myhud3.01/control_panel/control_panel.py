# === Standard Library Imports ===
import logging
import json
import os
from typing import Dict, Any, Optional

# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QTabWidget,
    QGroupBox, QCheckBox, QSpinBox, QComboBox, QMessageBox,
    QSplitter, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QIcon

# === Local Imports ===
from config import CONFIG_FILE, DB_FILE, STYLES
from widgets.scan_guide import ScanGuide
from widgets.range_window import RangeWindow

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
        self.main_tab = self.create_main_tab()
        self.tab_widget.addTab(self.main_tab, "메인")

        # 플레이어 탭
        self.players_tab = self.create_players_tab()
        self.tab_widget.addTab(self.players_tab, "플레이어")

        # 설정 탭
        self.settings_tab = self.create_settings_tab()
        self.tab_widget.addTab(self.settings_tab, "설정")

        # 스캔 가이드 탭
        self.scan_guide_tab = self.create_scan_guide_tab()
        self.tab_widget.addTab(self.scan_guide_tab, "스캔 가이드")

        layout.addWidget(self.tab_widget)

        # 상태 표시줄
        self.status_label = QLabel("HUD 준비됨")
        self.status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        layout.addWidget(self.status_label)

    def create_main_tab(self) -> QWidget:
        """메인 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 스캔 컨트롤 그룹
        scan_group = QGroupBox("스캔 컨트롤")
        scan_layout = QVBoxLayout(scan_group)

        self.scan_button = QPushButton("스캔 시작")
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.scan_button.clicked.connect(self.toggle_scan)
        scan_layout.addWidget(self.scan_button)

        # 스캔 상태 표시
        self.scan_status_label = QLabel("스캔 중지됨")
        self.scan_status_label.setStyleSheet("color: #E74C3C;")
        scan_layout.addWidget(self.scan_status_label)

        layout.addWidget(scan_group)

        # 빠른 액션 그룹
        actions_group = QGroupBox("빠른 액션")
        actions_layout = QVBoxLayout(actions_group)

        # 스타일 변경 버튼들
        styles_layout = QHBoxLayout()
        style_buttons = [
            ("🐟", "fish", "🟢 Fish"),
            ("🎯", "tag", "🟡 TAG"),
            ("🛡️", "nit", "🔴 Nit"),
            ("💥", "lag", "🔵 LAG"),
            ("🔥", "maniac", "🟠 Maniac"),
            ("👻", "weird", "🟣 Weird"),
            ("❓", "unknown", "⚪ Unknown")
        ]

        for emoji, key, style_name in style_buttons:
            btn = QPushButton(f"{emoji} {style_name}")
            btn.clicked.connect(lambda checked, s=style_name: self.quick_change_style(s))
            styles_layout.addWidget(btn)

        actions_layout.addLayout(styles_layout)

        # 기타 액션 버튼들
        other_actions_layout = QHBoxLayout()

        self.range_button = QPushButton("레인지 설정")
        self.range_button.clicked.connect(self.open_range_window)
        other_actions_layout.addWidget(self.range_button)

        self.delete_button = QPushButton("플레이어 삭제")
        self.delete_button.setStyleSheet("color: #E74C3C;")
        self.delete_button.clicked.connect(self.delete_selected_player)
        other_actions_layout.addWidget(self.delete_button)

        actions_layout.addLayout(other_actions_layout)

        layout.addWidget(actions_group)

        return tab

    def create_players_tab(self) -> QWidget:
        """플레이어 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 플레이어 리스트
        self.players_list = QListWidget()
        self.players_list.itemClicked.connect(self.on_player_selected)
        self.players_list.setMaximumHeight(200)
        layout.addWidget(self.players_list)

        # 선택된 플레이어 정보
        info_group = QGroupBox("플레이어 정보")
        info_layout = QVBoxLayout(info_group)

        self.player_name_label = QLabel("선택된 플레이어: 없음")
        self.player_name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.player_name_label)

        self.player_style_label = QLabel("스타일: -")
        info_layout.addWidget(self.player_style_label)

        # 메모 편집
        info_layout.addWidget(QLabel("메모:"))
        self.player_memo_edit = QTextEdit()
        self.player_memo_edit.setMaximumHeight(100)
        self.player_memo_edit.textChanged.connect(self.on_memo_changed)
        info_layout.addWidget(self.player_memo_edit)

        # 통계 정보
        stats_group = QGroupBox("게임 통계")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("통계 정보가 없습니다.")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        info_layout.addWidget(stats_group)
        layout.addWidget(info_group)

        # 플레이어 리스트 업데이트
        self.update_players_list()

        return tab

    def create_settings_tab(self) -> QWidget:
        """설정 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 스캔 설정
        scan_settings_group = QGroupBox("스캔 설정")
        scan_layout = QVBoxLayout(scan_settings_group)

        # 스캔 간격
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("스캔 간격 (ms):"))
        self.scan_interval_spin = QSpinBox()
        self.scan_interval_spin.setRange(100, 5000)
        self.scan_interval_spin.setValue(1000)
        self.scan_interval_spin.valueChanged.connect(self.on_setting_changed)
        interval_layout.addWidget(self.scan_interval_spin)
        scan_layout.addLayout(interval_layout)

        # 재시도 횟수
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("재시도 횟수:"))
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        self.retry_spin.setValue(3)
        self.retry_spin.valueChanged.connect(self.on_setting_changed)
        retry_layout.addWidget(self.retry_spin)
        scan_layout.addLayout(retry_layout)

        layout.addWidget(scan_settings_group)

        # HUD 설정
        hud_settings_group = QGroupBox("HUD 설정")
        hud_layout = QVBoxLayout(hud_settings_group)

        # HUD 크기
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("HUD 너비:"))
        self.hud_width_spin = QSpinBox()
        self.hud_width_spin.setRange(80, 200)
        self.hud_width_spin.setValue(120)
        self.hud_width_spin.valueChanged.connect(self.on_setting_changed)
        size_layout.addWidget(self.hud_width_spin)

        size_layout.addWidget(QLabel("HUD 높이:"))
        self.hud_height_spin = QSpinBox()
        self.hud_height_spin.setRange(80, 200)
        self.hud_height_spin.setValue(123)
        self.hud_height_spin.valueChanged.connect(self.on_setting_changed)
        size_layout.addWidget(self.hud_height_spin)

        hud_layout.addLayout(size_layout)

        # 자동 저장
        self.auto_save_check = QCheckBox("자동 저장 활성화")
        self.auto_save_check.setChecked(True)
        self.auto_save_check.stateChanged.connect(self.on_setting_changed)
        hud_layout.addWidget(self.auto_save_check)

        layout.addWidget(hud_settings_group)

        # 단축키 설정
        shortcuts_group = QGroupBox("단축키 설정")
        shortcuts_layout = QVBoxLayout(shortcuts_group)

        shortcuts_info = QLabel(
            "단축키는 설정 파일에서 직접 편집하세요.\n"
            "지원되는 키: Ctrl, Shift, Alt + 알파벳/숫자/F1-F12"
        )
        shortcuts_info.setWordWrap(True)
        shortcuts_layout.addWidget(shortcuts_info)

        layout.addWidget(shortcuts_group)

        # 저장 버튼
        save_settings_button = QPushButton("설정 저장")
        save_settings_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        save_settings_button.clicked.connect(self.save_settings)
        layout.addWidget(save_settings_button)

        return tab

    def create_scan_guide_tab(self) -> QWidget:
        """스캔 가이드 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 스캔 가이드 위젯
        self.scan_guide = ScanGuide()
        self.scan_guide.guide_updated.connect(self.on_guide_updated)
        layout.addWidget(self.scan_guide)

        return tab

    def toggle_scan(self):
        """스캔 토글"""
        is_scanning = self.manager.is_scanning

        if is_scanning:
            self.scan_button.setText("스캔 시작")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            self.scan_status_label.setText("스캔 중지됨")
            self.scan_status_label.setStyleSheet("color: #E74C3C;")
        else:
            self.scan_button.setText("스캔 중지")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #C0392B;
                }
            """)
            self.scan_status_label.setText("스캔 중...")
            self.scan_status_label.setStyleSheet("color: #27AE60;")

        self.scan_toggled.emit(not is_scanning)

    def quick_change_style(self, style: str):
        """빠른 스타일 변경"""
        if not self.selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        # 스타일 변경 로직
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.update_player_style(self.selected_player, style)

        self.update_player_info()

    def open_range_window(self):
        """레인지 창 열기"""
        if not self.selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        # 플레이어의 현재 레인지 가져오기
        current_range = {}
        if self.selected_player in self.db:
            current_range = self.db[self.selected_player].get('range', {})

        # 레인지 창 열기
        range_window = RangeWindow(self.selected_player, current_range, self)
        range_window.range_saved.connect(self.on_range_saved)
        range_window.exec()

    def on_range_saved(self, player_id: str, range_data: dict):
        """레인지 저장 처리"""
        if player_id in self.db:
            self.db[player_id]['range'] = range_data
            self.manager.hud_actions.save_database()
            logging.info(f"플레이어 {player_id} 레인지 저장됨")

    def delete_selected_player(self):
        """선택된 플레이어 삭제"""
        if not self.selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "확인",
            f"플레이어 '{self.selected_player}'을(를) 삭제하시겠습니까?\n"
            "이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.manager, 'hud_actions'):
                self.manager.hud_actions.delete_player(self.selected_player)
            self.selected_player = None
            self.update_players_list()
            self.update_player_info()

    def on_player_selected(self, item: QListWidgetItem):
        """플레이어 선택 처리"""
        player_id = item.text().split(' (')[0]  # 스타일 부분 제거
        self.selected_player = player_id
        self.show_player_detail(player_id)

    def show_player_detail(self, player_id: str):
        """플레이어 상세 정보 표시"""
        self.selected_player = player_id
        self.update_player_info()

        # 리스트에서 해당 아이템 선택
        for i in range(self.players_list.count()):
            item = self.players_list.item(i)
            if item.text().startswith(player_id):
                self.players_list.setCurrentItem(item)
                break

    def update_players_list(self):
        """플레이어 리스트 업데이트"""
        self.players_list.clear()

        for player_id, player_data in self.db.items():
            style = player_data.get('style', '⚪ Unknown')
            item_text = f"{player_id} ({style})"
            item = QListWidgetItem(item_text)
            self.players_list.addItem(item)

    def update_player_info(self):
        """선택된 플레이어 정보 업데이트"""
        if not self.selected_player or self.selected_player not in self.db:
            self.player_name_label.setText("선택된 플레이어: 없음")
            self.player_style_label.setText("스타일: -")
            self.player_memo_edit.setPlainText("")
            self.stats_label.setText("통계 정보가 없습니다.")
            return

        player_data = self.db[self.selected_player]

        self.player_name_label.setText(f"선택된 플레이어: {self.selected_player}")
        self.player_style_label.setText(f"스타일: {player_data.get('style', '⚪ Unknown')}")

        # 메모 업데이트 (무한 루프 방지)
        current_memo = self.player_memo_edit.toPlainText()
        db_memo = player_data.get('note', '')
        if current_memo != db_memo:
            self.player_memo_edit.blockSignals(True)
            self.player_memo_edit.setPlainText(db_memo)
            self.player_memo_edit.blockSignals(False)

        # 통계 정보
        range_data = player_data.get('range', {})
        if range_data:
            total_hands = 0
            position_count = len(range_data)
            for pos_data in range_data.values():
                if 'hands' in pos_data:
                    total_hands += len(pos_data['hands'])

            self.stats_label.setText(
                f"포지션: {position_count}개\n"
                f"총 핸드: {total_hands}개"
            )
        else:
            self.stats_label.setText("레인지 데이터가 없습니다.")

    def on_memo_changed(self):
        """메모 변경 처리"""
        if not self.selected_player:
            return

        memo = self.player_memo_edit.toPlainText()
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.update_player_note(self.selected_player, memo)

    def load_settings(self):
        """설정 로드"""
        # 스캔 설정
        scan_config = self.config.get('scan', {})
        self.scan_interval_spin.setValue(scan_config.get('interval', 1000))
        self.retry_spin.setValue(scan_config.get('retries', 3))

        # HUD 설정
        hud_config = self.config.get('hud', {})
        self.hud_width_spin.setValue(hud_config.get('width', 120))
        self.hud_height_spin.setValue(hud_config.get('height', 123))
        self.auto_save_check.setChecked(self.config.get('auto_save', True))

    def on_setting_changed(self):
        """설정 변경 처리"""
        if self.auto_save_check.isChecked():
            self.save_settings()

    def save_settings(self):
        """설정 저장"""
        # 설정 데이터 수집
        settings = {
            'scan': {
                'interval': self.scan_interval_spin.value(),
                'retries': self.retry_spin.value()
            },
            'hud': {
                'width': self.hud_width_spin.value(),
                'height': self.hud_height_spin.value()
            },
            'auto_save': self.auto_save_check.isChecked()
        }

        # 기존 설정과 병합
        self.config.update(settings)

        # 설정 파일 저장
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.save_config()

        self.settings_changed.emit(settings)
        self.status_label.setText("설정이 저장되었습니다.")

    def on_guide_updated(self, guide_data: dict):
        """가이드 업데이트 처리"""
        self.config['scan_guide'] = guide_data
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.save_config()
        logging.info("스캔 가이드 설정이 저장되었습니다.")

    def update_scan_status(self, is_scanning: bool):
        """스캔 상태 업데이트"""
        if is_scanning:
            self.scan_status_label.setText("스캔 중...")
            self.scan_status_label.setStyleSheet("color: #27AE60;")
        else:
            self.scan_status_label.setText("스캔 중지됨")
            self.scan_status_label.setStyleSheet("color: #E74C3C;")

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 설정 자동 저장
        if self.auto_save_check.isChecked():
            self.save_settings()
        event.accept()
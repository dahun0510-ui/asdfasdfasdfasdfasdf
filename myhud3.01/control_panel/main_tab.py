# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class MainTab(QWidget):
    """메인 탭 위젯"""

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.config = manager.config
        self.db = manager.db

        self.initUI()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

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

        self.parent().scan_toggled.emit(not is_scanning)  # 시그널 발생

    def quick_change_style(self, style: str):
        """빠른 스타일 변경"""
        if not hasattr(self.parent(), 'selected_player') or not self.parent().selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        # 스타일 변경 로직
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.update_player_style(self.parent().selected_player, style)

        self.parent().update_player_info()

    def open_range_window(self):
        """레인지 창 열기"""
        if not hasattr(self.parent(), 'selected_player') or not self.parent().selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        # 플레이어의 현재 레인지 가져오기
        current_range = {}
        if self.parent().selected_player in self.db:
            current_range = self.db[self.parent().selected_player].get('range', {})

        # 레인지 창 열기
        range_window = RangeWindow(self.parent().selected_player, current_range, self)
        range_window.range_saved.connect(self.parent().on_range_saved)
        range_window.exec()

    def delete_selected_player(self):
        """선택된 플레이어 삭제"""
        if not hasattr(self.parent(), 'selected_player') or not self.parent().selected_player:
            QMessageBox.warning(self, "경고", "플레이어를 먼저 선택하세요.")
            return

        reply = QMessageBox.question(
            self, "확인",
            f"플레이어 '{self.parent().selected_player}'을(를) 삭제하시겠습니까?\n"
            "이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.manager, 'hud_actions'):
                self.manager.hud_actions.delete_player(self.parent().selected_player)
            self.parent().selected_player = None
            self.parent().update_players_list()
            self.parent().update_player_info()
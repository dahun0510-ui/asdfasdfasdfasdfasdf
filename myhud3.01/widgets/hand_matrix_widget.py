# === Standard Library Imports ===
import logging
from typing import Dict, Any, Optional

# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# === Local Imports ===
from config import HAND_RANKS, HAND_SUITS, HAND_PERCENTILE

class HandMatrixWidget(QWidget):
    """핸드 매트릭스 위젯"""

    hand_selected = pyqtSignal(str, str)  # hand, action

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_range = {}  # 현재 선택된 레인지
        self.selected_action = "raise"  # 기본 액션
        self.matrix_buttons = {}  # 버튼 저장용 딕셔너리

        self.initUI()
        self.update_matrix_display()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 액션 선택 버튼들
        actions_layout = QHBoxLayout()

        self.action_buttons = {}
        actions = [
            ("Fold", "fold", "#FF6B6B"),
            ("Call", "call", "#4ECDC4"),
            ("Raise", "raise", "#45B7D1")
        ]

        for action_name, action_key, color in actions:
            btn = QPushButton(action_name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {color}DD;
                    border: 2px solid #FFD93D;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, key=action_key: self.set_action(key))
            actions_layout.addWidget(btn)
            self.action_buttons[action_key] = btn

        # Raise 버튼을 기본 선택
        self.action_buttons["raise"].setChecked(True)

        layout.addLayout(actions_layout)

        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 매트릭스 컨테이너
        self.matrix_container = QWidget()
        self.matrix_layout = QGridLayout(self.matrix_container)
        self.matrix_layout.setSpacing(1)
        self.matrix_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area.setWidget(self.matrix_container)
        layout.addWidget(scroll_area)

        # 행/열 헤더 추가
        self._create_headers()

        # 핸드 버튼들 생성
        self._create_hand_buttons()

    def _create_headers(self):
        """행과 열 헤더 생성"""
        # 코너 빈 공간
        corner_label = QLabel("")
        corner_label.setFixedSize(30, 30)
        self.matrix_layout.addWidget(corner_label, 0, 0)

        # 열 헤더 (수트)
        for col, suit in enumerate(HAND_SUITS, 1):
            suit_label = QLabel(suit)
            suit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            suit_label.setStyleSheet("""
                QLabel {
                    background-color: #2C3E50;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #34495E;
                }
            """)
            suit_label.setFixedSize(30, 30)
            self.matrix_layout.addWidget(suit_label, 0, col)

        # 행 헤더 (랭크)
        for row, rank in enumerate(HAND_RANKS, 1):
            rank_label = QLabel(rank)
            rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_label.setStyleSheet("""
                QLabel {
                    background-color: #2C3E50;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #34495E;
                }
            """)
            rank_label.setFixedSize(30, 30)
            self.matrix_layout.addWidget(rank_label, row, 0)

    def _create_hand_buttons(self):
        """핸드 버튼들 생성"""
        for row, rank1 in enumerate(HAND_RANKS):
            for col, suit1 in enumerate(HAND_SUITS):
                for col2, suit2 in enumerate(HAND_SUITS):
                    if col > col2:  # 중복 방지 (순서 없는 페어)
                        continue

                    # 핸드 생성 (예: AsKh, 22s 등)
                    if rank1 == HAND_RANKS[col2]:  # 페어
                        hand = f"{rank1}{rank1}"
                        if suit1 == suit2:
                            hand += "s"  # suited
                        else:
                            hand += "o"  # offsuit
                    else:
                        hand = f"{rank1}{HAND_RANKS[col2]}"
                        if suit1 == suit2:
                            hand += "s"
                        else:
                            hand += "o"

                    # 버튼 생성
                    btn = QPushButton(hand)
                    btn.setFixedSize(45, 30)
                    btn.setStyleSheet(self._get_button_style(hand, False))
                    btn.clicked.connect(lambda checked, h=hand: self.toggle_hand(h))

                    # 버튼 위치 계산 (대칭 매트릭스)
                    matrix_row = row + 1
                    matrix_col = col + 1

                    self.matrix_layout.addWidget(btn, matrix_row, matrix_col)
                    self.matrix_buttons[hand] = btn

    def _get_button_style(self, hand: str, is_selected: bool) -> str:
        """버튼 스타일 반환"""
        if not is_selected:
            return """
                QPushButton {
                    background-color: #ECF0F1;
                    color: #2C3E50;
                    border: 1px solid #BDC3C7;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #D5DBDB;
                }
            """

        # 선택된 경우 액션별 색상
        action_colors = {
            "fold": "#FF6B6B",
            "call": "#4ECDC4",
            "raise": "#45B7D1"
        }

        color = action_colors.get(self.selected_action, "#95A5A6")

        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: 2px solid #FFD93D;
                font-size: 10px;
                font-weight: bold;
            }}
        """

    def set_action(self, action: str):
        """액션 설정"""
        self.selected_action = action

        # 다른 버튼들 체크 해제
        for key, btn in self.action_buttons.items():
            btn.setChecked(key == action)

        # 선택된 핸드들의 스타일 업데이트
        for hand, btn in self.matrix_buttons.items():
            if hand in self.current_range:
                hand_data = self.current_range[hand]
                if isinstance(hand_data, dict) and hand_data.get('action') == action:
                    btn.setStyleSheet(self._get_button_style(hand, True))
                else:
                    btn.setStyleSheet(self._get_button_style(hand, False))

    def toggle_hand(self, hand: str):
        """핸드 토글"""
        if hand in self.current_range:
            current_action = self.current_range[hand]
            if isinstance(current_action, dict):
                current_action = current_action.get('action', 'fold')

            if current_action == self.selected_action:
                # 같은 액션인 경우 제거
                del self.current_range[hand]
                self.matrix_buttons[hand].setStyleSheet(self._get_button_style(hand, False))
            else:
                # 다른 액션인 경우 변경
                self.current_range[hand] = {'action': self.selected_action}
                self.matrix_buttons[hand].setStyleSheet(self._get_button_style(hand, True))
        else:
            # 새로 추가
            self.current_range[hand] = {'action': self.selected_action}
            self.matrix_buttons[hand].setStyleSheet(self._get_button_style(hand, True))

        # 시그널 발생
        self.hand_selected.emit(hand, self.selected_action)

    def set_range(self, range_data: Dict[str, Any]):
        """레인지 설정"""
        self.current_range = range_data.copy()
        self.update_matrix_display()

    def get_range(self) -> Dict[str, Any]:
        """현재 레인지 반환"""
        return self.current_range.copy()

    def update_matrix_display(self):
        """매트릭스 표시 업데이트"""
        for hand, btn in self.matrix_buttons.items():
            if hand in self.current_range:
                hand_data = self.current_range[hand]
                if isinstance(hand_data, dict):
                    action = hand_data.get('action', 'fold')
                else:
                    action = hand_data

                is_selected = action == self.selected_action
                btn.setStyleSheet(self._get_button_style(hand, is_selected))
            else:
                btn.setStyleSheet(self._get_button_style(hand, False))

    def clear_range(self):
        """레인지 초기화"""
        self.current_range.clear()
        self.update_matrix_display()

    def select_all_hands(self, action: str = None):
        """모든 핸드 선택"""
        if action is None:
            action = self.selected_action

        for hand in self.matrix_buttons.keys():
            self.current_range[hand] = {'action': action}

        self.update_matrix_display()

    def get_range_stats(self) -> Dict[str, int]:
        """레인지 통계 반환"""
        stats = {'fold': 0, 'call': 0, 'raise': 0}

        for hand_data in self.current_range.values():
            if isinstance(hand_data, dict):
                action = hand_data.get('action', 'fold')
            else:
                action = hand_data

            if action in stats:
                stats[action] += 1

        return stats

    def get_percentile_range(self, min_percentile: int, max_percentile: int) -> Dict[str, Any]:
        """퍼센타일 범위의 핸드들 반환"""
        result = {}

        for hand, percentile in HAND_PERCENTILE.items():
            if min_percentile <= percentile <= max_percentile:
                if hand in self.current_range:
                    result[hand] = self.current_range[hand]

        return result
# === Standard Library Imports ===
import logging
from typing import Dict, Any, Optional

# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QComboBox, QSpinBox, QGroupBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# === Local Imports ===
from widgets.hand_matrix_widget import HandMatrixWidget

class RangeWindow(QDialog):
    """레인지 설정 창"""

    range_saved = pyqtSignal(str, dict)  # player_id, range_data

    def __init__(self, player_id: str, current_range: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.player_id = player_id
        self.current_range = current_range or {}
        self.positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]

        self.initUI()
        self.load_current_range()

    def initUI(self):
        """UI 초기화"""
        self.setWindowTitle(f"레인지 설정 - {self.player_id}")
        self.setModal(True)
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        # 플레이어 정보
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"플레이어: {self.player_id}"))

        self.position_combo = QComboBox()
        self.position_combo.addItems(self.positions)
        self.position_combo.currentTextChanged.connect(self.on_position_changed)
        info_layout.addWidget(QLabel("포지션:"))
        info_layout.addWidget(self.position_combo)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # 탭 위젯
        self.tab_widget = QTabWidget()

        # 포지션별 탭 생성
        self.position_tabs = {}
        self.matrix_widgets = {}

        for position in self.positions:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)

            # 핸드 매트릭스
            matrix = HandMatrixWidget()
            matrix.hand_selected.connect(self.on_hand_selected)
            tab_layout.addWidget(matrix)

            # 탭에 추가
            self.tab_widget.addTab(tab, position)
            self.position_tabs[position] = tab
            self.matrix_widgets[position] = matrix

        layout.addWidget(self.tab_widget)

        # 컨트롤 버튼들
        controls_layout = QHBoxLayout()

        self.clear_button = QPushButton("초기화")
        self.clear_button.clicked.connect(self.clear_current_range)
        controls_layout.addWidget(self.clear_button)

        self.load_default_button = QPushButton("기본 레인지 로드")
        self.load_default_button.clicked.connect(self.load_default_range)
        controls_layout.addWidget(self.load_default_button)

        self.percentile_button = QPushButton("퍼센타일 선택")
        self.percentile_button.clicked.connect(self.show_percentile_dialog)
        controls_layout.addWidget(self.percentile_button)

        controls_layout.addStretch()

        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        controls_layout.addWidget(self.cancel_button)

        self.save_button = QPushButton("저장")
        self.save_button.setStyleSheet("""
            QPushButton {{
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }}
        """)
        self.save_button.clicked.connect(self.save_range)
        controls_layout.addWidget(self.save_button)

        layout.addLayout(controls_layout)

    def on_position_changed(self, position: str):
        """포지션 변경 처리"""
        if position in self.matrix_widgets:
            self.tab_widget.setCurrentWidget(self.position_tabs[position])

    def load_current_range(self):
        """현재 레인지 로드"""
        for position in self.positions:
            range_data = self.current_range.get(position, {}).get('hands', {})
            if range_data:
                self.matrix_widgets[position].set_range(range_data)

    def on_hand_selected(self, hand: str, action: str):
        """핸드 선택 처리"""
        # 현재 포지션의 매트릭스에서 핸드 선택 처리
        current_position = self.position_combo.currentText()
        if current_position in self.matrix_widgets:
            # 이미 HandMatrixWidget에서 처리됨
            pass

    def clear_current_range(self):
        """현재 포지션 레인지 초기화"""
        current_position = self.position_combo.currentText()
        if current_position in self.matrix_widgets:
            self.matrix_widgets[current_position].clear_range()

    def load_default_range(self):
        """기본 레인지 로드"""
        # 기본 레인지는 포지션별로 다르게 설정
        default_ranges = {
            "UTG": self._get_default_utg_range(),
            "MP": self._get_default_mp_range(),
            "CO": self._get_default_co_range(),
            "BTN": self._get_default_btn_range(),
            "SB": self._get_default_sb_range(),
            "BB": self._get_default_bb_range()
        }

        current_position = self.position_combo.currentText()
        if current_position in default_ranges:
            self.matrix_widgets[current_position].set_range(default_ranges[current_position])

    def show_percentile_dialog(self):
        """퍼센타일 선택 다이얼로그"""
        dialog = PercentileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            min_pct, max_pct = dialog.get_values()
            current_position = self.position_combo.currentText()
            if current_position in self.matrix_widgets:
                matrix = self.matrix_widgets[current_position]
                percentile_range = matrix.get_percentile_range(min_pct, max_pct)
                matrix.set_range(percentile_range)

    def save_range(self):
        """레인지 저장"""
        range_data = {}

        for position in self.positions:
            matrix = self.matrix_widgets[position]
            hands_data = matrix.get_range()
            if hands_data:
                range_data[position] = {'hands': hands_data}

        # 저장 확인
        if not range_data:
            reply = QMessageBox.question(
                self, "확인",
                "저장할 레인지 데이터가 없습니다. 계속하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 시그널 발생
        self.range_saved.emit(self.player_id, range_data)
        self.accept()

    def get_range_data(self) -> Dict[str, Any]:
        """레인지 데이터 반환"""
        range_data = {}

        for position in self.positions:
            matrix = self.matrix_widgets[position]
            hands_data = matrix.get_range()
            if hands_data:
                range_data[position] = {'hands': hands_data}

        return range_data

    def _get_default_utg_range(self) -> Dict[str, Any]:
        """UTG 기본 레인지"""
        # 타이트한 레인지
        return {
            "AA": {"action": "raise"},
            "KK": {"action": "raise"},
            "QQ": {"action": "raise"},
            "JJ": {"action": "raise"},
            "TT": {"action": "raise"},
            "99": {"action": "raise"},
            "88": {"action": "raise"},
            "AKs": {"action": "raise"},
            "AQs": {"action": "raise"},
            "AJs": {"action": "raise"},
            "ATs": {"action": "raise"},
            "AKo": {"action": "raise"},
        }

    def _get_default_mp_range(self) -> Dict[str, Any]:
        """MP 기본 레인지"""
        # UTG보다 약간 넓은 레인지
        range_data = self._get_default_utg_range()
        additional_hands = {
            "77": {"action": "raise"},
            "66": {"action": "raise"},
            "A9s": {"action": "raise"},
            "AQo": {"action": "raise"},
            "KQs": {"action": "raise"},
        }
        range_data.update(additional_hands)
        return range_data

    def _get_default_co_range(self) -> Dict[str, Any]:
        """CO 기본 레인지"""
        # 더 넓은 레인지
        range_data = self._get_default_mp_range()
        additional_hands = {
            "55": {"action": "raise"},
            "44": {"action": "raise"},
            "A8s": {"action": "raise"},
            "AJo": {"action": "raise"},
            "KJs": {"action": "raise"},
            "QJs": {"action": "raise"},
        }
        range_data.update(additional_hands)
        return range_data

    def _get_default_btn_range(self) -> Dict[str, Any]:
        """BTN 기본 레인지"""
        # 매우 넓은 레인지
        range_data = self._get_default_co_range()
        additional_hands = {
            "33": {"action": "raise"},
            "22": {"action": "raise"},
            "A7s": {"action": "raise"},
            "A6s": {"action": "raise"},
            "A5s": {"action": "raise"},
            "A4s": {"action": "raise"},
            "A3s": {"action": "raise"},
            "A2s": {"action": "raise"},
            "KQo": {"action": "raise"},
            "QJo": {"action": "raise"},
            "JTo": {"action": "raise"},
            "T9s": {"action": "raise"},
            "98s": {"action": "raise"},
            "87s": {"action": "raise"},
            "76s": {"action": "raise"},
        }
        range_data.update(additional_hands)
        return range_data

    def _get_default_sb_range(self) -> Dict[str, Any]:
        """SB 기본 레인지"""
        # 매우 넓은 스틸 레인지
        return {
            "AA": {"action": "raise"},
            "KK": {"action": "raise"},
            "QQ": {"action": "raise"},
            "JJ": {"action": "raise"},
            "TT": {"action": "raise"},
            "99": {"action": "raise"},
            "88": {"action": "raise"},
            "77": {"action": "raise"},
            "66": {"action": "raise"},
            "55": {"action": "raise"},
            "44": {"action": "raise"},
            "33": {"action": "raise"},
            "22": {"action": "raise"},
            "AKs": {"action": "raise"},
            "AQs": {"action": "raise"},
            "AJs": {"action": "raise"},
            "ATs": {"action": "raise"},
            "A9s": {"action": "raise"},
            "A8s": {"action": "raise"},
            "A7s": {"action": "raise"},
            "A6s": {"action": "raise"},
            "A5s": {"action": "raise"},
            "A4s": {"action": "raise"},
            "A3s": {"action": "raise"},
            "A2s": {"action": "raise"},
            "AKo": {"action": "raise"},
            "AQo": {"action": "raise"},
            "KQs": {"action": "raise"},
            "KJs": {"action": "raise"},
            "QJs": {"action": "raise"},
            "JTs": {"action": "raise"},
            "T9s": {"action": "raise"},
            "98s": {"action": "raise"},
            "87s": {"action": "raise"},
            "76s": {"action": "raise"},
            "65s": {"action": "raise"},
        }

    def _get_default_bb_range(self) -> Dict[str, Any]:
        """BB 기본 레인지"""
        # 콜/폴드 레인지 (3-bet 방어)
        return {
            "AA": {"action": "raise"},
            "KK": {"action": "raise"},
            "QQ": {"action": "raise"},
            "JJ": {"action": "raise"},
            "TT": {"action": "raise"},
            "99": {"action": "call"},
            "88": {"action": "call"},
            "77": {"action": "call"},
            "66": {"action": "call"},
            "55": {"action": "fold"},
            "AKs": {"action": "raise"},
            "AQs": {"action": "raise"},
            "AJs": {"action": "call"},
            "ATs": {"action": "call"},
            "A9s": {"action": "call"},
            "AKo": {"action": "raise"},
            "AQo": {"action": "call"},
        }


class PercentileDialog(QDialog):
    """퍼센타일 선택 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("퍼센타일 범위 선택")
        self.setModal(True)
        self.resize(300, 150)

        layout = QVBoxLayout(self)

        # 설명
        layout.addWidget(QLabel("선택할 핸드의 퍼센타일 범위를 설정하세요:"))

        # 범위 설정
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("최소:"))

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 100)
        self.min_spin.setValue(0)
        range_layout.addWidget(self.min_spin)

        range_layout.addWidget(QLabel("최대:"))

        self.max_spin = QSpinBox()
        self.max_spin.setRange(0, 100)
        self.max_spin.setValue(20)
        range_layout.addWidget(self.max_spin)

        layout.addLayout(range_layout)

        # 버튼들
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)

        layout.addLayout(buttons_layout)

    def get_values(self) -> tuple:
        """선택된 값들 반환"""
        return self.min_spin.value(), self.max_spin.value()
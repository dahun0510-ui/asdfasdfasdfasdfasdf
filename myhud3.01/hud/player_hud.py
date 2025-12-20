# === Standard Library Imports ===
import logging
from functools import partial

# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QContextMenuEvent

# === Local Imports ===
from config import STYLES, HAND_PERCENTILE

class PlayerHUD(QWidget):
    """플레이어 HUD 위젯"""

    def __init__(self, pos_idx, x, y, w, h, manager, config):
        super().__init__()
        self.pos_idx = pos_idx
        self.manager = manager
        self.config = config

        # 기본 속성 초기화
        self.player_id = "스캔 대기"
        self.note = ""
        self.is_moving = False
        self.context_menu_visible = False
        self.is_focused_hud = False
        self._memo_updating = False

        # 키보드 포커스 활성화
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # 창 설정
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(1.0)

        # HUD 크기
        self.hud_w = config.get('hud_width', 120)
        self.hud_h = config.get('hud_height', 123)
        self.setFixedSize(self.hud_w, self.hud_h)

        # 위치 설정
        hud_x = x - (self.hud_w - w) // 2
        hud_y = y - self.hud_h - 1
        self.setGeometry(hud_x, hud_y, self.hud_w, self.hud_h)

        self.initUI()
        self.show()

        self._drag_pos = None
        QTimer.singleShot(200, self.update_geometry)

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # 닉네임 라벨
        self.name_label = QLabel("Nickname")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: rgba(255,255,255,255); "
            "background: rgba(0,0,0,51); padding: 2px;"
        )
        self.name_label.setMaximumHeight(18)
        self.name_label.setMinimumHeight(18)
        self.name_label.setWordWrap(False)

        # 메모 편집기
        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText("메모...")
        self.memo_edit.setStyleSheet(
            "font-size: 10px; font-weight: 900; color: rgba(255,255,255,255); "
            "background: rgba(0,0,0,51); padding: 3px;"
        )
        self.memo_edit.setMaximumHeight(90)
        self.memo_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 메모 이벤트 연결
        self.memo_edit.textChanged.connect(self.on_memo_changed)
        self.memo_edit.mousePressEvent = self._on_memo_clicked
        self.memo_edit.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.memo_edit.customContextMenuRequested.connect(self._show_custom_context_menu)

        # 컨테이너
        self.container = QWidget()
        self.container.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(3)

        container_layout.addWidget(self.memo_edit)
        container_layout.addWidget(self.name_label)

        # 초기 스타일
        self.container.setStyleSheet(
            "background: rgba(30,30,30,51); border-radius: 6px;"
        )
        layout.addWidget(self.container)

    def _on_memo_clicked(self, event):
        """메모 클릭 시 HUD 포커싱"""
        # 다른 HUD 포커스 해제
        for hud in self.manager.huds:
            if hud != self:
                hud.set_focused(False)
        # 현재 HUD 포커스 설정
        self.set_focused(True)
        # 컨트롤 패널에 플레이어 정보 표시
        if self.manager.control_panel:
            self.manager.control_panel.show_player_detail(self.player_id)
        # 원래 이벤트 호출
        QTextEdit.mousePressEvent(self.memo_edit, event)

    def _show_custom_context_menu(self, pos):
        """메모에서 우클릭 시 HUD 컨텍스트 메뉴 표시"""
        global_pos = self.memo_edit.mapToGlobal(pos)
        from PyQt6.QtGui import QContextMenuEvent
        event = QContextMenuEvent(QContextMenuEvent.Reason.Mouse, pos, global_pos)
        self.contextMenuEvent(event)

    def set_focused(self, focused: bool):
        """HUD 포커스 상태 설정"""
        self.is_focused_hud = focused
        self.setWindowOpacity(1.0)
        self.update_style()

    def update_geometry(self):
        """HUD 위치 업데이트"""
        if self.pos_idx >= 0 and self.pos_idx < len(self.manager.pos_data):
            pos_data = self.manager.pos_data[self.pos_idx]
            self.manager.pos_data[self.pos_idx].update({
                'x': pos_data.get('x', 0),
                'y': pos_data.get('y', 0),
                'w': self.hud_w,
                'h': self.hud_h
            })

    def update_info(self, name: str, style_key: str, note: str = "", stats: dict = None):
        """HUD 정보 업데이트"""
        if self.is_moving:
            return

        if "스캔" in name:
            return

        # 업데이트 조건 확인
        current_style = getattr(self, 'style', "⚪ Unknown")
        if (self.player_id == name and
            current_style == style_key and
            self.note == note and
            not stats and
            not self.is_moving):
            return

        self.player_id = name
        self.note = note
        self.style = style_key

        # RFI 계산
        rfi_prefix = ""
        sb_bb_star = ""

        if name in self.manager.db:
            ranges = self.manager.db[name].get('range', {})
            if ranges:
                all_hands = {}
                sb_bb_hands = {}

                for pos in ranges.keys():
                    pos_hands = ranges[pos].get('hands', {})
                    if pos not in ['SB', 'BB']:
                        all_hands.update(pos_hands)
                    else:
                        sb_bb_hands.update(pos_hands)

                if all_hands:
                    rfi_pct = self._calculate_rfi_from_range(all_hands)
                    if rfi_pct > 0:
                        rfi_prefix = f"{rfi_pct}% "

                if sb_bb_hands:
                    sb_bb_pct = self._calculate_rfi_from_range(sb_bb_hands)
                    if sb_bb_pct > 0:
                        sb_bb_star = "★"

        # 표시 이름 설정
        display_name = f"{rfi_prefix}{sb_bb_star}{name}"
        color = next((c for s, c in STYLES if s == style_key), "#FFFFFF")

        # 스캔 상태에 따른 스타일
        is_scanning = "스캔" in name

        if is_scanning:
            name_bg = "rgba(0,0,0,51)"
            memo_bg = "rgba(0,0,0,51)"
        else:
            name_bg = "rgba(32,32,32,255)"
            if self.is_focused_hud:
                memo_bg = "rgba(0,0,0,128)"
            else:
                memo_bg = "rgba(0,0,0,51)"

        self.name_label.setText(display_name)
        self.name_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 10px; "
            f"padding: 2px; margin: 0px; background: {name_bg};"
        )

        # 메모 업데이트
        try:
            self.memo_edit.blockSignals(True)
            self.memo_edit.setPlainText(note)
        finally:
            self.memo_edit.blockSignals(False)

        self.memo_edit.setStyleSheet(
            f"font-size: 10px; font-weight: 900; color: rgba(255,255,255,255); "
            f"background: {memo_bg}; padding: 3px;"
        )

        self.update_style()

    def _calculate_rfi_from_range(self, hands_dict: dict) -> int:
        """레인지에서 RFI % 계산"""
        if not hands_dict:
            return 0

        max_pct = 0
        for hand in hands_dict.keys():
            hand_data = hands_dict[hand]
            if isinstance(hand_data, dict):
                action = hand_data.get('action', 'raise')
                if action != 'raise':
                    continue

            pct = HAND_PERCENTILE.get(hand, 0)
            if pct > max_pct:
                max_pct = pct

        return ((max_pct + 2) // 5) * 5

    def update_style(self):
        """스타일 업데이트"""
        if not hasattr(self, 'style'):
            self.style = "⚪ Unknown"

        color = next((c for s, c in STYLES if s == self.style), "#FFFFFF")
        border_width = 2 if self.is_focused_hud else 1

        if self.is_focused_hud:
            container_bg = "rgba(30,30,30,255)"
        else:
            container_bg = "rgba(30,30,30,128)"

        self.container.setStyleSheet(
            f"background: {container_bg}; "
            f"border: {border_width}px solid {color}; "
            f"border-radius: 6px;"
        )

    def mousePressEvent(self, event):
        """마우스 이벤트 처리"""
        button = event.button()
        modifiers = event.modifiers()

        # 마우스 버튼 단축키 처리
        if not self.is_moving and "스캔" not in self.player_id:
            button_map = {
                Qt.MouseButton.BackButton: "Mouse4",
                Qt.MouseButton.ForwardButton: "Mouse5",
                Qt.MouseButton.ExtraButton1: "Mouse6",
                Qt.MouseButton.ExtraButton2: "Mouse7",
                Qt.MouseButton.MiddleButton: "Mouse3",
                Qt.MouseButton.LeftButton: "Mouse1",
            }

            if button in button_map:
                parts = []
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    parts.append("Ctrl")
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    parts.append("Shift")
                if modifiers & Qt.KeyboardModifier.AltModifier:
                    parts.append("Alt")
                parts.append(button_map[button])

                shortcut_str = "+".join(parts)
                shortcuts = self.config.get('shortcuts', {})
                for action_key, shortcut_value in shortcuts.items():
                    if shortcut_value == shortcut_str:
                        self._execute_shortcut_action(action_key)
                        event.accept()
                        return

        # 기존 동작
        if self.is_moving and button == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
        elif "스캔" not in self.player_id and button == Qt.MouseButton.LeftButton:
            for hud in self.manager.huds:
                if hud != self:
                    hud.set_focused(False)
            self.setFocus()
            self.set_focused(True)
            if self.manager.control_panel:
                self.manager.control_panel.show_player_detail(self.player_id)
                self.manager.control_panel.activateWindow()
                self.manager.control_panel.raise_()

    def _execute_shortcut_action(self, action_key: str):
        """단축키 액션 실행"""
        style_map = {
            "fish": "🟢 Fish",
            "tag": "🟡 TAG",
            "nit": "🔴 Nit",
            "lag": "🔵 LAG",
            "maniac": "🟠 Maniac",
            "weird": "🟣 Weird",
            "unknown": "⚪ Unknown"
        }

        if action_key in style_map:
            self.change_style(style_map[action_key])
        elif action_key == "toggle_move":
            self.toggle_move()
        elif action_key == "range":
            self.open_range_window()
        elif action_key == "toggle_scan":
            if self.manager.control_panel:
                self.manager.control_panel.toggle_scan()

    def contextMenuEvent(self, event):
        """컨텍스트 메뉴"""
        if self.is_moving:
            return

        self.context_menu_visible = True
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #4CAF50;
            }
        """)

        shortcuts = self.config.get('shortcuts', {})

        style_info = [
            ('🟢 Fish', 'fish'),
            ('🟡 TAG', 'tag'),
            ('🔴 Nit', 'nit'),
            ('🔵 LAG', 'lag'),
            ('🟠 Maniac', 'maniac'),
            ('🟣 Weird', 'weird'),
            ('⚪ Unknown', 'unknown')
        ]

        for style, key in style_info:
            shortcut_key = shortcuts.get(key, '')
            if shortcut_key:
                menu.addAction(f"{style} ({shortcut_key})").triggered.connect(
                    partial(self.change_style, style))
            else:
                menu.addAction(style).triggered.connect(
                    partial(self.change_style, style))

        menu.addSeparator()

        move_key = shortcuts.get('toggle_move', 'L')
        move_txt = f"🔒 고정 ({move_key})" if self.is_moving else f"🔓 이동 ({move_key})"
        menu.addAction(move_txt).triggered.connect(self.toggle_move)

        if "스캔" not in self.player_id:
            menu.addAction("🗑️ 데이터 삭제").triggered.connect(self.delete_player)

        menu_pos = self.mapToGlobal(self.rect().center())
        menu.exec(menu_pos)
        self.context_menu_visible = False
        menu.deleteLater()

    def toggle_move(self):
        """이동 모드 토글"""
        self.is_moving = not self.is_moving
        logging.info(f"[HUD {self.pos_idx}] Move mode toggled: {self.is_moving}")

        if self.is_moving:
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def change_style(self, style):
        """스타일 변경"""
        if "스캔" in self.player_id:
            return
        p_data = self.manager.get_player_data(self.player_id)
        # 스타일 변경 로직 구현 필요

    def open_range_window(self):
        """레인지 창 열기"""
        # 레인지 창 열기 로직 구현 필요
        pass

    def delete_player(self):
        """플레이어 데이터 삭제"""
        # 플레이어 삭제 로직 구현 필요
        pass

    def on_memo_changed(self):
        """메모 변경 처리"""
        if self._memo_updating:
            return
        # 메모 변경 로직 구현 필요
# === Standard Library Imports ===
import logging
from typing import Optional

# === Third-Party Imports ===
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

# === Local Imports ===
# config import는 필요시 추가

class HudEvents:
    """HUD 이벤트 관리 클래스"""

    def __init__(self, manager):
        self.manager = manager
        self.config = manager.config
        self.key_timer = QTimer()
        self.key_timer.timeout.connect(self._reset_key_state)
        self.pressed_keys = set()

        # 액션 핸들러 딕셔너리 (OCP 준수)
        self.action_handlers = {
            "toggle_scan": self._handle_toggle_scan,
            "toggle_move": self._handle_toggle_move,
            "fish": lambda: self._handle_style_change("🟢 Fish"),
            "tag": lambda: self._handle_style_change("🟡 TAG"),
            "nit": lambda: self._handle_style_change("🔴 Nit"),
            "lag": lambda: self._handle_style_change("🔵 LAG"),
            "maniac": lambda: self._handle_style_change("🟠 Maniac"),
            "weird": lambda: self._handle_style_change("🟣 Weird"),
            "unknown": lambda: self._handle_style_change("⚪ Unknown"),
            "range": self._handle_range,
            "delete_player": self._handle_delete_player,
        }

    def handle_global_key_press(self, event: QKeyEvent):
        """전역 키보드 이벤트 처리"""
        key = event.key()
        modifiers = event.modifiers()

        # 키 상태 추적
        key_str = self._key_to_string(key, modifiers)
        if key_str not in self.pressed_keys:
            self.pressed_keys.add(key_str)

        # 단축키 처리
        shortcut_str = self._get_shortcut_string(modifiers, key)
        if shortcut_str:
            self._execute_shortcut(shortcut_str)

        # 키 타이머 리셋
        self.key_timer.start(300)  # 300ms 후 키 상태 리셋

    def handle_global_key_release(self, event: QKeyEvent):
        """전역 키보드 해제 이벤트 처리"""
        key = event.key()
        modifiers = event.modifiers()

        key_str = self._key_to_string(key, modifiers)
        self.pressed_keys.discard(key_str)

    def _key_to_string(self, key: int, modifiers: Qt.KeyboardModifier) -> str:
        """키를 문자열로 변환"""
        key_str = ""

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_str += "Ctrl+"
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_str += "Shift+"
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_str += "Alt+"

        # 특수 키 매핑
        special_keys = {
            Qt.Key.Key_Escape: "Escape",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Insert: "Insert",
            Qt.Key.Key_Delete: "Delete",
            Qt.Key.Key_Pause: "Pause",
            Qt.Key.Key_Print: "Print",
            Qt.Key.Key_SysReq: "SysReq",
            Qt.Key.Key_Clear: "Clear",
            Qt.Key.Key_Home: "Home",
            Qt.Key.Key_End: "End",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Right: "Right",
            Qt.Key.Key_Down: "Down",
            Qt.Key.Key_PageUp: "PageUp",
            Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_F1: "F1",
            Qt.Key.Key_F2: "F2",
            Qt.Key.Key_F3: "F3",
            Qt.Key.Key_F4: "F4",
            Qt.Key.Key_F5: "F5",
            Qt.Key.Key_F6: "F6",
            Qt.Key.Key_F7: "F7",
            Qt.Key.Key_F8: "F8",
            Qt.Key.Key_F9: "F9",
            Qt.Key.Key_F10: "F10",
            Qt.Key.Key_F11: "F11",
            Qt.Key.Key_F12: "F12",
        }

        if key in special_keys:
            key_str += special_keys[key]
        else:
            key_str += event.text().upper() if event.text() else f"Key{key}"

        return key_str

    def _get_shortcut_string(self, modifiers: Qt.KeyboardModifier, key: int) -> Optional[str]:
        """단축키 문자열 생성"""
        parts = []

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")

        # 마우스 버튼 처리
        mouse_buttons = {
            Qt.Key.Key_unknown: None,  # 마우스 버튼은 별도 처리
        }

        # 일반 키
        if key >= Qt.Key.Key_A and key <= Qt.Key.Key_Z:
            parts.append(chr(key).upper())
        elif key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9:
            parts.append(chr(key))
        elif key == Qt.Key.Key_Space:
            parts.append("Space")
        elif key >= Qt.Key.Key_F1 and key <= Qt.Key.Key_F12:
            parts.append(f"F{key - Qt.Key.Key_F1 + 1}")
        else:
            # 특수 키들은 처리하지 않음
            return None

        return "+".join(parts) if parts else None

    def _execute_shortcut(self, shortcut_str: str):
        """단축키 실행"""
        shortcuts = self.config.get('shortcuts', {})

        # 설정된 단축키와 매칭
        for action_key, shortcut_value in shortcuts.items():
            if shortcut_value == shortcut_str:
                self._perform_action(action_key)
                break

    def _perform_action(self, action_key: str):
        """액션 수행 (전략 패턴 적용)"""
        logging.info(f"단축키 액션 실행: {action_key}")

        handler = self.action_handlers.get(action_key)
        if handler:
            handler()
        else:
            logging.warning(f"알 수 없는 액션: {action_key}")

    def _handle_toggle_scan(self):
        """스캔 토글 핸들러"""
        if self.manager.control_panel:
            self.manager.control_panel.toggle_scan()

    def _handle_toggle_move(self):
        """이동 모드 토글 핸들러"""
        focused_hud = self._get_focused_hud()
        if focused_hud:
            focused_hud.toggle_move()

    def _handle_style_change(self, style: str):
        """스타일 변경 핸들러"""
        focused_hud = self._get_focused_hud()
        if focused_hud:
            focused_hud.change_style(style)

    def _handle_range(self):
        """레인지 창 열기 핸들러"""
        focused_hud = self._get_focused_hud()
        if focused_hud:
            focused_hud.open_range_window()

    def _handle_delete_player(self):
        """플레이어 삭제 핸들러"""
        focused_hud = self._get_focused_hud()
        if focused_hud:
            focused_hud.delete_player()

    def _get_focused_hud(self):
        """포커스된 HUD 반환"""
        for hud in self.manager.huds:
            if hud.is_focused_hud:
                return hud
        return None

    def _reset_key_state(self):
        """키 상태 리셋"""
        self.pressed_keys.clear()

    def handle_mouse_event(self, event_type: str, button: str, modifiers: Qt.KeyboardModifier):
        """마우스 이벤트 처리"""
        parts = []

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")

        parts.append(button)

        shortcut_str = "+".join(parts)
        self._execute_shortcut(shortcut_str)

    def install_global_hotkeys(self):
        """전역 단축키 설치"""
        try:
            # PyQt6에서는 QApplication.installEventFilter를 사용하여 전역 이벤트 처리
            app = QApplication.instance()
            if app:
                app.installEventFilter(self)
                logging.info("전역 단축키 설치 완료")
        except Exception as e:
            logging.error(f"전역 단축키 설치 실패: {e}")

    def eventFilter(self, obj, event):
        """이벤트 필터"""
        try:
            if event.type() == event.Type.KeyPress:
                self.handle_global_key_press(event)
            elif event.type() == event.Type.KeyRelease:
                self.handle_global_key_release(event)
        except Exception as e:
            logging.error(f"이벤트 필터 오류: {e}")

        return False  # 이벤트를 계속 처리하도록 함
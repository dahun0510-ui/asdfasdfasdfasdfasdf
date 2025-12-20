# === Standard Library Imports ===
import logging
import sys
import os
from typing import Dict, Any, List, Optional

# === Third-Party Imports ===
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QIcon, QAction

# === Local Imports ===
from config import CONFIG_FILE, DB_FILE, DEFAULT_CONFIG
from hud.player_hud import PlayerHUD
from hud.ocr_worker import OCRWorker
from hud.hud_actions import HudActions
from hud.hud_events import HudEvents
from control_panel.control_panel import ControlPanel

class PokerHUDManager(QWidget):
    """포커 HUD 메인 매니저"""

    def __init__(self):
        super().__init__()
        self.config = DEFAULT_CONFIG.copy()
        self.db = {}  # 플레이어 데이터베이스
        self.huds = []  # HUD 위젯들
        self.pos_data = []  # 포지션 데이터
        self.is_scanning = False

        # 컴포넌트 초기화
        self.hud_actions = None
        self.hud_events = None
        self.ocr_worker = None
        self.control_panel = None
        self.tray_icon = None

        self.init_logging()
        self.init_components()
        self.init_tray_icon()
        self.load_data()

    def init_logging(self):
        """로깅 초기화"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('poker_hud.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("Poker HUD 시작")

    def init_components(self):
        """컴포넌트 초기화"""
        # HUD 액션 매니저
        self.hud_actions = HudActions(self)

        # HUD 이벤트 매니저
        self.hud_events = HudEvents(self)

        # OCR 워커
        self.ocr_worker = OCRWorker(self)
        self.ocr_worker.ocr_result.connect(self.on_ocr_result)
        self.ocr_worker.scan_started.connect(self.on_scan_started)
        self.ocr_worker.scan_finished.connect(self.on_scan_finished)
        self.ocr_worker.error_occurred.connect(self.on_ocr_error)

        # 컨트롤 패널
        self.control_panel = ControlPanel(self)
        self.control_panel.scan_toggled.connect(self.toggle_scan)
        self.control_panel.settings_changed.connect(self.on_settings_changed)

        # 포지션 데이터 초기화 (6개 포지션)
        for i in range(6):
            self.pos_data.append({
                'x': 100 + i * 200,
                'y': 300,
                'w': self.config.get('hud_width', 120),
                'h': self.config.get('hud_height', 123)
            })

        # HUD 위젯들 생성
        self.create_huds()

    def create_huds(self):
        """HUD 위젯들 생성"""
        for i in range(6):
            hud = PlayerHUD(
                pos_idx=i,
                x=self.pos_data[i]['x'],
                y=self.pos_data[i]['y'],
                w=self.pos_data[i]['w'],
                h=self.pos_data[i]['h'],
                manager=self,
                config=self.config
            )
            self.huds.append(hud)

    def init_tray_icon(self):
        """트레이 아이콘 초기화"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # 아이콘 설정 (기본 아이콘 사용)
            self.tray_icon.setToolTip("Poker HUD")

            # 트레이 메뉴
            tray_menu = QMenu()

            show_action = QAction("컨트롤 패널 표시", self)
            show_action.triggered.connect(self.show_control_panel)
            tray_menu.addAction(show_action)

            tray_menu.addSeparator()

            scan_action = QAction("스캔 토글", self)
            scan_action.triggered.connect(self.toggle_scan_from_tray)
            tray_menu.addAction(scan_action)

            tray_menu.addSeparator()

            exit_action = QAction("종료", self)
            exit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(exit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def load_data(self):
        """데이터 로드"""
        # 설정 로드
        self.config = self.hud_actions.load_config()

        # 데이터베이스 로드
        self.db = self.hud_actions.load_database()

        logging.info(f"데이터 로드 완료 - 플레이어: {len(self.db)}명")

    def toggle_scan(self, start_scan: bool = None):
        """스캔 토글"""
        if start_scan is None:
            start_scan = not self.is_scanning

        if start_scan and not self.is_scanning:
            self.start_scan()
        elif not start_scan and self.is_scanning:
            self.stop_scan()

    def toggle_scan_from_tray(self):
        """트레이에서 스캔 토글"""
        self.toggle_scan()

    def start_scan(self):
        """스캔 시작"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.ocr_worker.start()
        self.control_panel.update_scan_status(True)

        # 트레이 아이콘 업데이트
        if self.tray_icon:
            self.tray_icon.setToolTip("Poker HUD - 스캔 중")

        logging.info("스캔 시작")

    def stop_scan(self):
        """스캔 중지"""
        if not self.is_scanning:
            return

        self.is_scanning = False
        self.ocr_worker.stop()
        self.control_panel.update_scan_status(False)

        # 트레이 아이콘 업데이트
        if self.tray_icon:
            self.tray_icon.setToolTip("Poker HUD - 중지됨")

        logging.info("스캔 중지")

    def on_scan_started(self):
        """스캔 시작 콜백"""
        pass

    def on_scan_finished(self):
        """스캔 완료 콜백"""
        pass

    def on_ocr_result(self, ocr_data: dict):
        """OCR 결과 처리"""
        try:
            players = ocr_data.get('players', [])

            # 플레이어 수만큼 HUD 업데이트
            for i, player_data in enumerate(players[:6]):  # 최대 6명
                if i < len(self.huds):
                    name = player_data.get('name', f'Player{i+1}')
                    style = self.get_player_style(name)
                    note = self.get_player_note(name)

                    self.huds[i].update_info(name, style, note)

            # 남은 HUD들은 스캔 대기로 설정
            for i in range(len(players), 6):
                if i < len(self.huds):
                    self.huds[i].update_info("스캔 대기", "⚪ Unknown", "")

        except Exception as e:
            logging.error(f"OCR 결과 처리 오류: {e}")

    def on_ocr_error(self, error_msg: str):
        """OCR 오류 처리"""
        logging.error(f"OCR 오류: {error_msg}")
        # 오류 발생 시 스캔 중지
        self.stop_scan()

    def on_settings_changed(self, settings: dict):
        """설정 변경 처리"""
        self.config.update(settings)

        # OCR 워커 설정 업데이트
        if self.ocr_worker:
            ocr_config = {
                'scan_interval': settings.get('scan', {}).get('interval', 1000),
                'max_retries': settings.get('scan', {}).get('retries', 3)
            }
            self.ocr_worker.update_config(ocr_config)

        # HUD 크기 변경 시 HUD들 재생성
        hud_settings = settings.get('hud', {})
        if 'width' in hud_settings or 'height' in hud_settings:
            self.update_hud_sizes()

        logging.info("설정 업데이트됨")

    def update_hud_sizes(self):
        """HUD 크기 업데이트"""
        new_width = self.config.get('hud_width', 120)
        new_height = self.config.get('hud_height', 123)

        for i, hud in enumerate(self.huds):
            # 기존 HUD 삭제
            hud.close()
            hud.deleteLater()

        # 새 HUD들 생성
        self.huds.clear()
        self.create_huds()

        logging.info(f"HUD 크기 업데이트: {new_width}x{new_height}")

    def get_player_style(self, player_id: str) -> str:
        """플레이어 스타일 조회"""
        if player_id in self.db:
            return self.db[player_id].get('style', '⚪ Unknown')
        return '⚪ Unknown'

    def get_player_note(self, player_id: str) -> str:
        """플레이어 메모 조회"""
        if player_id in self.db:
            return self.db[player_id].get('note', '')
        return ''

    def get_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """플레이어 데이터 조회"""
        return self.db.get(player_id)

    def show_control_panel(self):
        """컨트롤 패널 표시"""
        if self.control_panel:
            self.control_panel.show()
            self.control_panel.raise_()
            self.control_panel.activateWindow()

    def quit_application(self):
        """애플리케이션 종료"""
        logging.info("애플리케이션 종료")

        # 스캔 중지
        self.stop_scan()

        # 데이터 저장
        if self.hud_actions:
            self.hud_actions.save_config()
            self.hud_actions.save_database()

        # 트레이 아이콘 제거
        if self.tray_icon:
            self.tray_icon.hide()

        # QApplication 종료
        QApplication.quit()

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 트레이 아이콘으로 최소화
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Poker HUD",
                "프로그램이 트레이로 최소화되었습니다.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            self.quit_application()
            event.accept()


def main():
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("Poker HUD")
    app.setApplicationVersion("3.01")
    app.setOrganizationName("PokerHUD")

    # 메인 매니저 생성
    manager = PokerHUDManager()

    # 컨트롤 패널 표시
    manager.show_control_panel()

    # 이벤트 루프 시작
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
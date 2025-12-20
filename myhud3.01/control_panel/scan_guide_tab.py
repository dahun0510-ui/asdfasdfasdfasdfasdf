# === Third-Party Imports ===
from PyQt6.QtWidgets import QWidget, QVBoxLayout

# === Local Imports ===
from widgets.scan_guide import ScanGuide

class ScanGuideTab(QWidget):
    """스캔 가이드 탭 위젯"""

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager

        self.initUI()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

        # 스캔 가이드 위젯
        self.scan_guide = ScanGuide()
        self.scan_guide.guide_updated.connect(self.on_guide_updated)
        layout.addWidget(self.scan_guide)

    def on_guide_updated(self, guide_data: dict):
        """가이드 업데이트 처리"""
        self.manager.config['scan_guide'] = guide_data
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.save_config()
        # 로깅
        import logging
        logging.info("스캔 가이드 설정이 저장되었습니다.")
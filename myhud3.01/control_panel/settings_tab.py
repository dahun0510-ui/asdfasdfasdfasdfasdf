# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QSpinBox, QCheckBox
)

class SettingsTab(QWidget):
    """설정 탭 위젯"""

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.config = manager.config

        self.initUI()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

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

        self.parent().settings_changed.emit(settings)
        # 상태 표시 (부모에 위임)
        if hasattr(self.parent(), 'status_label'):
            self.parent().status_label.setText("설정이 저장되었습니다.")
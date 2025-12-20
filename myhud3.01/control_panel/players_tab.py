# === Third-Party Imports ===
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QListWidget, QListWidgetItem, QGroupBox
)
from PyQt6.QtCore import Qt

class PlayersTab(QWidget):
    """플레이어 탭 위젯"""

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.config = manager.config
        self.db = manager.db

        self.initUI()

    def initUI(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)

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
        self.player_memo_edit.setPlaceholderText("메모...")
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

    def on_player_selected(self, item: QListWidgetItem):
        """플레이어 선택 처리"""
        player_id = item.text().split(' (')[0]  # 스타일 부분 제거
        self.parent().selected_player = player_id
        self.parent().show_player_detail(player_id)

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
        if not hasattr(self.parent(), 'selected_player') or not self.parent().selected_player or self.parent().selected_player not in self.db:
            self.player_name_label.setText("선택된 플레이어: 없음")
            self.player_style_label.setText("스타일: -")
            self.player_memo_edit.setPlainText("")
            self.stats_label.setText("통계 정보가 없습니다.")
            return

        player_data = self.db[self.parent().selected_player]

        self.player_name_label.setText(f"선택된 플레이어: {self.parent().selected_player}")
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
        if not hasattr(self.parent(), 'selected_player') or not self.parent().selected_player:
            return

        memo = self.player_memo_edit.toPlainText()
        if hasattr(self.manager, 'hud_actions'):
            self.manager.hud_actions.update_player_note(self.parent().selected_player, memo)
# === Standard Library Imports ===
import logging
import json
import os
from typing import Dict, Any, Optional

# === Third-Party Imports ===
from PyQt6.QtWidgets import QMessageBox

# === Local Imports ===
from config import CONFIG_FILE, DB_FILE

class HudActions:
    """HUD 액션 관리 클래스"""

    def __init__(self, manager):
        self.manager = manager
        self.config = manager.config
        self.db = manager.db

    def save_config(self):
        """설정 저장"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logging.info("설정 파일 저장 완료")
        except Exception as e:
            logging.error(f"설정 파일 저장 실패: {e}")
            QMessageBox.critical(None, "오류", f"설정 파일 저장 실패:\n{e}")

    def load_config(self) -> dict:
        """설정 로드"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                logging.info("설정 파일 로드 완료")
                return loaded_config
            else:
                logging.warning("설정 파일이 존재하지 않아 기본 설정 사용")
                return {}
        except Exception as e:
            logging.error(f"설정 파일 로드 실패: {e}")
            QMessageBox.warning(None, "경고", f"설정 파일 로드 실패, 기본 설정 사용:\n{e}")
            return {}

    def save_database(self):
        """데이터베이스 저장"""
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2, ensure_ascii=False)
            logging.info("데이터베이스 저장 완료")
        except Exception as e:
            logging.error(f"데이터베이스 저장 실패: {e}")
            QMessageBox.critical(None, "오류", f"데이터베이스 저장 실패:\n{e}")

    def load_database(self) -> dict:
        """데이터베이스 로드"""
        try:
            if os.path.exists(DB_FILE):
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    loaded_db = json.load(f)
                logging.info("데이터베이스 로드 완료")
                return loaded_db
            else:
                logging.info("데이터베이스 파일이 존재하지 않아 빈 데이터베이스 생성")
                return {}
        except Exception as e:
            logging.error(f"데이터베이스 로드 실패: {e}")
            QMessageBox.warning(None, "경고", f"데이터베이스 로드 실패, 빈 데이터베이스 사용:\n{e}")
            return {}

    def update_player_style(self, player_id: str, style: str):
        """플레이어 스타일 업데이트"""
        if player_id not in self.db:
            self.db[player_id] = {}

        self.db[player_id]['style'] = style
        self.save_database()
        logging.info(f"플레이어 {player_id} 스타일 업데이트: {style}")

        # HUD 업데이트
        for hud in self.manager.huds:
            if hud.player_id == player_id:
                hud.update_info(player_id, style, hud.note)

    def update_player_note(self, player_id: str, note: str):
        """플레이어 메모 업데이트"""
        if player_id not in self.db:
            self.db[player_id] = {}

        self.db[player_id]['note'] = note
        self.save_database()
        logging.info(f"플레이어 {player_id} 메모 업데이트")

        # HUD 업데이트
        for hud in self.manager.huds:
            if hud.player_id == player_id:
                hud.update_info(player_id, hud.style, note)

    def delete_player(self, player_id: str):
        """플레이어 삭제"""
        if player_id in self.db:
            del self.db[player_id]
            self.save_database()
            logging.info(f"플레이어 {player_id} 삭제됨")

            # HUD 초기화
            for hud in self.manager.huds:
                if hud.player_id == player_id:
                    hud.update_info("스캔 대기", "⚪ Unknown", "")

    def get_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """플레이어 데이터 조회"""
        return self.db.get(player_id, {})

    def update_player_range(self, player_id: str, position: str, hand: str, action: str):
        """플레이어 레인지 업데이트"""
        if player_id not in self.db:
            self.db[player_id] = {}

        if 'range' not in self.db[player_id]:
            self.db[player_id]['range'] = {}

        if position not in self.db[player_id]['range']:
            self.db[player_id]['range'][position] = {'hands': {}}

        self.db[player_id]['range'][position]['hands'][hand] = {'action': action}
        self.save_database()
        logging.debug(f"플레이어 {player_id} 레인지 업데이트: {position} {hand} -> {action}")

    def get_player_range(self, player_id: str, position: str) -> Dict[str, Any]:
        """플레이어 레인지 조회"""
        player_data = self.get_player_data(player_id)
        if not player_data or 'range' not in player_data:
            return {}

        return player_data['range'].get(position, {'hands': {}})

    def clear_player_range(self, player_id: str, position: Optional[str] = None):
        """플레이어 레인지 초기화"""
        if player_id not in self.db:
            return

        if position:
            if 'range' in self.db[player_id] and position in self.db[player_id]['range']:
                self.db[player_id]['range'][position] = {'hands': {}}
        else:
            if 'range' in self.db[player_id]:
                self.db[player_id]['range'] = {}

        self.save_database()
        logging.info(f"플레이어 {player_id} 레인지 초기화: {position or '전체'}")

    def export_data(self, filepath: str):
        """데이터 내보내기"""
        try:
            export_data = {
                'config': self.config,
                'database': self.db,
                'timestamp': __import__('time').time()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logging.info(f"데이터 내보내기 완료: {filepath}")
            QMessageBox.information(None, "완료", f"데이터가 성공적으로 내보내졌습니다:\n{filepath}")

        except Exception as e:
            logging.error(f"데이터 내보내기 실패: {e}")
            QMessageBox.critical(None, "오류", f"데이터 내보내기 실패:\n{e}")

    def import_data(self, filepath: str):
        """데이터 가져오기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if 'config' in import_data:
                self.config.update(import_data['config'])
                self.save_config()

            if 'database' in import_data:
                self.db.update(import_data['database'])
                self.save_database()

            logging.info(f"데이터 가져오기 완료: {filepath}")
            QMessageBox.information(None, "완료", f"데이터가 성공적으로 가져와졌습니다:\n{filepath}")

        except Exception as e:
            logging.error(f"데이터 가져오기 실패: {e}")
            QMessageBox.critical(None, "오류", f"데이터 가져오기 실패:\n{e}")

    def reset_all_data(self):
        """모든 데이터 초기화"""
        reply = QMessageBox.question(
            None, "확인",
            "모든 플레이어 데이터와 설정을 초기화하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear()
            self.config = {}  # 기본 설정으로 초기화
            self.save_database()
            self.save_config()

            # 모든 HUD 초기화
            for hud in self.manager.huds:
                hud.update_info("스캔 대기", "⚪ Unknown", "")

            logging.info("모든 데이터 초기화 완료")
            QMessageBox.information(None, "완료", "모든 데이터가 초기화되었습니다.")
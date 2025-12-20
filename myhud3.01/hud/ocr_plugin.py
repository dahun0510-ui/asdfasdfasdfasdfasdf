# === Standard Library Imports ===
from typing import Dict, Any, Optional
import logging
import time
import threading

# === Third-Party Imports ===
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage

# === Local Imports ===
from interfaces import IPlugin
from hud.ocr_worker import OCRWorker
from data_flow_manager import DataFlowManager
from config import OCR_CONFIG

class OCRPlugin(IPlugin):
    """OCR 플러그인 구현"""

    def __init__(self):
        self.name = "OCR Plugin"
        self.version = "1.0.0"
        self.description = "OCR 스캔 플러그인"
        self.is_running = False
        self.data_flow_manager: Optional[DataFlowManager] = None
        self.ocr_worker: Optional[OCRWorker] = None
        self.scan_timer: Optional[QTimer] = None

    def get_name(self) -> str:
        return self.name

    def get_version(self) -> str:
        return self.version

    def get_description(self) -> str:
        return self.description

    def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            self.data_flow_manager = config.get('data_flow_manager')
            if not self.data_flow_manager:
                logging.error("DataFlowManager not provided in config")
                return False

            # OCR 워커 생성
            self.ocr_worker = OCRWorker(self.data_flow_manager)

            # 시그널 연결
            self.ocr_worker.ocr_result.connect(self._on_ocr_result)
            self.ocr_worker.scan_started.connect(self._on_scan_started)
            self.ocr_worker.scan_finished.connect(self._on_scan_finished)
            self.ocr_worker.error_occurred.connect(self._on_error_occurred)

            # 이벤트 구독
            event_bus = self.data_flow_manager.get_event_bus()
            event_bus.subscribe("scan_request", self._on_scan_request)

            logging.info(f"{self.get_name()} initialized")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize {self.get_name()}: {e}")
            return False

    def start(self) -> bool:
        if not self.ocr_worker:
            return False

        try:
            self.is_running = True

            # OCR 워커 시작
            self.ocr_worker.start()

            # 스캔 타이머 설정
            self.scan_timer = QTimer()
            self.scan_timer.timeout.connect(self._perform_scan)
            scan_interval = OCR_CONFIG.get('scan_interval', 1000)
            self.scan_timer.start(scan_interval)

            logging.info(f"{self.get_name()} started")
            return True
        except Exception as e:
            logging.error(f"Failed to start {self.get_name()}: {e}")
            return False

    def stop(self) -> bool:
        try:
            self.is_running = False

            # 스캔 타이머 중지
            if self.scan_timer:
                self.scan_timer.stop()
                self.scan_timer = None

            # OCR 워커 중지
            if self.ocr_worker:
                self.ocr_worker.is_running = False
                self.ocr_worker.wait(3000)  # 3초 대기

            logging.info(f"{self.get_name()} stopped")
            return True
        except Exception as e:
            logging.error(f"Failed to stop {self.get_name()}: {e}")
            return False

    def shutdown(self) -> bool:
        try:
            self.stop()

            # OCR 워커 정리
            if self.ocr_worker:
                self.ocr_worker = None

            self.data_flow_manager = None
            logging.info(f"{self.get_name()} shutdown")
            return True
        except Exception as e:
            logging.error(f"Failed to shutdown {self.get_name()}: {e}")
            return False

    def is_active(self) -> bool:
        return self.is_running

    def perform_scan(self) -> bool:
        """수동 스캔 수행"""
        try:
            if not self.is_running or not self.ocr_worker:
                return False

            self._perform_scan()
            return True
        except Exception as e:
            logging.error(f"Failed to perform manual scan: {e}")
            return False

    def get_scan_status(self) -> Dict[str, Any]:
        """스캔 상태 정보"""
        return {
            "is_running": self.is_running,
            "worker_active": self.ocr_worker.isRunning() if self.ocr_worker else False,
            "scan_interval": self.scan_timer.interval() if self.scan_timer else 0
        }

    def _perform_scan(self):
        """스캔 수행"""
        try:
            if not self.is_running or not self.ocr_worker:
                return

            # 실제 스캔 로직은 OCRWorker에서 처리
            # 여기서는 이벤트로 스캔 요청
            event_bus = self.data_flow_manager.get_event_bus()
            event_bus.publish({
                "event_type": "scan_request",
                "data": {"timestamp": time.time()},
                "source": "ocr_plugin"
            })

        except Exception as e:
            logging.error(f"Error during scan: {e}")

    def _on_ocr_result(self, result: dict):
        """OCR 결과 처리"""
        try:
            # 결과를 데이터 플로우로 전송
            if self.data_flow_manager:
                # 비동기로 처리
                import asyncio
                asyncio.create_task(
                    self.data_flow_manager.process_player_data(
                        result.get("player_id", "unknown"), result
                    )
                )
        except Exception as e:
            logging.error(f"Error processing OCR result: {e}")

    def _on_scan_started(self):
        """스캔 시작 처리"""
        logging.debug("Scan started")

    def _on_scan_finished(self):
        """스캔 완료 처리"""
        logging.debug("Scan finished")

    def _on_error_occurred(self, error_msg: str):
        """오류 처리"""
        logging.error(f"OCR error: {error_msg}")

        # 오류 이벤트를 데이터 플로우로 전송
        if self.data_flow_manager:
            event_bus = self.data_flow_manager.get_event_bus()
            event_bus.publish({
                "event_type": "error_occurred",
                "data": {"error": error_msg, "source": "ocr_plugin"},
                "source": "ocr_plugin"
            })

    def _on_scan_request(self, event):
        """스캔 요청 처리"""
        try:
            # 실제 OCR 스캔 수행
            if self.ocr_worker and self.is_running:
                # OCRWorker의 스캔 메서드 호출 (실제 구현 필요)
                pass
        except Exception as e:
            logging.error(f"Error handling scan request: {e}")
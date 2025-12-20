import logging
import sys

class LoggerManager:
    @staticmethod
    def init_logging():
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
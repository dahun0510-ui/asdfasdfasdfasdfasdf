# === Standard Library Imports ===
import json
import logging
import os

# === Constants ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "player_data.json")
POS_FILE = os.path.join(SCRIPT_DIR, "hud_positions.json")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "hud_config.json")

# === Default Configuration ===
DEFAULT_CONFIG = {
    'scan_interval_ms': 20000,
    'use_gpu': False,
    'enable_logging': True,
    'hud_width': 120,
    'hud_height': 119,
    'auto_save_interval': 300000,
    'max_memo_lines': 3,
    'theme': 'dark',
    'shortcuts': {
        'fish': '1',
        'tag': '2',
        'nit': '3',
        'lag': '4',
        'maniac': '5',
        'weird': '6',
        'unknown': '7',
        'toggle_move': 'L',
        'range': 'R',
        'toggle_scan': 'Space'
    }
}

class ConfigManager:
    @staticmethod
    def load_config() -> dict:
        config_path = os.path.abspath(CONFIG_FILE)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    merged = {**DEFAULT_CONFIG, **config}
                    logging.info(f"Config loaded from {config_path}: shortcuts={merged.get('shortcuts', {})}")
                    return merged
            except (IOError, OSError) as e:
                logging.error(f"Config file read error: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"Config file parse error: {e}")
            except Exception as e:
                logging.error(f"Unexpected config load error: {e}")
        else:
            logging.info(f"Config file not found at {config_path}, using defaults")
        return DEFAULT_CONFIG.copy()

    @staticmethod
    def save_config(config: dict) -> bool:
        """Config 저장 (성공 여부 반환)"""
        try:
            config_path = os.path.abspath(CONFIG_FILE)
            # JSON 직렬화 사전 검증
            json.dumps(config)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logging.info(f"Config saved to {config_path}: shortcuts={config.get('shortcuts', {})}")
            return True
        except (IOError, OSError) as e:
            logging.error(f"Config file write error: {e}", exc_info=True)
            return False
        except (TypeError, ValueError) as e:
            logging.error(f"Config serialization error: {e}", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"Unexpected config save error: {e}", exc_info=True)
            return False

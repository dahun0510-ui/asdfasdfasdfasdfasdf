#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Poker HUD 3.01 메인 실행 파일
OBS 아키텍처 기반 통합 포커 HUD 시스템

이 모듈은 포커 HUD 애플리케이션의 메인 엔트리 포인트를 제공합니다.
디자인 패턴(Factory, Observer, Strategy)을 활용한 모듈식 아키텍처를 구현합니다.
"""

# === Standard Library Imports ===
import sys
import os
import signal
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 프로젝트 루트 경로 추가 (core 폴더의 부모 디렉토리)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# === Local Imports ===
from plugins.plugin_factory import PluginFactory
from plugins.plugin_registry import PluginRegistry
from plugins.plugin_loader import PluginLoader
from plugins.plugin_lifecycle_manager import PluginLifecycleManager
from plugins.interfaces import IManager
from plugins.poker_types import ComponentType, ComponentConfig, Result, HealthStatus

# === Mock Components for Testing ===
class MockDataFlowManager:
    """테스트용 모의 데이터 플로우 관리자"""

    def __init__(self):
        self._running = False

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        print("MockDataFlowManager 초기화")
        return Result.ok(True)

    async def start(self) -> Result[bool, str]:
        print("MockDataFlowManager 시작")
        self._running = True
        return Result.ok(True)

    async def stop(self) -> Result[bool, str]:
        print("MockDataFlowManager 중지")
        self._running = False
        return Result.ok(True)

    async def shutdown(self) -> Result[bool, str]:
        print("MockDataFlowManager 종료")
        return Result.ok(True)

    def get_stats(self) -> dict:
        return {"status": "mock", "running": self._running}

# 플러그인 임포트 (GUI 모드에서만 사용)
try:
    GUI_AVAILABLE = True
    from hud.hud_plugin import HUDPlugin
    from hud.ocr_plugin import OCRPlugin
    from hud.data_store_plugin import DataStorePlugin
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ GUI 컴포넌트를 사용할 수 없습니다 (PyQt6 미설치 또는 디스플레이 없음)")
    HUDPlugin = None
    OCRPlugin = None
    DataStorePlugin = None

# DataFlowManager 설정
if GUI_AVAILABLE:
    try:
        from core.data_flow_manager import DataFlowManager
    except ImportError:
        DataFlowManager = MockDataFlowManager
        print("⚠️ 실제 DataFlowManager를 찾을 수 없어 Mock을 사용합니다")
else:
    DataFlowManager = MockDataFlowManager

# PluginManager 설정
try:
    from plugins.plugin_manager import PluginManager
    print("✅ 실제 PluginManager를 사용합니다")
except ImportError:
    class MockPluginManager:
        """테스트용 모의 플러그인 관리자"""

        def __init__(self):
            self._running = False

        async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
            print("MockPluginManager 초기화")
            return Result.ok(True)

        async def start(self) -> Result[bool, str]:
            print("MockPluginManager 시작")
            self._running = True
            return Result.ok(True)

        async def stop(self) -> Result[bool, str]:
            print("MockPluginManager 중지")
            self._running = False
            return Result.ok(True)

        async def shutdown(self) -> Result[bool, str]:
            print("MockPluginManager 종료")
            return Result.ok(True)

        def get_loaded_plugins(self) -> dict:
            return {"mock_plugin": "loaded"}

    PluginManager = MockPluginManager
    print("⚠️ 실제 PluginManager를 찾을 수 없어 Mock을 사용합니다")

# === Automatic Issue Resolution ===
async def auto_fix_issues():
    """자동으로 알려진 문제를 해결합니다."""
    import sys
    import os
    import shutil
    from pathlib import Path

    print("🔧 자동 문제 해결 중...")

    # 1. Python 캐시 정리
    project_root = Path(__file__).parent.parent
    cache_dirs = []

    for root, dirs, files in os.walk(project_root):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))

    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ 캐시 삭제: {cache_dir}")
        except:
            pass

    # 2. .pyc 파일 삭제
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print(f"✅ .pyc 파일 삭제: {file}")
                except:
                    pass

    # 3. ComponentConfig 테스트
    try:
        from plugins.poker_types import ComponentConfig, ComponentType
        test_config = ComponentConfig(
            name="Test Component",
            type=ComponentType.HUD_CORE
        )
        print(f"✅ ComponentConfig 테스트 성공 (id: {test_config.id})")
    except Exception as e:
        print(f"❌ ComponentConfig 테스트 실패: {e}")
        return

    print("🎉 자동 문제 해결 완료!")
    print()

# === Default Configuration ===
DEFAULT_CONFIG = {
    "plugin_dir": "plugins",
    "cache_enabled": True,
    "max_plugins": 10,
    "scan_interval": 1000,  # ms
    "debug_mode": False,
    "log_level": "INFO"
}

# 플러그인 임포트 (GUI 모드에서만 사용)
try:
    GUI_AVAILABLE = True
    from hud.hud_plugin import HUDPlugin
    from hud.ocr_plugin import OCRPlugin
    from hud.data_store_plugin import DataStorePlugin
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ GUI 컴포넌트를 사용할 수 없습니다 (PyQt6 미설치 또는 디스플레이 없음)")
    HUDPlugin = None
    OCRPlugin = None
    DataStorePlugin = None

class PokerHUDApplication(IManager):
    """
    포커 HUD 메인 애플리케이션 클래스

    이 클래스는 전체 포커 HUD 시스템의 중앙 컨트롤러 역할을 수행합니다.
    플러그인 관리자와 데이터 플로우 관리자를 통합하여 시스템을 조율합니다.

    Attributes:
        _plugin_manager: 플러그인 생명주기 관리
        _data_flow_manager: 데이터 흐름 및 이벤트 처리 관리
        _config: 애플리케이션 설정
        _running: 애플리케이션 실행 상태
    """

    def __init__(self) -> None:
        """PokerHUDApplication 초기화"""
        self._data_flow_manager: Optional[DataFlowManager] = None
        self._plugin_factory: Optional[PluginFactory] = None
        self._plugin_registry: Optional[PluginRegistry] = None
        self._plugin_loader: Optional[PluginLoader] = None
        self._lifecycle_manager: Optional[PluginLifecycleManager] = None
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._running = False

        # 로깅 설정 (한 번만 수행)
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        self.logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """애플리케이션 이름"""
        return "Poker HUD Application"

    @property
    def version(self) -> str:
        """애플리케이션 버전"""
        return "3.01"

    def initialize(self, config: Dict[str, Any]) -> bool:
        """애플리케이션 초기화"""
        try:
            # 입력 유효성 검사
            if not isinstance(config, dict):
                self.logger.error("Invalid config type: expected dict")
                return False

            self.logger.info("Initializing Poker HUD Application...")

            # 설정 업데이트 (안전하게)
            safe_config = {k: v for k, v in config.items() if isinstance(k, str)}
            self._config.update(safe_config)

            # 데이터 플로우 관리자 초기화
            self._data_flow_manager = DataFlowManager()
            df_config = {
                'cache_enabled': self._config.get('cache_enabled', True)
            }
            if not self._data_flow_manager.initialize(df_config):
                self.logger.error("Failed to initialize DataFlowManager")
                return False

            # 플러그인 시스템 초기화
            self._plugin_factory = PluginFactory()
            self._plugin_registry = PluginRegistry()
            self._plugin_loader = PluginLoader(self._plugin_registry)
            self._lifecycle_manager = PluginLifecycleManager(self._plugin_loader)

            # 플러그인 등록
            self._register_plugins()

            # 생명주기 관리자 초기화
            plugin_configs = self._get_plugin_configs()
            if not self._lifecycle_manager.initialize_plugins(plugin_configs):
                self.logger.error("Failed to initialize plugin lifecycle manager")
                return False

            self.logger.info("Poker HUD Application initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False

    def start(self) -> bool:
        """애플리케이션 시작"""
        try:
            if self._running:
                return True

            self.logger.info("Starting Poker HUD Application...")

            # 데이터 플로우 관리자 시작
            if not self._data_flow_manager.start():
                self.logger.error("Failed to start DataFlowManager")
                return False

            # 플러그인 생명주기 시작
            if not self._lifecycle_manager.start_plugins():
                self.logger.error("Failed to start plugins")
                return False

            self._running = True
            self.logger.info("Poker HUD Application started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start application: {e}")
            return False

    def stop(self) -> bool:
        """애플리케이션 중지"""
        try:
            if not self._running:
                return True

            self.logger.info("Stopping Poker HUD Application...")

            self._running = False

            # 플러그인 생명주기 중지
            if self._lifecycle_manager:
                self._lifecycle_manager.stop_plugins()

            # 데이터 플로우 관리자 중지
            if self._data_flow_manager:
                self._data_flow_manager.stop()

            self.logger.info("Poker HUD Application stopped successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop application: {e}")
            return False

    def shutdown(self) -> bool:
        """애플리케이션 종료"""
        try:
            self.logger.info("Shutting down Poker HUD Application...")

            self.stop()

            # 플러그인 생명주기 종료
            if self._lifecycle_manager:
                self._lifecycle_manager.shutdown_plugins()

            # 데이터 플로우 관리자 종료
            if self._data_flow_manager:
                self._data_flow_manager.shutdown()

            self.logger.info("Poker HUD Application shutdown successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to shutdown application: {e}")
            return False

    def _register_plugins(self):
        """플러그인 등록"""
        try:
            # 플러그인 클래스 등록
            self._plugin_factory.register_plugin_class('hud_plugin', HUDPlugin)
            self._plugin_factory.register_plugin_class('ocr_plugin', OCRPlugin)
            self._plugin_factory.register_plugin_class('data_store_plugin', DataStorePlugin)

            # 팩토리 등록
            self._plugin_registry.register_factory('hud_plugin', self._plugin_factory)
            self._plugin_registry.register_factory('ocr_plugin', self._plugin_factory)
            self._plugin_registry.register_factory('data_store_plugin', self._plugin_factory)

            self.logger.info("Plugin classes registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register plugins: {e}")

    def _get_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """플러그인 설정 반환"""
        return {
            'hud_plugin': {
                'enabled': True,
                'priority': 1,
                'data_flow_manager': self._data_flow_manager
            },
            'ocr_plugin': {
                'enabled': True,
                'priority': 2,
                'data_flow_manager': self._data_flow_manager
            },
            'data_store_plugin': {
                'enabled': True,
                'priority': 3,
                'data_flow_manager': self._data_flow_manager
            }
        }

    def get_component(self, component_type: str) -> Optional[Any]:
        """컴포넌트 조회"""
        if component_type == 'plugin_manager':
            return self._plugin_manager
        elif component_type == 'data_flow_manager':
            return self._data_flow_manager
        elif component_type in self._plugins:
            return self._plugins[component_type]
        return None

    def get_status(self) -> Dict[str, Any]:
        """애플리케이션 상태 반환"""
        return {
            'running': self._running,
            'version': self.version,
            'plugins': list(self._plugins.keys()),
            'data_flow_stats': self._data_flow_manager.get_stats() if self._data_flow_manager else {},
            'plugin_stats': {
                'loaded': len(self._plugin_manager.get_active_plugins()) if self._plugin_manager else 0,
                'total': len(self._plugins)
            }
        }
        self._health_status = HealthStatus.HEALTHY

    @property
    def name(self) -> str:
        return "Poker HUD Application"

    @property
    def version(self) -> str:
        return "3.01"

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.DATA_FLOW  # 메인 애플리케이션은 데이터 플로우 타입

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """애플리케이션 초기화"""
        try:
            print("=== Poker HUD Application Initializing ===")

            # 설정 로드
            self._config = self._load_config()
            self._config.update(config.settings)  # 추가 설정 병합

            # 데이터 플로우 관리자 초기화
            self._data_flow_manager = DataFlowManager()
            df_config = ComponentConfig(
                name="Data Flow Manager",
                type=ComponentType.EVENT_BUS,
                settings={"cache_enabled": self._config.get("cache_enabled", True)}
            )
            df_result = await self._data_flow_manager.initialize(df_config)
            if not df_result.success:
                self._health_status = HealthStatus.UNHEALTHY
                return Result.err(f"Failed to initialize DataFlowManager: {df_result.error}")

            # 플러그인 관리자 초기화
            self._plugin_manager = PluginManager()
            pm_config = ComponentConfig(
                name="Plugin Manager",
                type=ComponentType.PLUGIN_MANAGER,
                settings={
                    "plugin_dir": self._config.get("plugin_dir", "plugins"),
                    "plugin_configs": self._get_plugin_configs()
                }
            )
            pm_result = await self._plugin_manager.initialize(pm_config)
            if not pm_result.success:
                self._health_status = HealthStatus.UNHEALTHY
                return Result.err(f"Failed to initialize PluginManager: {pm_result.error}")

            print("=== Poker HUD Application Initialized ===")
            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)

        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to initialize application: {str(e)}")

    async def start(self) -> Result[bool, str]:
        """애플리케이션 시작"""
        try:
            print("=== Poker HUD Application Starting ===")

            if self._running:
                return Result.ok(True)

            # 데이터 플로우 관리자 시작
            if self._data_flow_manager:
                df_result = await self._data_flow_manager.start()
                if not df_result.success:
                    return Result.err(f"Failed to start DataFlowManager: {df_result.error}")

            # 플러그인 관리자 시작
            if self._plugin_manager:
                pm_result = await self._plugin_manager.start()
                if not pm_result.success:
                    return Result.err(f"Failed to start PluginManager: {pm_result.error}")

            self._running = True
            print("=== Poker HUD Application Started ===")
            return Result.ok(True)

        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to start application: {str(e)}")

    async def stop(self) -> Result[bool, str]:
        """애플리케이션 중지"""
        try:
            print("=== Poker HUD Application Stopping ===")

            if not self._running:
                return Result.ok(True)

            self._running = False

            # 플러그인 관리자 중지
            if self._plugin_manager:
                pm_result = await self._plugin_manager.stop()
                if not pm_result.success:
                    print(f"Warning: Failed to stop PluginManager: {pm_result.error}")

            # 데이터 플로우 관리자 중지
            if self._data_flow_manager:
                df_result = await self._data_flow_manager.stop()
                if not df_result.success:
                    print(f"Warning: Failed to stop DataFlowManager: {df_result.error}")

            print("=== Poker HUD Application Stopped ===")
            self._health_status = HealthStatus.DEGRADED
            return Result.ok(True)

        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to stop application: {str(e)}")

    async def shutdown(self) -> Result[bool, str]:
        """애플리케이션 종료"""
        try:
            print("=== Poker HUD Application Shutting Down ===")

            stop_result = await self.stop()
            if not stop_result.success:
                print(f"Warning: Failed to stop application: {stop_result.error}")

            # 컴포넌트 정리
            if self._plugin_manager:
                pm_result = await self._plugin_manager.shutdown()
                if not pm_result.success:
                    print(f"Warning: Failed to shutdown PluginManager: {pm_result.error}")
                self._plugin_manager = None

            if self._data_flow_manager:
                df_result = await self._data_flow_manager.shutdown()
                if not df_result.success:
                    print(f"Warning: Failed to shutdown DataFlowManager: {df_result.error}")
                self._data_flow_manager = None

            print("=== Poker HUD Application Shutdown Complete ===")
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)

        except Exception as e:
            return Result.err(f"Failed to shutdown application: {str(e)}")

    def get_component(self, component_type: ComponentType):
        """컴포넌트 조회"""
        try:
            if component_type == ComponentType.PLUGIN_MANAGER:
                return self._plugin_manager
            elif component_type == ComponentType.DATA_FLOW:
                return self._data_flow_manager
            else:
                return None
        except Exception as e:
            print(f"Failed to get component {component_type}: {e}")
            return None

    async def start_application(self) -> Result[bool, str]:
        """애플리케이션 시작 (IManager 인터페이스)"""
        return await self.start()

    async def stop_application(self) -> Result[bool, str]:
        """애플리케이션 중지 (IManager 인터페이스)"""
        return await self.stop()

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        try:
            config_path = Path(__file__).parent / "config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 기본 설정 반환
                return {
                    "cache_enabled": True,
                    "plugin_dir": "plugins",
                    "scan_interval": 1000,
                    "hud_width": 120,
                    "hud_height": 123
                }
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}

    def _get_plugin_configs(self) -> Dict[str, Any]:
        """플러그인 설정 생성"""
        try:
            plugin_configs = {}

            # Player HUD 플러그인 설정
            plugin_configs["player_hud_plugin"] = ComponentConfig(
                id="player_hud_plugin",
                settings={
                    "manager": self,
                    "hud_width": self._config.get("hud_width", 120),
                    "hud_height": self._config.get("hud_height", 123),
                    "task_queue": self._data_flow_manager._data_flow_system._task_queue
                }
            )

            # OCR 플러그인 설정
            plugin_configs["ocr_plugin"] = ComponentConfig(
                id="ocr_plugin",
                settings={
                    "data_flow_manager": self._data_flow_manager,
                    "manager": self,
                    "scan_interval": self._config.get("scan_interval", 1000),
                    "task_queue": self._data_flow_manager._data_flow_system._task_queue
                }
            )

            # HUD 플러그인 설정
            plugin_configs["hud_plugin"] = ComponentConfig(
                id="hud_plugin",
                settings={
                    "scanner": None,  # OCR 플러그인에서 제공
                    "display": None,  # Player HUD 플러그인에서 제공
                    "data_flow_manager": self._data_flow_manager
                }
            )

            # 데이터 저장소 플러그인 설정
            plugin_configs["data_store_plugin"] = ComponentConfig(
                id="data_store_plugin",
                settings={
                    "data_store": None,  # 실제 데이터 저장소 구현 필요
                    "data_flow_manager": self._data_flow_manager
                }
            )

            return plugin_configs

        except Exception as e:
            print(f"Failed to get plugin configs: {str(e)}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        """애플리케이션 상태 조회"""
        try:
            return {
                "running": self._running,
                "version": self.version,
                "data_flow_stats": self._data_flow_manager.get_stats() if self._data_flow_manager else {},
                "active_plugins": list(self._plugin_manager.get_loaded_plugins().keys()) if self._plugin_manager else [],
                "health_status": self._health_status.value
            }
        except Exception as e:
            print(f"Failed to get status: {e}")
            return {"error": str(e)}

    async def reload_plugin(self, plugin_name: str) -> Result[bool, str]:
        """플러그인 리로드"""
        try:
            if self._plugin_manager:
                return await self._plugin_manager.reload_plugin(plugin_name)
            return Result.err("PluginManager not available")
        except Exception as e:
            return Result.err(f"Failed to reload plugin {plugin_name}: {str(e)}")

    async def run(self):
        """메인 이벤트 루프 실행 (비동기)"""
        try:
            print("=== Poker HUD Application Running ===")
            print("📊 실시간 모니터링 모드")
            print("💡 명령어:")
            print("   'status' - 현재 상태 확인")
            print("   'plugins' - 플러그인 목록")
            print("   'stop' - 애플리케이션 중지")
            print("   Ctrl+C - 강제 종료")
            print("-" * 50)

            # 시그널 핸들러 설정
            def signal_handler():
                print("\n🛑 Shutdown requested by user")
                import asyncio
                asyncio.create_task(self.stop())

            signal.signal(signal.SIGINT, lambda s, f: signal_handler())
            signal.signal(signal.SIGTERM, lambda s, f: signal_handler())

            # 초기 상태 표시
            await self._monitor_system()

            # 메인 루프
            while self._running:
                try:
                    # 사용자 입력 대기 (비동기)
                    import asyncio
                    import sys

                    if sys.platform != 'win32':
                        # Unix-like 시스템에서만 입력 대기
                        import select
                        import tty
                        import termios

                        # 터미널 설정 저장
                        old_settings = termios.tcgetattr(sys.stdin)

                        try:
                            tty.setcbreak(sys.stdin.fileno())

                            # 1초 동안 입력 확인
                            if select.select([sys.stdin], [], [], 1.0)[0]:
                                char = sys.stdin.read(1)
                                if char == 's':
                                    await self._show_status()
                                elif char == 'p':
                                    await self._show_plugins()
                                elif char == '\x03':  # Ctrl+C
                                    break
                        finally:
                            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    else:
                        # Windows에서는 간단히 대기
                        await asyncio.sleep(5)
                        await self._monitor_system()

                except Exception as e:
                    print(f"⚠️ 입력 처리 에러: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            print(f"❌ 메인 루프 에러: {e}")
        finally:
            await self.stop()

    async def _monitor_system(self):
        """시스템 상태 모니터링"""
        try:
            status = self.get_status()
            print(f"📈 상태: {status.get('health_status', 'unknown')} | "
                  f"실행: {status.get('running', False)} | "
                  f"플러그인: {len(status.get('active_plugins', []))}")

        except Exception as e:
            print(f"⚠️ 모니터링 에러: {e}")

    async def _show_status(self):
        """상세 상태 표시"""
        try:
            status = self.get_status()
            print("\n" + "="*50)
            print("📊 시스템 상태")
            print("="*50)
            print(f"실행 상태: {status.get('running', False)}")
            print(f"건강 상태: {status.get('health_status', 'unknown')}")
            print(f"버전: {status.get('version', 'unknown')}")
            print(f"활성 플러그인: {len(status.get('active_plugins', []))}")

            if 'data_flow_stats' in status:
                dfs = status['data_flow_stats']
                print(f"데이터 플로우 - 상태: {dfs.get('state_count', 0)}, "
                      f"캐시: {dfs.get('cache_size', 0)}")
            print("="*50 + "\n")

        except Exception as e:
            print(f"⚠️ 상태 조회 에러: {e}")

    async def _show_plugins(self):
        """플러그인 목록 표시"""
        try:
            status = self.get_status()
            plugins = status.get('active_plugins', [])
            print("\n" + "="*50)
            print("🔌 활성 플러그인")
            print("="*50)
            if plugins:
                for i, plugin in enumerate(plugins, 1):
                    print(f"{i}. {plugin}")
            else:
                print("활성 플러그인이 없습니다.")
            print("="*50 + "\n")

        except Exception as e:
            print(f"⚠️ 플러그인 조회 에러: {e}")

    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (레거시)"""
        print(f"\nReceived signal {signum}")
        self._running = False

async def main():
    """메인 함수 (비동기)"""
    import argparse

    # 자동 문제 해결
    await auto_fix_issues()

    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Poker HUD Application')
    parser.add_argument('--console', action='store_true',
                       help='Run in console mode (no GUI)')
    parser.add_argument('--test', action='store_true',
                       help='Run quick test mode')

    args = parser.parse_args()

    # 테스트 모드
    if args.test:
        print("=== Poker HUD Quick Test ===")
        app = PokerHUDApplication()

        try:
            # 간단한 초기화 테스트
            init_config = ComponentConfig(
                name="Poker HUD Application",
                type=ComponentType.HUD_CORE,
                settings={}
            )
            init_result = await app.initialize(init_config)
            if not init_result.success:
                print(f"❌ 초기화 실패: {init_result.error}")
                return 1

            print("✅ 초기화 성공")

            # 시작 테스트
            start_result = await app.start()
            if not start_result.success:
                print(f"❌ 시작 실패: {start_result.error}")
                return 1

            print("✅ 시작 성공")

            # 잠시 실행 후 중지
            import asyncio
            await asyncio.sleep(2)

            stop_result = await app.stop()
            if not stop_result.success:
                print(f"⚠️ 중지 경고: {stop_result.error}")

            print("✅ 테스트 완료")
            return 0

        except Exception as e:
            print(f"❌ 테스트 에러: {e}")
            return 1
        finally:
            shutdown_result = await app.shutdown()
            if not shutdown_result.success:
                print(f"⚠️ 종료 경고: {shutdown_result.error}")

    # 콘솔 모드
    elif args.console:
        print("=== Poker HUD Console Mode ===")
        print("GUI 없이 콘솔에서 실행합니다.")
        app = PokerHUDApplication()

        try:
            # 초기화
            init_config = ComponentConfig(
                name="Poker HUD Application",
                type=ComponentType.HUD_CORE,
                settings={}
            )
            init_result = await app.initialize(init_config)
            if not init_result.success:
                print(f"❌ 초기화 실패: {init_result.error}")
                return 1

            print("✅ 초기화 성공")

            # 시작
            start_result = await app.start()
            if not start_result.success:
                print(f"❌ 시작 실패: {start_result.error}")
                return 1

            print("✅ 시작 성공")
            print("실행 중... Ctrl+C로 중지")

            # 실행 (간단한 모니터링)
            while app._running:
                status = app.get_status()
                print(f"상태: {status.get('health_status', 'unknown')}, "
                      f"실행중: {status.get('running', False)}")
                await asyncio.sleep(5)

            return 0

        except KeyboardInterrupt:
            print("\n사용자에 의해 중지됨")
            return 0
        except Exception as e:
            print(f"❌ 실행 에러: {e}")
            return 1
        finally:
            shutdown_result = await app.shutdown()
            if not shutdown_result.success:
                print(f"⚠️ 종료 경고: {shutdown_result.error}")

    # GUI 모드 (기본)
    else:
        print("=== Poker HUD GUI Mode ===")

        # GUI가 실제로 사용 가능한지 확인
        if not GUI_AVAILABLE:
            print("⚠️ GUI 컴포넌트를 사용할 수 없어 콘솔 모드로 자동 전환합니다.")
            print("GUI 모드로 실행하려면 PyQt6을 설치하세요: pip install PyQt6")
            print()

            # 콘솔 모드로 전환
            app = PokerHUDApplication()

            try:
                # 초기화
                init_config = ComponentConfig(
                    name="Poker HUD Application",
                    type=ComponentType.HUD_CORE,
                    settings={}
                )
                init_result = await app.initialize(init_config)
                if not init_result.success:
                    print(f"❌ 초기화 실패: {init_result.error}")
                    return 1

                print("✅ 초기화 성공")

                # 시작
                start_result = await app.start()
                if not start_result.success:
                    print(f"❌ 시작 실패: {start_result.error}")
                    return 1

                print("✅ 시작 성공")
                print("실행 중... Ctrl+C로 중지")

                # 실행 (간단한 모니터링)
                while app._running:
                    status = app.get_status()
                    print(f"상태: {status.get('health_status', 'unknown')}, "
                          f"실행중: {status.get('running', False)}")
                    await asyncio.sleep(5)

                return 0

            except KeyboardInterrupt:
                print("\n사용자에 의해 중지됨")
                return 0
            except Exception as e:
                print(f"❌ 실행 에러: {e}")
                return 1
            finally:
                shutdown_result = await app.shutdown()
                if not shutdown_result.success:
                    print(f"⚠️ 종료 경고: {shutdown_result.error}")

        # 실제 GUI 모드
        print("GUI 모드로 실행합니다...")

        app = PokerHUDApplication()

        try:
            # 초기화
            init_config = ComponentConfig(
                name="Poker HUD Application",
                type=ComponentType.HUD_CORE,
                settings={}
            )
            init_result = await app.initialize(init_config)
            if not init_result.success:
                print(f"❌ 초기화 실패: {init_result.error}")
                return 1

            print("✅ 초기화 성공")

            # 시작
            start_result = await app.start()
            if not start_result.success:
                print(f"❌ 시작 실패: {start_result.error}")
                return 1

            print("✅ 시작 성공")

            # 실제 GUI 실행 (PyQt6 QApplication 등)
            print("🎯 GUI 실행 중...")
            print("💡 실제 GUI를 보려면 PyQt6과 디스플레이 환경이 필요합니다.")
            print("💡 현재는 콘솔 모니터링 모드로 실행됩니다.")
            print()

            # GUI 이벤트 루프 대신 콘솔 모니터링
            await app.run()

            return 0

        except Exception as e:
            print(f"❌ 애플리케이션 에러: {e}")
            return 1

        finally:
            shutdown_result = await app.shutdown()
            if not shutdown_result.success:
                print(f"⚠️ 종료 경고: {shutdown_result.error}")

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
# === Standard Library Imports ===
from typing import Dict, Any, List, Optional
from pathlib import Path

# === Local Imports ===
from .interfaces import IPluginSystem, IPlugin
from .plugin_loader import PluginLoader
from .poker_types import Result, ComponentType, ComponentConfig, PluginInfo, HealthStatus
from .plugin_factory import PluginFactory, PluginFactoryBuilder
from observer_pattern import EventSubject, EventBusAdapter, EventPriority
from strategy_pattern import StrategyDataProcessor, DataProcessingStrategyBuilder, OCRProcessingStrategy, HUDDisplayStrategy

class PluginManager(IPluginSystem):
    """
    플러그인 관리자 - 디자인 패턴 통합 구현

    Factory Pattern, Observer Pattern, Strategy Pattern을 통합하여
    플러그인의 생명주기, 이벤트 처리, 데이터 처리를 관리합니다.

    Attributes:
        _plugin_loader: 플러그인 파일 로더
        _active_plugins: 활성 플러그인 인스턴스들
        _plugin_configs: 플러그인 설정들
        _plugin_factory: 플러그인 팩토리 (Factory Pattern)
        _event_subject: 이벤트 주체 (Observer Pattern)
        _event_bus_adapter: 이벤트 버스 어댑터
        _data_processor: 데이터 처리기 (Strategy Pattern)
    """

    def __init__(self) -> None:
        """PluginManager 초기화"""
        self._plugin_loader: Optional[PluginLoader] = None
        self._active_plugins: Dict[str, IPlugin] = {}
        self._plugin_configs: Dict[str, ComponentConfig] = {}
        self._health_status = HealthStatus.HEALTHY

        # Design Pattern Components
        self._plugin_factory: Optional[PluginFactory] = None
        self._event_subject: Optional[EventSubject] = None
        self._event_bus_adapter: Optional[EventBusAdapter] = None
        self._data_processor: Optional[StrategyDataProcessor] = None

    @property
    def component_type(self) -> ComponentType:
        """컴포넌트 타입"""
        return ComponentType.PLUGIN_MANAGER

    @property
    def health_status(self) -> HealthStatus:
        """건강 상태"""
        return self._health_status

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """초기화 - 디자인 패턴 컴포넌트들 설정"""
        try:
            # 플러그인 디렉토리 설정
            plugin_dir = config.settings.get('plugin_dir', 'plugins')
            self._plugin_loader = PluginLoader(plugin_dir)

            # 플러그인 설정 로드
            self._plugin_configs = config.settings.get('plugin_configs', {})

            # Factory Pattern: 플러그인 팩토리 초기화
            self._plugin_factory = self._build_plugin_factory()

            # Observer Pattern: 이벤트 시스템 초기화
            self._event_subject = EventSubject()
            self._event_bus_adapter = EventBusAdapter(self._event_subject)

            # Strategy Pattern: 데이터 처리기 초기화
            self._data_processor = self._build_data_processor()

            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to initialize PluginManager: {str(e)}")

    def _build_plugin_factory(self) -> PluginFactory:
        """Factory Pattern: 플러그인 팩토리 구축"""
        builder = PluginFactoryBuilder()

        # 플러그인 타입들을 등록 (실제 플러그인 클래스를 import해서 등록)
        try:
            from plugins.ocr_plugin import OCRPlugin
            result = builder._factory.register_plugin_type(ComponentType.OCR_SCANNER, OCRPlugin)
            print(f"OCR result type: {type(result)}, has success: {hasattr(result, 'success')}")
            if hasattr(result, 'success') and not result.success:
                print(f"Warning: Failed to register OCR plugin: {result.error}")
        except ImportError as e:
            print(f"Warning: Could not import OCRPlugin: {e}")
        except Exception as e:
            print(f"Warning: Failed to register OCR plugin: {e}")

        try:
            from plugins.player_hud_plugin import PlayerHUDPlugin
            result = builder._factory.register_plugin_type(ComponentType.HUD_DISPLAY, PlayerHUDPlugin)
            if not result.success:
                print(f"Warning: Failed to register HUD display plugin: {result.error}")
        except ImportError as e:
            print(f"Warning: Could not import PlayerHUDPlugin: {e}")
        except Exception as e:
            print(f"Warning: Failed to register HUD display plugin: {e}")

        try:
            from plugins.hud_plugin import HUDPlugin
            result = builder._factory.register_plugin_type(ComponentType.HUD_MANAGER, HUDPlugin)
            if not result.success:
                print(f"Warning: Failed to register HUD manager plugin: {result.error}")
        except ImportError as e:
            print(f"Warning: Could not import HUDPlugin: {e}")
        except Exception as e:
            print(f"Warning: Failed to register HUD manager plugin: {e}")

        try:
            from plugins.data_store_plugin import DataStorePlugin
            result = builder._factory.register_plugin_type(ComponentType.DATA_STORE, DataStorePlugin)
            if not result.success:
                print(f"Warning: Failed to register data store plugin: {result.error}")
        except ImportError as e:
            print(f"Warning: Could not import DataStorePlugin: {e}")
        except Exception as e:
            print(f"Warning: Failed to register data store plugin: {e}")

        return builder.build()

    def _build_data_processor(self) -> StrategyDataProcessor:
        """Strategy Pattern: 데이터 처리기 구축"""
        builder = DataProcessingStrategyBuilder()

        # 기본 전략들 등록
        builder.add_strategy(OCRProcessingStrategy())
        builder.add_strategy(HUDDisplayStrategy())

        # 기본 전략 설정
        builder.set_default_strategy('image', 'ocr_processor')
        builder.set_default_strategy('player_data', 'hud_display')
        builder.set_default_strategy('game_state', 'hud_display')

        return builder.build_processor()

    async def start(self) -> Result[bool, str]:
        """시작"""
        try:
            # 사용 가능한 플러그인 검색
            discover_result = await self.discover_plugins()
            if not discover_result.success:
                return Result.err(f"Failed to discover plugins: {discover_result.error}")

            available_plugins = {p.id: p for p in discover_result.value}

            # 설정된 플러그인 로드 및 시작
            for plugin_id in self._plugin_configs.keys():
                if plugin_id in available_plugins:
                    load_result = await self.load_plugin(plugin_id)
                    if not load_result.success:
                        print(f"Warning: Failed to load plugin {plugin_id}: {load_result.error}")

            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to start PluginManager: {str(e)}")

    async def stop(self) -> Result[bool, str]:
        """중지"""
        try:
            # 모든 활성 플러그인 중지 및 언로드
            plugin_ids = list(self._active_plugins.keys())
            for plugin_id in plugin_ids:
                unload_result = await self.unload_plugin(plugin_id)
                if not unload_result.success:
                    print(f"Warning: Failed to unload plugin {plugin_id}: {unload_result.error}")

            self._health_status = HealthStatus.DEGRADED
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to stop PluginManager: {str(e)}")

    async def shutdown(self) -> Result[bool, str]:
        """종료 - 디자인 패턴 컴포넌트들 정리"""
        try:
            await self.stop()

            # Observer Pattern: 이벤트 시스템 종료
            if self._event_subject:
                subject_shutdown_result = await self._event_subject.shutdown()
                if not subject_shutdown_result.success:
                    print(f"Warning: Failed to shutdown event subject: {subject_shutdown_result.error}")

            # Event Bus Adapter 종료
            if self._event_bus_adapter:
                adapter_shutdown_result = await self._event_bus_adapter.shutdown()
                if not adapter_shutdown_result.success:
                    print(f"Warning: Failed to shutdown event bus adapter: {adapter_shutdown_result.error}")

            # Data Processor 종료
            if self._data_processor:
                processor_shutdown_result = await self._data_processor.shutdown()
                if not processor_shutdown_result.success:
                    print(f"Warning: Failed to shutdown data processor: {processor_shutdown_result.error}")

            # Factory Pattern: 모든 플러그인 정리
            if self._plugin_factory:
                factory_shutdown_result = await self._plugin_factory.shutdown_all()
                if not factory_shutdown_result.success:
                    print(f"Warning: Failed to shutdown plugin factory: {factory_shutdown_result.error}")

            self._active_plugins.clear()
            self._plugin_configs.clear()
            self._plugin_loader = None
            self._plugin_factory = None
            self._event_subject = None
            self._event_bus_adapter = None
            self._data_processor = None
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to shutdown PluginManager: {str(e)}")

    async def discover_plugins(self) -> Result[List[PluginInfo], str]:
        """플러그인 검색"""
        try:
            if not self._plugin_loader:
                return Result.err("PluginLoader not initialized")

            available_plugins = self._plugin_loader.discover_plugins()
            plugin_infos = []

            for plugin_name in available_plugins:
                # 기본 플러그인 정보 생성 (실제로는 플러그인 메타데이터에서 읽어와야 함)
                info = PluginInfo(
                    id=plugin_name,
                    name=plugin_name.replace('_', ' ').title(),
                    version="1.0.0",
                    description=f"{plugin_name} plugin",
                    author="Unknown"
                )
                plugin_infos.append(info)

            return Result.ok(plugin_infos)
        except Exception as e:
            return Result.err(f"Failed to discover plugins: {str(e)}")

    async def load_plugin(self, plugin_id: str) -> Result[IPlugin, str]:
        """플러그인 로드 - Factory Pattern 사용"""
        try:
            if plugin_id in self._active_plugins:
                return Result.ok(self._active_plugins[plugin_id])

            config = self._plugin_configs.get(plugin_id, ComponentConfig(id=plugin_id, settings={}))

            # Factory Pattern: 팩토리를 사용해서 플러그인 생성
            if self._plugin_factory:
                # 설정에서 플러그인 타입을 결정
                plugin_type = config.settings.get('plugin_type')
                if plugin_type:
                    try:
                        component_type = ComponentType(plugin_type)
                        factory_result = await self._plugin_factory.create_plugin(component_type, config)
                        if factory_result.success:
                            plugin = factory_result.value
                            self._active_plugins[plugin_id] = plugin

                            # Observer Pattern: 플러그인을 이벤트 옵저버로 등록
                            if hasattr(plugin, 'interested_events'):
                                await self._event_subject.attach(plugin)

                            return Result.ok(plugin)
                    except ValueError:
                        pass  # Invalid component type, fall back to loader

            # Fallback: 기존 로더 사용
            plugin = self._plugin_loader.load_plugin(plugin_id, config.settings)

            if not plugin:
                return Result.err(f"Failed to load plugin {plugin_id}")

            # 플러그인 초기화
            init_result = await plugin.initialize(config)
            if not init_result.success:
                return Result.err(f"Failed to initialize plugin {plugin_id}: {init_result.error}")

            # 플러그인 시작
            start_result = await plugin.start()
            if not start_result.success:
                return Result.err(f"Failed to start plugin {plugin_id}: {start_result.error}")

            self._active_plugins[plugin_id] = plugin
            return Result.ok(plugin)
        except Exception as e:
            return Result.err(f"Failed to load plugin {plugin_id}: {str(e)}")

    async def unload_plugin(self, plugin_id: str) -> Result[bool, str]:
        """플러그인 언로드"""
        try:
            if plugin_id not in self._active_plugins:
                return Result.ok(True)

            plugin = self._active_plugins[plugin_id]

            # 플러그인 중지
            stop_result = await plugin.stop()
            if not stop_result.success:
                print(f"Warning: Failed to stop plugin {plugin_id}: {stop_result.error}")

            # 플러그인 종료
            shutdown_result = await plugin.shutdown()
            if not shutdown_result.success:
                print(f"Warning: Failed to shutdown plugin {plugin_id}: {shutdown_result.error}")

            # 로더에서 언로드
            self._plugin_loader.unload_plugin(plugin_id)
            del self._active_plugins[plugin_id]

            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to unload plugin {plugin_id}: {str(e)}")

    def get_loaded_plugins(self) -> Dict[str, IPlugin]:
        """로드된 플러그인 조회"""
        return self._active_plugins.copy()

    async def reload_plugin(self, plugin_id: str) -> Result[bool, str]:
        """플러그인 리로드"""
        try:
            # 먼저 언로드
            unload_result = await self.unload_plugin(plugin_id)
            if not unload_result.success:
                return unload_result

            # 다시 로드
            load_result = await self.load_plugin(plugin_id)
            if not load_result.success:
                return Result.err(f"Failed to reload plugin {plugin_id}: {load_result.error}")

            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to reload plugin {plugin_id}: {str(e)}")

    # === 레거시 호환성 메서드들 ===

    def get_active_plugins(self) -> List[str]:
        """활성 플러그인 목록 (레거시)"""
        return list(self._active_plugins.keys())

    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """특정 플러그인 반환 (레거시)"""
        return self._active_plugins.get(plugin_name)

    def add_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> Result[bool, str]:
        """플러그인 설정 추가 (레거시)"""
        try:
            component_config = ComponentConfig(id=plugin_name, settings=config)
            self._plugin_configs[plugin_name] = component_config
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to add config for plugin {plugin_name}: {str(e)}")

    # === 디자인 패턴 접근 메서드들 ===

    def get_event_bus(self):
        """Observer Pattern: 이벤트 버스 접근"""
        return self._event_bus_adapter

    def get_data_processor(self):
        """Strategy Pattern: 데이터 처리기 접근"""
        return self._data_processor

    def get_plugin_factory(self):
        """Factory Pattern: 플러그인 팩토리 접근"""
        return self._plugin_factory

    async def publish_event(self, event_type: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL) -> Result[bool, str]:
        """Observer Pattern: 이벤트 발행"""
        if self._event_bus_adapter:
            return await self._event_bus_adapter.publish_event(event_type, data, priority)
        return Result.err("Event bus not initialized")

    async def process_data(self, data: Any, data_type: str, context: Dict[str, Any] = None) -> Result[Any, str]:
        """Strategy Pattern: 데이터 처리"""
        if self._data_processor:
            return await self._data_processor.process_data(data, data_type, context)
        return Result.err("Data processor not initialized")
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol
import logging

# === Local Imports ===
from .poker_types import (
    Result, ComponentType, ComponentConfig, HealthStatus,
    PluginInfo, Event, StateUpdate, DataPacket, ISubscriber
)

# === Core Component Interface ===
class ICoreComponent(ABC):
    """
    모든 코어 컴포넌트의 기본 인터페이스

    이 인터페이스는 시스템의 모든 주요 컴포넌트가 구현해야 하는
    기본적인 생명주기 메소드들을 정의합니다.

    컴포넌트들은 초기화 → 시작 → 중지 → 종료의 생명주기를 따릅니다.
    각 단계에서 Result 타입을 반환하여 성공/실패 상태를 명확히 합니다.
    """

    @abstractmethod
    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """
        비동기 초기화

        컴포넌트를 초기화하고 필요한 리소스를 준비합니다.
        이 메소드는 컴포넌트의 전체 생명주기에서 한 번만 호출됩니다.

        Args:
            config: 컴포넌트 설정 정보

        Returns:
            Result[bool, str]: 초기화 성공 여부
        """
        pass

    @abstractmethod
    async def start(self) -> Result[bool, str]:
        """
        비동기 시작

        초기화된 컴포넌트를 실제로 시작합니다.
        이 메소드는 여러 번 호출될 수 있습니다 (시작/중지 반복).

        Returns:
            Result[bool, str]: 시작 성공 여부
        """
        pass

    @abstractmethod
    async def stop(self) -> Result[bool, str]:
        """
        비동기 중지

        실행 중인 컴포넌트를 일시적으로 중지합니다.
        리소스는 유지되며, 다시 시작할 수 있습니다.

        Returns:
            Result[bool, str]: 중지 성공 여부
        """
        pass

    @abstractmethod
    async def shutdown(self) -> Result[bool, str]:
        """
        비동기 종료

        컴포넌트를 완전히 종료하고 모든 리소스를 해제합니다.
        이 메소드 호출 후 컴포넌트는 더 이상 사용할 수 없습니다.

        Returns:
            Result[bool, str]: 종료 성공 여부
        """
        pass

    @property
    @abstractmethod
    def component_type(self) -> ComponentType:
        """
        컴포넌트 타입

        이 컴포넌트의 유형을 식별합니다.
        시스템 모니터링 및 관리에 사용됩니다.

        Returns:
            ComponentType: 컴포넌트의 타입
        """
        pass

    @property
    @abstractmethod
    def health_status(self) -> HealthStatus:
        """
        건강 상태

        컴포넌트의 현재 건강 상태를 보고합니다.
        모니터링 시스템에서 사용됩니다.

        Returns:
            HealthStatus: 컴포넌트의 건강 상태
        """
        pass

# === Plugin System ===
class IPlugin(ABC):
    """
    기본 플러그인 인터페이스

    모든 플러그인이 구현해야 하는 기본 인터페이스입니다.
    플러그인의 생명주기 관리와 메타데이터 제공을 담당합니다.

    플러그인은 ICoreComponent를 상속하므로 동일한 생명주기 메소드들을
    가지고 있으며, 추가로 이름, 버전 등의 메타데이터를 제공합니다.
    """

    @abstractmethod
    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """
        플러그인 초기화

        플러그인을 초기화하고 필요한 리소스를 준비합니다.

        Args:
            config: 플러그인 설정 정보

        Returns:
            Result[bool, str]: 초기화 성공 여부
        """
        pass

    @abstractmethod
    async def start(self) -> Result[bool, str]:
        """
        플러그인 시작

        초기화된 플러그인을 실제로 시작합니다.

        Returns:
            Result[bool, str]: 시작 성공 여부
        """
        pass

    @abstractmethod
    async def stop(self) -> Result[bool, str]:
        """
        플러그인 중지

        실행 중인 플러그인을 일시적으로 중지합니다.

        Returns:
            Result[bool, str]: 중지 성공 여부
        """
        pass

    @abstractmethod
    async def shutdown(self) -> Result[bool, str]:
        """
        플러그인 종료

        플러그인을 완전히 종료하고 모든 리소스를 해제합니다.

        Returns:
            Result[bool, str]: 종료 성공 여부
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        플러그인 이름

        플러그인의 고유 식별자입니다.

        Returns:
            str: 플러그인 이름
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        플러그인 버전

        플러그인의 버전 정보입니다.

        Returns:
            str: 플러그인 버전 (예: "1.0.0")
        """
        pass

    @property
    @abstractmethod
    def component_type(self) -> ComponentType:
        """
        컴포넌트 타입

        이 플러그인의 컴포넌트 유형입니다.

        Returns:
            ComponentType: 플러그인의 컴포넌트 타입
        """
        pass

    @property
    @abstractmethod
    def health_status(self) -> HealthStatus:
        """건강 상태"""
        pass

class IPluginSystem(ICoreComponent):
    """
    플러그인 시스템 인터페이스

    플러그인의 검색, 로드, 언로드, 관리를 담당하는 시스템의 인터페이스입니다.
    동적 플러그인 관리를 위한 모든 기능을 제공합니다.
    """

    @abstractmethod
    async def discover_plugins(self) -> Result[List[PluginInfo], str]:
        """
        플러그인 검색

        시스템에서 사용 가능한 플러그인을 검색합니다.

        Returns:
            Result[List[PluginInfo], str]: 발견된 플러그인 정보 목록
        """
        pass

    @abstractmethod
    async def load_plugin(self, plugin_id: str) -> Result[IPlugin, str]:
        """
        플러그인 로드

        지정된 플러그인을 로드하고 초기화합니다.

        Args:
            plugin_id: 로드할 플러그인의 ID

        Returns:
            Result[IPlugin, str]: 로드된 플러그인 인스턴스
        """
        pass

    @abstractmethod
    async def unload_plugin(self, plugin_id: str) -> Result[bool, str]:
        """
        플러그인 언로드

        지정된 플러그인을 언로드하고 리소스를 해제합니다.

        Args:
            plugin_id: 언로드할 플러그인의 ID

        Returns:
            Result[bool, str]: 언로드 성공 여부
        """
        pass

    @abstractmethod
    def get_loaded_plugins(self) -> Dict[str, IPlugin]:
        """
        로드된 플러그인 조회

        현재 로드되어 있는 모든 플러그인을 반환합니다.

        Returns:
            Dict[str, IPlugin]: 플러그인 ID를 키로 하는 플러그인 인스턴스 딕셔너리
        """
        pass

    @abstractmethod
    async def reload_plugin(self, plugin_id: str) -> Result[bool, str]:
        """
        플러그인 리로드

        지정된 플러그인을 언로드한 후 다시 로드합니다.

        Args:
            plugin_id: 리로드할 플러그인의 ID

        Returns:
            Result[bool, str]: 리로드 성공 여부
        """
        pass

# === Core Interfaces ===
class IManager(ICoreComponent):
    """
    메인 매니저 인터페이스

    애플리케이션의 주요 컴포넌트들을 통합 관리하는 메인 매니저의 인터페이스입니다.
    전체 시스템의 시작, 중지, 상태 관리를 담당합니다.
    """

    @abstractmethod
    async def start_application(self) -> Result[bool, str]:
        """
        애플리케이션 시작

        전체 애플리케이션을 시작하고 모든 컴포넌트들을 초기화합니다.

        Returns:
            Result[bool, str]: 애플리케이션 시작 성공 여부
        """
        pass

    @abstractmethod
    async def stop_application(self) -> Result[bool, str]:
        """애플리케이션 종료"""
        pass

    @abstractmethod
    def get_component(self, component_type: ComponentType) -> Optional[ICoreComponent]:
        """컴포넌트 조회"""
        pass

class IScanner(IPlugin):
    """
    스캔 인터페이스 (OCR 등)

    화면이나 이미지에서 텍스트를 스캔하는 기능을 제공하는 인터페이스입니다.
    OCR (Optical Character Recognition) 기능을 위한 표준 인터페이스를 정의합니다.
    """

    @abstractmethod
    async def start_scan(self) -> Result[bool, str]:
        """
        스캔 시작

        스캔 작업을 시작합니다.

        Returns:
            Result[bool, str]: 스캔 시작 성공 여부
        """
        pass

    @abstractmethod
    async def stop_scan(self) -> Result[bool, str]:
        """
        스캔 중지

        진행 중인 스캔 작업을 중지합니다.

        Returns:
            Result[bool, str]: 스캔 중지 성공 여부
        """
        pass

    @abstractmethod
    def is_scanning(self) -> bool:
        """
        스캔 상태 확인

        현재 스캔이 진행 중인지 확인합니다.

        Returns:
            bool: 스캔 진행 중 여부
        """
        pass

    @abstractmethod
    def get_scan_result(self) -> Optional[Dict[str, Any]]:
        """
        스캔 결과 반환

        가장 최근의 스캔 결과를 반환합니다.

        Returns:
            Optional[Dict[str, Any]]: 스캔 결과 데이터 또는 None
        """
        pass

class IDisplay(IPlugin):
    """
    표시 인터페이스 (HUD 등)

    HUD (Heads-Up Display) 및 기타 시각적 요소를 표시하고 관리하는 인터페이스입니다.
    플레이어 정보를 실시간으로 화면에 표시하는 기능을 제공합니다.
    """

    @abstractmethod
    async def show_hud(self, player_id: str, data: Dict[str, Any]) -> Result[bool, str]:
        """
        HUD 표시

        지정된 플레이어의 HUD를 표시합니다.

        Args:
            player_id: 플레이어 ID
            data: 표시할 HUD 데이터

        Returns:
            Result[bool, str]: HUD 표시 성공 여부
        """
        pass

    @abstractmethod
    async def hide_hud(self, player_id: str) -> Result[bool, str]:
        """
        HUD 숨김

        지정된 플레이어의 HUD를 숨깁니다.

        Args:
            player_id: 플레이어 ID

        Returns:
            Result[bool, str]: HUD 숨김 성공 여부
        """
        pass

    @abstractmethod
    async def update_hud(self, player_id: str, updates: Dict[str, Any]) -> Result[bool, str]:
        """
        HUD 업데이트

        지정된 플레이어의 HUD를 업데이트합니다.

        Args:
            player_id: 플레이어 ID
            updates: 업데이트할 데이터

        Returns:
            Result[bool, str]: HUD 업데이트 성공 여부
        """
        pass

class IDataManager(IPlugin):
    """
    데이터 관리 인터페이스

    플레이어 데이터의 저장, 로드, 관리를 담당하는 인터페이스입니다.
    플레이어 통계, 설정, 게임 히스토리 등의 데이터를 영구적으로 저장하고 검색합니다.
    """

    @abstractmethod
    async def save_player_data(self, player_id: str, data: Dict[str, Any]) -> Result[bool, str]:
        """
        플레이어 데이터 저장

        지정된 플레이어의 데이터를 저장합니다.

        Args:
            player_id: 플레이어 ID
            data: 저장할 데이터

        Returns:
            Result[bool, str]: 저장 성공 여부
        """
        pass

    @abstractmethod
    async def load_player_data(self, player_id: str) -> Result[Optional[Dict[str, Any]], str]:
        """
        플레이어 데이터 로드

        지정된 플레이어의 데이터를 로드합니다.

        Args:
            player_id: 플레이어 ID

        Returns:
            Result[Optional[Dict[str, Any]], str]: 로드된 데이터 또는 None
        """
        pass

    @abstractmethod
    async def delete_player_data(self, player_id: str) -> Result[bool, str]:
        """
        플레이어 데이터 삭제

        지정된 플레이어의 데이터를 삭제합니다.

        Args:
            player_id: 플레이어 ID

        Returns:
            Result[bool, str]: 삭제 성공 여부
        """
        pass

    @abstractmethod
    def list_players(self) -> List[str]:
        """
        플레이어 목록 반환

        저장된 모든 플레이어 ID 목록을 반환합니다.

        Returns:
            List[str]: 플레이어 ID 목록
        """
        pass

class IControlPanel(IPlugin):
    """
    컨트롤 패널 인터페이스

    사용자 인터페이스 컨트롤 패널을 관리하는 인터페이스입니다.
    설정 변경, 모니터링, 제어를 위한 GUI를 제공합니다.
    """

    @abstractmethod
    async def show_panel(self) -> Result[bool, str]:
        """
        패널 표시

        컨트롤 패널을 화면에 표시합니다.

        Returns:
            Result[bool, str]: 패널 표시 성공 여부
        """
        pass

    @abstractmethod
    async def hide_panel(self) -> Result[bool, str]:
        """
        패널 숨김

        컨트롤 패널을 화면에서 숨깁니다.

        Returns:
            Result[bool, str]: 패널 숨김 성공 여부
        """
        pass

    @abstractmethod
    async def update_settings(self, settings: Dict[str, Any]) -> Result[bool, str]:
        """
        설정 업데이트

        컨트롤 패널의 설정을 업데이트합니다.

        Args:
            settings: 업데이트할 설정 데이터

        Returns:
            Result[bool, str]: 설정 업데이트 성공 여부
        """
        pass

class ILogger(IPlugin):
    """
    로깅 인터페이스

    애플리케이션의 로깅 기능을 제공하는 인터페이스입니다.
    다양한 로그 레벨과 구조화된 로깅을 지원합니다.
    """

    @abstractmethod
    async def log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None) -> Result[bool, str]:
        """
        로그 기록

        지정된 레벨로 메시지를 로깅합니다.

        Args:
            level: 로그 레벨 (예: logging.INFO)
            message: 로그 메시지
            extra: 추가 로그 데이터

        Returns:
            Result[bool, str]: 로깅 성공 여부
        """
        pass

    @abstractmethod
    async def set_level(self, level: int) -> Result[bool, str]:
        """
        로그 레벨 설정

        로거의 최소 로그 레벨을 설정합니다.

        Args:
            level: 설정할 로그 레벨

        Returns:
            Result[bool, str]: 레벨 설정 성공 여부
        """
        pass

# === Data Flow System ===
class IDataFlowSystem(ICoreComponent):
    """
    통합 데이터 흐름 시스템

    이벤트, 데이터 패킷, 상태 업데이트를 통합 관리하는 시스템 인터페이스입니다.
    발행-구독 패턴을 통해 컴포넌트 간 데이터 흐름을 조율합니다.
    """

    @abstractmethod
    async def publish_event(self, event: Event) -> Result[bool, str]:
        """
        이벤트 발행

        이벤트를 모든 구독자에게 발행합니다.

        Args:
            event: 발행할 이벤트

        Returns:
            Result[bool, str]: 이벤트 발행 성공 여부
        """
        pass

    @abstractmethod
    async def send_data(self, packet: DataPacket) -> Result[bool, str]:
        """
        데이터 전송

        데이터 패킷을 목적지로 전송합니다.

        Args:
            packet: 전송할 데이터 패킷

        Returns:
            Result[bool, str]: 데이터 전송 성공 여부
        """
        pass

    @abstractmethod
    async def update_state(self, state: StateUpdate) -> Result[bool, str]:
        """
        상태 업데이트

        시스템 상태를 업데이트하고 관련 컴포넌트에 알립니다.

        Args:
            state: 상태 업데이트 정보

        Returns:
            Result[bool, str]: 상태 업데이트 성공 여부
        """
        pass

    @abstractmethod
    def subscribe(self, subscriber: ISubscriber) -> Result[bool, str]:
        """
        구독자 등록

        이벤트와 데이터 업데이트를 받을 구독자를 등록합니다.

        Args:
            subscriber: 등록할 구독자

        Returns:
            Result[bool, str]: 구독자 등록 성공 여부
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscriber: ISubscriber) -> Result[bool, str]:
        """
        구독자 해제

        등록된 구독자를 해제합니다.

        Args:
            subscriber: 해제할 구독자

        Returns:
            Result[bool, str]: 구독자 해제 성공 여부
        """
        pass

# === Event System ===
class IEventBus(ICoreComponent):
    """
    이벤트 버스 인터페이스

    이벤트 기반 통신을 위한 중앙 집중식 이벤트 버스입니다.
    발행-구독 패턴을 통해 컴포넌트 간 느슨한 결합을 유지합니다.
    """

    @abstractmethod
    async def subscribe(self, event_type: str, callback: callable) -> Result[bool, str]:
        """
        이벤트 구독

        특정 타입의 이벤트를 구독합니다.

        Args:
            event_type: 구독할 이벤트 타입
            callback: 이벤트 발생 시 호출될 콜백 함수

        Returns:
            Result[bool, str]: 구독 성공 여부
        """
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: str, callback: callable) -> Result[bool, str]:
        """
        이벤트 구독 해제

        특정 타입의 이벤트 구독을 해제합니다.

        Args:
            event_type: 구독 해제할 이벤트 타입
            callback: 제거할 콜백 함수

        Returns:
            Result[bool, str]: 구독 해제 성공 여부
        """
        pass

    @abstractmethod
    async def publish(self, event: Event) -> Result[bool, str]:
        """
        이벤트 발행

        이벤트를 모든 관련 구독자에게 발행합니다.

        Args:
            event: 발행할 이벤트

        Returns:
            Result[bool, str]: 이벤트 발행 성공 여부
        """
        pass

# === Data Bus System ===
class IDataBus(ICoreComponent):
    """
    데이터 버스 인터페이스

    컴포넌트 간 데이터 전송을 위한 라우팅 시스템입니다.
    출발지와 목적지를 기반으로 데이터를 라우팅합니다.
    """

    @abstractmethod
    async def send_data(self, source: str, destination: str, data: Any) -> Result[bool, str]:
        """
        데이터 전송

        지정된 목적지로 데이터를 전송합니다.

        Args:
            source: 데이터 출발지 식별자
            destination: 데이터 목적지 식별자
            data: 전송할 데이터

        Returns:
            Result[bool, str]: 데이터 전송 성공 여부
        """
        pass

    @abstractmethod
    async def receive_data(self, source: str, data_type: str) -> Result[Optional[Any], str]:
        """
        데이터 수신

        지정된 출발지와 타입의 데이터를 수신합니다.

        Args:
            source: 데이터 출발지 식별자
            data_type: 데이터 타입

        Returns:
            Result[Optional[Any], str]: 수신된 데이터 또는 None
        """
        pass

    @abstractmethod
    async def add_route(self, source: str, destination: str) -> Result[bool, str]:
        """
        라우트 추가

        출발지와 목적지 간의 데이터 라우트를 추가합니다.

        Args:
            source: 출발지 식별자
            destination: 목적지 식별자

        Returns:
            Result[bool, str]: 라우트 추가 성공 여부
        """
        pass

    @abstractmethod
    async def remove_route(self, source: str, destination: str) -> Result[bool, str]:
        """
        라우트 제거

        출발지와 목적지 간의 데이터 라우트를 제거합니다.

        Args:
            source: 출발지 식별자
            destination: 목적지 식별자

        Returns:
            Result[bool, str]: 라우트 제거 성공 여부
        """
        pass

class IStateManager(ICoreComponent):
    """
    상태 관리자 인터페이스

    애플리케이션의 상태 정보를 중앙 집중식으로 관리하는 인터페이스입니다.
    키-값 저장소를 통해 상태를 저장, 조회, 삭제합니다.
    """

    @abstractmethod
    async def set_state(self, state_id: str, value: Any) -> Result[bool, str]:
        """
        상태 설정

        지정된 ID로 상태 값을 설정합니다.

        Args:
            state_id: 상태 식별자
            value: 설정할 상태 값

        Returns:
            Result[bool, str]: 상태 설정 성공 여부
        """
        pass

    @abstractmethod
    async def get_state(self, state_id: str) -> Result[Optional[Any], str]:
        """
        상태 조회

        지정된 ID의 상태 값을 조회합니다.

        Args:
            state_id: 조회할 상태 식별자

        Returns:
            Result[Optional[Any], str]: 상태 값 또는 None (존재하지 않는 경우)
        """
        pass

    @abstractmethod
    async def delete_state(self, state_id: str) -> Result[bool, str]:
        """
        상태 삭제

        지정된 ID의 상태를 삭제합니다.

        Args:
            state_id: 삭제할 상태 식별자

        Returns:
            Result[bool, str]: 상태 삭제 성공 여부
        """
        pass

    @abstractmethod
    def has_state(self, state_id: str) -> bool:
        """
        상태 존재 확인

        지정된 ID의 상태가 존재하는지 확인합니다.

        Args:
            state_id: 확인할 상태 식별자

        Returns:
            bool: 상태 존재 여부
        """
        pass

    @abstractmethod
    def get_all_states(self) -> Dict[str, Any]:
        """
        모든 상태 조회

        저장된 모든 상태를 딕셔너리 형태로 반환합니다.

        Returns:
            Dict[str, Any]: 모든 상태의 딕셔너리
        """
        pass

class IDataProcessor(ICoreComponent):
    """
    데이터 처리자 인터페이스 - Strategy Pattern

    다양한 데이터 처리 전략을 지원하는 인터페이스입니다.
    Strategy 패턴을 통해 데이터 타입에 따라 적절한 처리 알고리즘을 선택합니다.
    """

    @abstractmethod
    async def process_data(self, data: Any, data_type: str, context: Dict[str, Any] = None) -> Result[Any, str]:
        """
        데이터 처리

        주어진 데이터 타입에 맞는 전략을 사용하여 데이터를 처리합니다.

        Args:
            data: 처리할 데이터
            data_type: 데이터 타입 식별자
            context: 처리 컨텍스트 (옵션)

        Returns:
            Result[Any, str]: 처리된 데이터 또는 에러
        """
        pass

    @abstractmethod
    def get_available_strategies(self, data_type: str = None) -> List[str]:
        """
        사용 가능한 전략 목록

        지정된 데이터 타입에 대해 사용 가능한 처리 전략 목록을 반환합니다.

        Args:
            data_type: 데이터 타입 식별자 (None인 경우 모든 전략)

        Returns:
            List[str]: 사용 가능한 전략 이름 목록
        """
        pass

    @abstractmethod
    def set_default_strategy(self, data_type: str, strategy_name: str) -> Result[bool, str]:
        """
        기본 전략 설정

        지정된 데이터 타입의 기본 처리 전략을 설정합니다.

        Args:
            data_type: 데이터 타입 식별자
            strategy_name: 설정할 전략 이름

        Returns:
            Result[bool, str]: 전략 설정 성공 여부
        """
        pass

# === Plugin System Extensions ===
class IPluginFactory(ABC):
    """플러그인 팩토리 인터페이스"""

    @abstractmethod
    def create_plugin(self, plugin_type: str, config: Dict[str, Any]) -> Optional[IPlugin]:
        """플러그인 생성"""
        pass

class IPluginRegistry(ABC):
    """플러그인 레지스트리 인터페이스"""

    @abstractmethod
    def register_plugin(self, plugin_type: str, factory: IPluginFactory) -> bool:
        """플러그인 등록"""
        pass

    @abstractmethod
    def get_plugin_types(self) -> List[str]:
        """등록된 플러그인 타입 목록"""
        pass

class IPluginLoader(ABC):
    """플러그인 로더 인터페이스"""

    @abstractmethod
    def load_plugin(self, plugin_type: str) -> Optional[IPlugin]:
        """플러그인 로드"""
        pass

    @abstractmethod
    def unload_plugin(self, plugin_type: str) -> bool:
        """플러그인 언로드"""
        pass

class IPluginLifecycleManager(ABC):
    """플러그인 생명주기 관리자 인터페이스"""

    @abstractmethod
    def initialize_plugins(self, configs: Dict[str, Dict[str, Any]]) -> bool:
        """플러그인 초기화"""
        pass

    @abstractmethod
    def start_plugins(self) -> bool:
        """플러그인 시작"""
        pass

    @abstractmethod
    def stop_plugins(self) -> bool:
        """플러그인 중지"""
        pass

    @abstractmethod
    def shutdown_plugins(self) -> bool:
        """플러그인 종료"""
        pass
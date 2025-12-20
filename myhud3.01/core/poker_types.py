# === Standard Library Imports ===
from typing import TypeVar, Generic, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# === Type Variables ===
T = TypeVar('T')
E = TypeVar('E')

# === Result Type ===
@dataclass
class Result(Generic[T, E]):
    """
    결과 타입 (성공/실패 처리)

    함수의 실행 결과를 명확하게 표현하기 위한 타입입니다.
    성공과 실패를 명확히 구분하여 예외 처리 대신 타입 안전한 방법을 제공합니다.

    Attributes:
        success: 작업 성공 여부
        value: 성공 시 반환 값 (실패 시 None)
        error: 실패 시 에러 정보 (성공 시 None)
    """

    success: bool
    value: Optional[T] = None
    error: Optional[E] = None

    @classmethod
    def ok(cls, value: T) -> 'Result[T, E]':
        """
        성공 결과 생성

        작업이 성공했을 때 결과를 생성합니다.

        Args:
            value: 성공 값

        Returns:
            Result[T, E]: 성공 결과를 포함한 Result 객체
        """
        return cls(success=True, value=value)

    @classmethod
    def err(cls, error: E) -> 'Result[T, E]':
        """
        실패 결과 생성

        작업이 실패했을 때 결과를 생성합니다.

        Args:
            error: 에러 정보

        Returns:
            Result[T, E]: 실패 결과를 포함한 Result 객체
        """
        return cls(success=False, error=error)

# === Component Types ===
class ComponentType(Enum):
    """
    컴포넌트 타입 열거형

    시스템의 각 컴포넌트를 식별하기 위한 타입 정의입니다.
    컴포넌트 관리, 모니터링, 설정 등에 사용됩니다.
    """
    PLUGIN_MANAGER = "plugin_manager"
    DATA_FLOW = "data_flow"
    SCANNER = "scanner"
    OCR_SCANNER = "ocr_scanner"
    DISPLAY = "display"
    HUD_DISPLAY = "hud_display"
    HUD_MANAGER = "hud_manager"
    DATA_STORE = "data_store"
    CONTROL_PANEL = "control_panel"
    LOGGER = "logger"
    EVENT_BUS = "event_bus"
    DATA_BUS = "data_bus"
    STATE_MANAGER = "state_manager"

class HealthStatus(Enum):
    """
    컴포넌트 건강 상태

    컴포넌트의 운영 상태를 나타내는 열거형입니다.
    모니터링 시스템에서 컴포넌트의 건강도를 평가하는 데 사용됩니다.
    """
    HEALTHY = "healthy"      # 정상 작동
    DEGRADED = "degraded"    # 성능 저하 또는 부분 장애
    UNHEALTHY = "unhealthy"  # 심각한 장애 또는 작동 불가

# === Configuration Types ===
@dataclass
class ComponentConfig:
    """
    컴포넌트 설정

    컴포넌트의 초기화와 구성을 위한 설정 정보를 담는 데이터 클래스입니다.

    Attributes:
        id: 컴포넌트 고유 식별자
        settings: 컴포넌트별 설정 값들
        dependencies: 의존하는 컴포넌트 ID 목록
    """
    id: str
    settings: Dict[str, Any]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class PluginInfo:
    """
    플러그인 정보

    플러그인의 메타데이터를 담는 데이터 클래스입니다.
    플러그인 검색, 로드, 관리에 사용됩니다.

    Attributes:
        id: 플러그인 고유 식별자
        name: 플러그인 표시 이름
        version: 플러그인 버전
        description: 플러그인 설명
        author: 플러그인 작성자
        dependencies: 의존하는 플러그인 ID 목록
    """
    id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

# === Event Types ===
@dataclass
class Event:
    """
    이벤트 데이터

    이벤트 버스를 통해 전달되는 이벤트 정보를 담는 데이터 클래스입니다.

    Attributes:
        event_type: 이벤트 타입 식별자
        source: 이벤트 발생 출처
        timestamp: 이벤트 발생 시각 (Unix timestamp)
        data: 이벤트 관련 추가 데이터
    """
    event_type: str
    source: str
    timestamp: float
    data: Dict[str, Any]

@dataclass
class StateUpdate:
    """
    상태 업데이트

    상태 변경 이벤트를 나타내는 데이터 클래스입니다.

    Attributes:
        state_id: 변경된 상태의 식별자
        value: 새로운 상태 값
        source: 상태 변경 출처
        timestamp: 상태 변경 시각 (Unix timestamp)
    """
    state_id: str
    value: Any
    source: str
    timestamp: float

@dataclass
class DataPacket:
    """
    데이터 패킷

    컴포넌트 간 데이터 전송을 위한 패킷 구조입니다.

    Attributes:
        source: 데이터 출발지
        destination: 데이터 목적지
        data_type: 데이터 타입
        payload: 실제 데이터
        timestamp: 패킷 생성 시각 (Unix timestamp)
        metadata: 추가 메타데이터
        correlation_id: 요청-응답 상관관계 추적을 위한 ID
    """
    source: str
    destination: str
    data_type: str
    payload: Any
    timestamp: float
    metadata: Dict[str, Any] = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

# === Subscriber Interface ===
class ISubscriber:
    """
    구독자 인터페이스

    이벤트, 데이터, 상태 변경을 구독하는 컴포넌트가 구현해야 하는 인터페이스입니다.
    Observer 패턴의 구독자 역할을 수행합니다.
    """

    async def on_event(self, event: Event) -> None:
        """
        이벤트 수신

        이벤트 버스로부터 이벤트를 수신할 때 호출됩니다.

        Args:
            event: 수신된 이벤트
        """
        pass

    async def on_data(self, packet: DataPacket) -> None:
        """
        데이터 수신

        데이터 버스로부터 데이터 패킷을 수신할 때 호출됩니다.

        Args:
            packet: 수신된 데이터 패킷
        """
        pass

    async def on_state_change(self, update: StateUpdate) -> None:
        """
        상태 변경 수신

        상태 관리자로부터 상태 변경을 수신할 때 호출됩니다.

        Args:
            update: 상태 변경 정보
        """
        pass
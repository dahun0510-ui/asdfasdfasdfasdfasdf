"""
Poker HUD Type Definitions

이 모듈은 Poker HUD 시스템에서 사용되는 모든 타입 정의를 포함합니다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
import asyncio
from datetime import datetime

# === Generic Type Variables ===
T = TypeVar('T')
E = TypeVar('E')

# === Result Type ===
class Result(Generic[T, E]):
    """
    성공/실패 결과를 나타내는 제네릭 타입

    성공 시 data에 값이, 실패 시 error에 에러 메시지가 저장됩니다.
    """

    def __init__(self, success: bool, data: Optional[T] = None, error: Optional[E] = None):
        self.success = success
        self.data = data
        self.error = error

    @classmethod
    def ok(cls, data: T) -> 'Result[T, Any]':
        """성공 결과를 생성합니다."""
        return cls(True, data=data)

    @classmethod
    def err(cls, error: E) -> 'Result[Any, E]':
        """실패 결과를 생성합니다."""
        return cls(False, error=error)

    def is_ok(self) -> bool:
        """성공 여부를 반환합니다."""
        return self.success

    def is_err(self) -> bool:
        """실패 여부를 반환합니다."""
        return not self.success

    def unwrap(self) -> T:
        """성공 시 데이터를 반환하고, 실패 시 예외를 발생시킵니다."""
        if self.is_err():
            raise ValueError(f"Result is error: {self.error}")
        return self.data

    def unwrap_err(self) -> E:
        """실패 시 에러를 반환하고, 성공 시 예외를 발생시킵니다."""
        if self.is_ok():
            raise ValueError(f"Result is ok: {self.data}")
        return self.error

# === Component Types ===
class ComponentType(Enum):
    """컴포넌트 타입 열거형"""
    PLUGIN_MANAGER = "plugin_manager"
    EVENT_BUS = "event_bus"
    TASK_QUEUE = "task_queue"
    HUD_CORE = "hud_core"
    OCR_WORKER = "ocr_worker"
    DATA_PROCESSOR = "data_processor"

# === Health Status ===
class HealthStatus(Enum):
    """컴포넌트 건강 상태 열거형"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

# === Configuration Types ===
@dataclass
class ComponentConfig:
    """
    컴포넌트 설정 정보

    각 컴포넌트의 초기화에 필요한 설정 정보를 담습니다.
    """
    name: str
    type: ComponentType
    enabled: bool = True
    priority: int = 0
    settings: Dict[str, Any] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}
        if self.dependencies is None:
            self.dependencies = []

# === Plugin Information ===
@dataclass
class PluginInfo:
    """
    플러그인 정보

    플러그인의 메타데이터를 담습니다.
    """
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}

# === Event System Types ===
@dataclass
class Event:
    """
    이벤트 데이터

    시스템 내에서 발생하는 이벤트를 표현합니다.
    """
    type: str
    source: str
    timestamp: datetime
    data: Dict[str, Any] = None
    priority: int = 0

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

# === State Management Types ===
@dataclass
class StateUpdate:
    """
    상태 업데이트 정보

    컴포넌트 상태 변경을 표현합니다.
    """
    component: str
    state: str
    timestamp: datetime
    data: Dict[str, Any] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

# === Data Packet ===
@dataclass
class DataPacket:
    """
    데이터 패킷

    컴포넌트 간 데이터 전송을 위한 패킷입니다.
    """
    source: str
    destination: str
    type: str
    data: Any
    timestamp: datetime
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# === Subscriber Interface ===
class ISubscriber(ABC):
    """
    이벤트 구독자 인터페이스

    이벤트를 구독하고 처리할 수 있는 컴포넌트를 위한 인터페이스입니다.
    """

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """
        이벤트 수신 처리

        Args:
            event: 수신된 이벤트
        """
        pass

    @abstractmethod
    def get_subscribed_events(self) -> List[str]:
        """
        구독 중인 이벤트 타입 목록 반환

        Returns:
            List[str]: 구독 이벤트 타입 목록
        """
        pass

# === Utility Functions ===
def create_event(event_type: str, source: str, data: Optional[Dict[str, Any]] = None, priority: int = 0) -> Event:
    """이벤트 객체를 생성합니다."""
    return Event(
        type=event_type,
        source=source,
        timestamp=datetime.now(),
        data=data or {},
        priority=priority
    )

def create_data_packet(source: str, destination: str, packet_type: str, data: Any, correlation_id: Optional[str] = None) -> DataPacket:
    """데이터 패킷을 생성합니다."""
    return DataPacket(
        source=source,
        destination=destination,
        type=packet_type,
        data=data,
        timestamp=datetime.now(),
        correlation_id=correlation_id
    )
"""
Strategy Pattern Implementation
Configurable data processing strategies for different algorithms
"""

from typing import Dict, List, Any, Optional, Protocol
from abc import ABC, abstractmethod
from poker_types import Result, ComponentType, HealthStatus, ComponentConfig
from interfaces import IDataProcessor


class DataProcessingContext:
    """
    데이터 처리 컨텍스트

    데이터 처리 작업의 컨텍스트 정보를 담는 클래스입니다.
    처리 과정의 메타데이터, 히스토리, 성능 정보를 관리합니다.

    Attributes:
        data: 처리할 데이터
        metadata: 추가 메타데이터
        processing_history: 처리 단계 히스토리
        start_time: 처리 시작 시각
        end_time: 처리 종료 시각
    """

    def __init__(self, data: Any, metadata: Dict[str, Any] = None):
        self.data = data
        self.metadata = metadata or {}
        self.processing_history: List[str] = []
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def add_processing_step(self, step: str) -> None:
        """
        처리 단계 추가

        처리 히스토리에 새로운 단계를 추가합니다.

        Args:
            step: 처리 단계 설명
        """
        self.processing_history.append(step)

    def get_processing_time(self) -> float:
        """
        총 처리 시간 조회

        처리 시작부터 종료까지의 총 시간을 반환합니다.

        Returns:
            float: 처리 시간 (초)
        """
        return self.end_time - self.start_time if self.end_time > 0 else 0.0


class IDataProcessingStrategy(Protocol):
    """
    데이터 처리 전략 인터페이스

    Strategy 패턴의 전략 인터페이스입니다.
    다양한 데이터 처리 알고리즘을 위한 표준 인터페이스를 정의합니다.
    """

    @property
    def strategy_name(self) -> str:
        """
        전략 이름

        전략의 고유 식별자입니다.

        Returns:
            str: 전략 이름
        """
        ...

    @property
    def strategy_type(self) -> str:
        """
        전략 타입

        전략의 카테고리나 타입입니다.

        Returns:
            str: 전략 타입
        """
        ...

    async def process(self, context: DataProcessingContext) -> Result[Any, str]:
        """
        데이터 처리

        주어진 컨텍스트를 사용하여 데이터를 처리합니다.

        Args:
            context: 처리 컨텍스트

        Returns:
            Result[Any, str]: 처리 결과 또는 에러
        """
        ...

    def can_handle(self, data_type: str, context: Dict[str, Any] = None) -> bool:
        """
        처리 가능 여부 확인

        이 전략이 주어진 데이터 타입을 처리할 수 있는지 확인합니다.

        Args:
            data_type: 데이터 타입
            context: 추가 컨텍스트 정보

        Returns:
            bool: 처리 가능 여부
        """
        ...


class BaseDataProcessingStrategy(ABC):
    """
    데이터 처리 전략 기본 클래스

    모든 데이터 처리 전략의 기본 구현을 제공하는 추상 기본 클래스입니다.
    공통 기능을 구현하고 서브클래스에서 구체적인 처리 로직을 구현하도록 합니다.

    Attributes:
        _name: 전략 이름
        _strategy_type: 전략 타입
    """

    def __init__(self, name: str, strategy_type: str):
        self._name = name
        self._strategy_type = strategy_type

    @property
    def strategy_name(self) -> str:
        """전략 이름"""
        return self._name

    @property
    def strategy_type(self) -> str:
        """전략 타입"""
        return self._strategy_type

    @abstractmethod
    async def process(self, context: DataProcessingContext) -> Result[Any, str]:
        """
        데이터 처리

        주어진 컨텍스트를 사용하여 데이터를 처리합니다.

        Args:
            context: 처리 컨텍스트

        Returns:
            Result[Any, str]: 처리 결과 또는 에러
        """
        pass

    @abstractmethod
    def can_handle(self, data_type: str, context: Dict[str, Any] = None) -> bool:
        """
        처리 가능 여부 확인

        이 전략이 주어진 데이터 타입을 처리할 수 있는지 확인합니다.

        Args:
            data_type: 데이터 타입
            context: 추가 컨텍스트 정보

        Returns:
            bool: 처리 가능 여부
        """
        pass


class DataProcessingStrategyRegistry:
    """
    데이터 처리 전략 레지스트리

    데이터 처리 전략들을 등록하고 관리하는 중앙 레지스트리입니다.
    전략 이름과 타입별로 전략을 검색하고 사용할 수 있습니다.

    Attributes:
        _strategies: 전략 이름으로 인덱싱된 전략 딕셔너리
        _strategies_by_type: 전략 타입별 전략 목록 딕셔너리
    """

    def __init__(self):
        self._strategies: Dict[str, IDataProcessingStrategy] = {}
        self._strategies_by_type: Dict[str, List[IDataProcessingStrategy]] = {}

    def register_strategy(self, strategy: IDataProcessingStrategy) -> Result[bool, str]:
        """
        전략 등록

        새로운 데이터 처리 전략을 레지스트리에 등록합니다.

        Args:
            strategy: 등록할 전략 인스턴스

        Returns:
            Result[bool, str]: 등록 성공 여부
        """
        try:
            if strategy.strategy_name in self._strategies:
                return Result.err(f"Strategy {strategy.strategy_name} already registered")

            self._strategies[strategy.strategy_name] = strategy

            # Also index by type
            if strategy.strategy_type not in self._strategies_by_type:
                self._strategies_by_type[strategy.strategy_type] = []
            self._strategies_by_type[strategy.strategy_type].append(strategy)

            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to register strategy: {str(e)}")

    def get_strategy(self, name: str) -> Optional[IDataProcessingStrategy]:
        """
        전략 조회

        이름으로 전략을 조회합니다.

        Args:
            name: 조회할 전략 이름

        Returns:
            Optional[IDataProcessingStrategy]: 찾은 전략 또는 None
        """
        return self._strategies.get(name)

    def get_strategies_by_type(self, strategy_type: str) -> List[IDataProcessingStrategy]:
        """
        타입별 전략 목록 조회

        지정된 타입의 모든 전략을 반환합니다.

        Args:
            strategy_type: 전략 타입

        Returns:
            List[IDataProcessingStrategy]: 해당 타입의 전략 목록
        """
        return self._strategies_by_type.get(strategy_type, [])

    def find_suitable_strategy(self, data_type: str, context: Dict[str, Any] = None) -> Optional[IDataProcessingStrategy]:
        """
        적합한 전략 찾기

        주어진 데이터 타입을 처리할 수 있는 전략을 찾습니다.

        Args:
            data_type: 데이터 타입
            context: 추가 컨텍스트 정보

        Returns:
            Optional[IDataProcessingStrategy]: 적합한 전략 또는 None
        """
        for strategy in self._strategies.values():
            if strategy.can_handle(data_type, context):
                return strategy
        return None

    def get_all_strategies(self) -> List[IDataProcessingStrategy]:
        """
        모든 전략 조회

        등록된 모든 전략을 반환합니다.

        Returns:
            List[IDataProcessingStrategy]: 모든 전략 목록
        """
        return list(self._strategies.values())

    def unregister_strategy(self, name: str) -> Result[bool, str]:
        """
        전략 등록 해제

        지정된 전략을 레지스트리에서 제거합니다.

        Args:
            name: 제거할 전략 이름

        Returns:
            Result[bool, str]: 제거 성공 여부
        """
        try:
            if name not in self._strategies:
                return Result.err(f"Strategy {name} not found")

            strategy = self._strategies[name]

            # Remove from type index
            if strategy.strategy_type in self._strategies_by_type:
                self._strategies_by_type[strategy.strategy_type].remove(strategy)
                if not self._strategies_by_type[strategy.strategy_type]:
                    del self._strategies_by_type[strategy.strategy_type]

            # Remove from main registry
            del self._strategies[name]

            return Result.success(True)
        except Exception as e:
            return Result.err(f"Failed to unregister strategy: {str(e)}")


class StrategyDataProcessor(IDataProcessor):
    """
    전략 패턴 데이터 프로세서

    Strategy 패턴을 사용하여 다양한 데이터 타입에 대한 유연한 처리를 제공하는 데이터 프로세서입니다.
    전략 레지스트리를 통해 데이터 타입별로 적절한 처리 알고리즘을 선택합니다.

    Attributes:
        _registry: 전략 레지스트리
        _default_strategies: 데이터 타입별 기본 전략 매핑
        _health_status: 컴포넌트 건강 상태
    """

    def __init__(self, registry: DataProcessingStrategyRegistry):
        self._registry = registry
        self._default_strategies: Dict[str, str] = {}  # data_type -> strategy_name
        self._health_status = HealthStatus.HEALTHY

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.DATA_STORE  # Using existing type, could add new one

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """Initialize the data processor"""
        try:
            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to initialize StrategyDataProcessor: {str(e)}")

    async def start(self) -> Result[bool, str]:
        """Start the data processor"""
        return Result.ok(True)

    async def stop(self) -> Result[bool, str]:
        """Stop the data processor"""
        return Result.ok(True)

    async def shutdown(self) -> Result[bool, str]:
        """Shutdown the data processor"""
        try:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to shutdown StrategyDataProcessor: {str(e)}")

    async def process_data(self, data: Any, data_type: str, context: Dict[str, Any] = None) -> Result[Any, str]:
        """Process data using appropriate strategy"""
        try:
            processing_context = DataProcessingContext(data, context)

            # Find suitable strategy
            strategy = None

            # First try default strategy for this data type
            if data_type in self._default_strategies:
                strategy_name = self._default_strategies[data_type]
                strategy = self._registry.get_strategy(strategy_name)

            # If no default or default not found, find any suitable strategy
            if not strategy:
                strategy = self._registry.find_suitable_strategy(data_type, context)

            if not strategy:
                return Result.err(f"No suitable strategy found for data type: {data_type}")

            # Process the data
            processing_context.add_processing_step(f"Using strategy: {strategy.strategy_name}")
            result = await strategy.process(processing_context)

            if result.success:
                processing_context.add_processing_step("Processing completed successfully")
            else:
                processing_context.add_processing_step(f"Processing failed: {result.error}")

            return result

        except Exception as e:
            return Result.err(f"Data processing failed: {str(e)}")

    def set_default_strategy(self, data_type: str, strategy_name: str) -> Result[bool, str]:
        """Set default strategy for a data type"""
        try:
            if strategy_name not in self._registry._strategies:
                return Result.err(f"Strategy {strategy_name} not registered")

            self._default_strategies[data_type] = strategy_name
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to set default strategy: {str(e)}")

    def get_available_strategies(self, data_type: str = None) -> List[str]:
        """Get available strategy names"""
        if data_type:
            strategies = self._registry.get_strategies_by_type(data_type)
            return [s.strategy_name for s in strategies]
        else:
            return list(self._registry._strategies.keys())


# Example concrete strategies

class OCRProcessingStrategy(BaseDataProcessingStrategy):
    """Strategy for OCR data processing"""

    def __init__(self):
        super().__init__("ocr_processor", "text_extraction")

    async def process(self, context: DataProcessingContext) -> Result[Any, str]:
        """Process OCR data"""
        try:
            # Simulate OCR processing
            if not isinstance(context.data, (str, bytes)):
                return Result.err("OCR strategy requires string or bytes data")

            # Add processing metadata
            context.metadata['processed_by'] = 'OCRProcessingStrategy'
            context.metadata['processing_steps'] = ['text_extraction', 'validation']

            # Simple text processing (in real implementation, this would use OCR library)
            processed_text = str(context.data).upper() if isinstance(context.data, str) else context.data.decode('utf-8', errors='ignore').upper()

            return Result.ok({
                'text': processed_text,
                'confidence': 0.95,
                'metadata': context.metadata
            })

        except Exception as e:
            return Result.err(f"OCR processing failed: {str(e)}")

    def can_handle(self, data_type: str, context: Dict[str, Any] = None) -> bool:
        return data_type in ['image', 'screenshot', 'ocr_data']


class HUDDisplayStrategy(BaseDataProcessingStrategy):
    """Strategy for HUD display data processing"""

    def __init__(self):
        super().__init__("hud_display", "visualization")

    async def process(self, context: DataProcessingContext) -> Result[Any, str]:
        """Process HUD display data"""
        try:
            if not isinstance(context.data, dict):
                return Result.err("HUD strategy requires dictionary data")

            # Validate required fields
            required_fields = ['player_name', 'position', 'stack_size']
            for field in required_fields:
                if field not in context.data:
                    return Result.err(f"Missing required field: {field}")

            # Process HUD data
            context.metadata['processed_by'] = 'HUDDisplayStrategy'
            context.metadata['display_ready'] = True

            # Format display data
            display_data = {
                'player_info': context.data,
                'visual_elements': ['avatar', 'stats', 'range_indicator'],
                'position': context.data.get('position'),
                'metadata': context.metadata
            }

            return Result.ok(display_data)

        except Exception as e:
            return Result.err(f"HUD processing failed: {str(e)}")

    def can_handle(self, data_type: str, context: Dict[str, Any] = None) -> bool:
        return data_type in ['player_data', 'hud_data', 'game_state']


class DataProcessingStrategyBuilder:
    """Builder for configuring data processing strategies"""

    def __init__(self):
        self._registry = DataProcessingStrategyRegistry()
        self._processor = StrategyDataProcessor(self._registry)

    def add_strategy(self, strategy: IDataProcessingStrategy) -> 'DataProcessingStrategyBuilder':
        """Add a strategy to the registry"""
        result = self._registry.register_strategy(strategy)
        if not result.success:
            raise ValueError(f"Failed to add strategy: {result.error}")
        return self

    def set_default_strategy(self, data_type: str, strategy_name: str) -> 'DataProcessingStrategyBuilder':
        """Set default strategy for a data type"""
        result = self._processor.set_default_strategy(data_type, strategy_name)
        if not result.success:
            raise ValueError(f"Failed to set default strategy: {result.error}")
        return self

    def build_processor(self) -> StrategyDataProcessor:
        """Build the configured data processor"""
        return self._processor

    def build_registry(self) -> DataProcessingStrategyRegistry:
        """Build the configured strategy registry"""
        return self._registry
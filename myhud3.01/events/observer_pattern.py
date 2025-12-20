"""
Observer Pattern Implementation
Enhanced event system with observer pattern for reactive programming
"""

from typing import Dict, List, Callable, Any, Optional, Set
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
from poker_types import Result, ComponentType, HealthStatus, ComponentConfig
from interfaces import IEventBus


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Event:
    """Event data structure"""

    def __init__(self, event_type: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL,
                 source: str = None, timestamp: float = None):
        self.event_type = event_type
        self.data = data
        self.priority = priority
        self.source = source
        self.timestamp = timestamp or asyncio.get_event_loop().time()

    def __repr__(self) -> str:
        return f"Event(type={self.event_type}, priority={self.priority.name}, source={self.source})"


class IObserver(ABC):
    """Observer interface"""

    @abstractmethod
    async def on_event(self, event: Event) -> None:
        """Handle event notification"""
        pass

    @property
    @abstractmethod
    def observer_id(self) -> str:
        """Unique observer identifier"""
        pass

    @property
    @abstractmethod
    def interested_events(self) -> Set[str]:
        """Set of event types this observer is interested in"""
        pass


class ISubject(ABC):
    """Subject interface for observer pattern"""

    @abstractmethod
    async def attach(self, observer: IObserver) -> Result[bool, str]:
        """Attach an observer"""
        pass

    @abstractmethod
    async def detach(self, observer: IObserver) -> Result[bool, str]:
        """Detach an observer"""
        pass

    @abstractmethod
    async def notify(self, event: Event) -> Result[bool, str]:
        """Notify all observers of an event"""
        pass

    @abstractmethod
    def get_observers(self, event_type: str = None) -> List[IObserver]:
        """Get list of observers, optionally filtered by event type"""
        pass


class EventSubject(ISubject):
    """Concrete subject implementation with priority-based event handling"""

    def __init__(self):
        self._observers: Dict[str, List[IObserver]] = {}
        self._event_queues: Dict[EventPriority, asyncio.PriorityQueue] = {
            priority: asyncio.PriorityQueue() for priority in EventPriority
        }
        self._processing_task: Optional[asyncio.Task] = None
        self._is_processing = False

    async def attach(self, observer: IObserver) -> Result[bool, str]:
        """Attach an observer to interested events"""
        try:
            for event_type in observer.interested_events:
                if event_type not in self._observers:
                    self._observers[event_type] = []
                self._observers[event_type].append(observer)
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to attach observer: {str(e)}")

    async def detach(self, observer: IObserver) -> Result[bool, str]:
        """Detach an observer from all events"""
        try:
            for event_type in list(self._observers.keys()):
                if observer in self._observers[event_type]:
                    self._observers[event_type].remove(observer)
                    # Clean up empty lists
                    if not self._observers[event_type]:
                        del self._observers[event_type]
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to detach observer: {str(e)}")

    async def notify(self, event: Event) -> Result[bool, str]:
        """Notify observers of an event"""
        try:
            # Queue event for processing
            priority_value = event.priority.value
            await self._event_queues[event.priority].put((priority_value, event))

            # Start processing if not already running
            if not self._is_processing:
                self._processing_task = asyncio.create_task(self._process_events())

            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to notify observers: {str(e)}")

    async def _process_events(self) -> None:
        """Process events from priority queues"""
        self._is_processing = True

        try:
            while True:
                # Get highest priority event
                event = None
                for priority in reversed(EventPriority):  # CRITICAL to LOW
                    try:
                        _, event = self._event_queues[priority].get_nowait()
                        break
                    except asyncio.QueueEmpty:
                        continue

                if event is None:
                    # No events in any queue, check if we should stop
                    all_empty = all(queue.empty() for queue in self._event_queues.values())
                    if all_empty:
                        break
                    else:
                        await asyncio.sleep(0.01)  # Small delay before checking again
                        continue

                # Notify observers
                if event.event_type in self._observers:
                    tasks = []
                    for observer in self._observers[event.event_type]:
                        task = asyncio.create_task(observer.on_event(event))
                        tasks.append(task)

                    # Wait for all observers to handle the event
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)

        finally:
            self._is_processing = False

    def get_observers(self, event_type: str = None) -> List[IObserver]:
        """Get list of observers"""
        if event_type:
            return self._observers.get(event_type, []).copy()
        else:
            # Return all observers (unique)
            all_observers = set()
            for observers in self._observers.values():
                all_observers.update(observers)
            return list(all_observers)

    async def shutdown(self) -> Result[bool, str]:
        """Shutdown the subject and cancel processing"""
        try:
            if self._processing_task and not self._processing_task.done():
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

            self._observers.clear()
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Shutdown failed: {str(e)}")

    async def shutdown(self) -> Result[bool, str]:
        """Shutdown the subject and cancel processing"""
        try:
            if self._processing_task and not self._processing_task.done():
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

            self._observers.clear()
            return Result.success(True)
        except Exception as e:
            return Result.err(f"Shutdown failed: {str(e)}")


class EventBusAdapter(IEventBus):
    """Adapter to make EventSubject compatible with existing IEventBus interface"""

    def __init__(self, subject: EventSubject):
        self._subject = subject
        self._health_status = HealthStatus.HEALTHY

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.EVENT_BUS

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """Initialize the event bus adapter"""
        try:
            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to initialize EventBusAdapter: {str(e)}")

    async def start(self) -> Result[bool, str]:
        """Start the event bus adapter"""
        return Result.ok(True)

    async def stop(self) -> Result[bool, str]:
        """Stop the event bus adapter"""
        return Result.ok(True)

    async def shutdown(self) -> Result[bool, str]:
        """Shutdown the event bus adapter"""
        try:
            shutdown_result = await self._subject.shutdown()
            if not shutdown_result.success:
                print(f"Warning: Failed to shutdown event subject: {shutdown_result.error}")
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to shutdown EventBusAdapter: {str(e)}")

    async def subscribe(self, event_type: str, callback: callable) -> Result[bool, str]:
        """Subscribe to an event type with a callback"""
        return await self._subject.attach(CallbackObserver(f"callback_{id(callback)}", {event_type}, callback))

    async def unsubscribe(self, event_type: str, callback: callable) -> Result[bool, str]:
        """Unsubscribe from an event type"""
        # Find and detach the callback observer
        observers = self._subject.get_observers(event_type)
        for observer in observers:
            if isinstance(observer, CallbackObserver) and observer._callback == callback:
                return await self._subject.detach(observer)
        return Result.err("Callback not found")

    async def publish(self, event: Event) -> Result[bool, str]:
        """Publish an event through the subject"""
        return await self._subject.notify(event)

    async def publish_event(self, event_type: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL) -> Result[bool, str]:
        """Publish an event through the subject (convenience method)"""
        event = Event(event_type=event_type, data=data, priority=priority)
        return await self._subject.notify(event)


class CallbackObserver(IObserver):
    """Simple observer that wraps a callback function"""

    def __init__(self, observer_id: str, interested_events: Set[str], callback: Callable[[Event], None]):
        self._observer_id = observer_id
        self._interested_events = interested_events
        self._callback = callback

    async def on_event(self, event: Event) -> None:
        """Handle event by calling the callback"""
        try:
            self._callback(event)
        except Exception as e:
            # Log error but don't let it crash the event system
            print(f"Error in callback observer {self._observer_id}: {str(e)}")

    @property
    def observer_id(self) -> str:
        return self._observer_id

    @property
    def interested_events(self) -> Set[str]:
        return self._interested_events
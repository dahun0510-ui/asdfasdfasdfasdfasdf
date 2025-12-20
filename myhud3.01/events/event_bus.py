# === Standard Library Imports ===
import asyncio
import time
import threading
from typing import Dict, List, Callable, Any, Optional, Set
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

# === Local Imports ===
from interfaces import IEventBus

class EventType(Enum):
    """이벤트 타입 열거형"""
    HUD_UPDATE = "hud_update"
    PLAYER_DATA_UPDATE = "player_data_update"
    SCAN_COMPLETE = "scan_complete"
    ERROR_OCCURRED = "error_occurred"
    CONFIG_CHANGED = "config_changed"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"

class Event:
    """이벤트 클래스"""

    def __init__(self, event_type: EventType, data: Optional[Any] = None,
                 source: Optional[str] = None):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = time.time()  # 결정적 타임스탬프 생성

class EventBus(IEventBus):
    """이벤트 버스 구현"""

    def __init__(self):
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._lock = threading.Lock()
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._event_loop_task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: str, callback: Callable) -> bool:
        """이벤트 구독"""
        try:
            with self._lock:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = set()
                self._subscribers[event_type].add(callback)
            return True
        except Exception as e:
            print(f"Failed to subscribe to {event_type}: {e}")
            return False

    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """이벤트 구독 해제"""
        try:
            with self._lock:
                if event_type in self._subscribers:
                    self._subscribers[event_type].discard(callback)
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]
            return True
        except Exception as e:
            print(f"Failed to unsubscribe from {event_type}: {e}")
            return False

    def publish(self, event: Event) -> bool:
        """이벤트 발행 (동기)"""
        try:
            event_type_str = event.event_type.value
            with self._lock:
                if event_type_str in self._subscribers:
                    for callback in self._subscribers[event_type_str].copy():
                        try:
                            # 비동기로 콜백 실행
                            if asyncio.iscoroutinefunction(callback):
                                asyncio.create_task(callback(event))
                            else:
                                self._executor.submit(callback, event)
                        except Exception as e:
                            print(f"Error in event callback: {e}")
            return True
        except Exception as e:
            print(f"Failed to publish event {event.event_type}: {e}")
            return False

    async def publish_async(self, event: Event) -> bool:
        """이벤트 발행 (비동기)"""
        try:
            await self._event_queue.put(event)
            return True
        except Exception as e:
            print(f"Failed to publish async event {event.event_type}: {e}")
            return False

    def start_event_loop(self) -> bool:
        """이벤트 루프 시작"""
        try:
            if self._running:
                return True

            # 이미 이벤트 루프가 실행 중인지 확인
            try:
                loop = asyncio.get_running_loop()
                # 이미 실행 중인 루프가 있으면 새로운 태스크로 처리
                self._event_loop_task = loop.create_task(self._process_events())
                self._running = True
                return True
            except RuntimeError:
                # 실행 중인 루프가 없으면 새로 생성
                pass

            self._running = True
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._event_loop_task = loop.create_task(self._process_events())
            loop.run_until_complete(self._event_loop_task)
            return True
        except Exception as e:
            print(f"Failed to start event loop: {e}")
            return False

    def stop_event_loop(self) -> bool:
        """이벤트 루프 중지"""
        try:
            self._running = False
            if self._event_loop_task:
                self._event_loop_task.cancel()
            self._executor.shutdown(wait=True)
            return True
        except Exception as e:
            print(f"Failed to stop event loop: {e}")
            return False

    async def _process_events(self):
        """이벤트 처리 루프"""
        while self._running:
            try:
                event = await self._event_queue.get()
                await self._handle_event(event)
                self._event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")

    async def _handle_event(self, event: Event):
        """이벤트 처리"""
        event_type_str = event.event_type.value
        with self._lock:
            if event_type_str in self._subscribers:
                tasks = []
                for callback in self._subscribers[event_type_str].copy():
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            tasks.append(callback(event))
                        else:
                            # 동기 콜백을 비동기로 실행
                            tasks.append(asyncio.get_event_loop().run_in_executor(
                                self._executor, callback, event))
                    except Exception as e:
                        print(f"Error in async event callback: {e}")

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

    def get_subscriber_count(self, event_type: str) -> int:
        """특정 이벤트 타입의 구독자 수"""
        with self._lock:
            return len(self._subscribers.get(event_type, set()))

    def get_all_event_types(self) -> List[str]:
        """등록된 모든 이벤트 타입"""
        with self._lock:
            return list(self._subscribers.keys())

    def clear_subscribers(self, event_type: Optional[str] = None) -> bool:
        """구독자 클리어"""
        try:
            with self._lock:
                if event_type:
                    self._subscribers.pop(event_type, None)
                else:
                    self._subscribers.clear()
            return True
        except Exception as e:
            print(f"Failed to clear subscribers: {e}")
            return False

    def shutdown(self) -> bool:
        """리소스 정리"""
        try:
            # 실행 중인 태스크 취소
            if self._event_loop_task and not self._event_loop_task.done():
                self._event_loop_task.cancel()

            # ThreadPoolExecutor 종료
            if hasattr(self, '_executor') and self._executor:
                self._executor.shutdown(wait=True)

            self._running = False
            return True
        except Exception as e:
            print(f"Failed to shutdown EventBus: {e}")
            return False
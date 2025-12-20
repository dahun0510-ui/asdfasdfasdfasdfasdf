# === Standard Library Imports ===
import asyncio
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue

# === Local Imports ===
from interfaces import ICoreComponent
from poker_types import Result, ComponentType, ComponentConfig, HealthStatus


class TaskPriority(Enum):
    """작업 우선순위 레벨"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskType(Enum):
    """작업 타입 분류"""
    IO_BOUND = "io_bound"      # I/O 바운드 (네트워크, 파일, DB)
    CPU_BOUND = "cpu_bound"    # CPU 바운드 (계산, 이미지 처리)
    GPU_BOUND = "gpu_bound"    # GPU 바운드 (그래픽 처리)
    REAL_TIME = "real_time"    # 실시간 (HUD 업데이트)


@dataclass
class Task:
    """
    비동기 작업 데이터 클래스

    각 작업의 상태와 메타데이터를 관리합니다.

    Attributes:
        id: 고유 작업 식별자
        type: 작업 타입 (I/O, CPU, GPU, 실시간)
        priority: 작업 우선순위
        coroutine: 실행할 코루틴 함수
        timeout: 작업 타임아웃 (초)
        created_at: 작업 생성 시간
        started_at: 작업 시작 시간
        completed_at: 작업 완료 시간
        result: 작업 결과
        error: 작업 에러 (실패 시)
        retry_count: 재시도 횟수
        max_retries: 최대 재시도 횟수
    """
    id: str
    type: TaskType
    priority: TaskPriority
    coroutine: Callable[[], Awaitable[Any]]
    timeout: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 3

    @property
    def is_completed(self) -> bool:
        """작업 완료 여부"""
        return self.completed_at is not None

    @property
    def is_failed(self) -> bool:
        return self.error is not None

    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

class WorkerPool:
    """워커 풀 - 다양한 작업 타입별로 최적화된 실행기 관리"""

    def __init__(self):
        # I/O 바운드 작업용 (네트워크, 파일, DB)
        self.io_executor = ThreadPoolExecutor(
            max_workers=20,
            thread_name_prefix="IO-Worker"
        )

        # CPU 바운드 작업용 (계산, 이미지 처리)
        self.cpu_executor = ProcessPoolExecutor(
            max_workers=4,  # CPU 코어 수에 맞춤
            initializer=self._cpu_worker_init
        )

        # GPU 바운드 작업용 (향후 확장)
        self.gpu_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="GPU-Worker"
        )

class WorkerPool:
    """
    작업자 풀 - 다양한 작업 타입에 특화된 실행기 관리

    I/O 바운드, CPU 바운드, GPU 바운드, 실시간 작업을 위한
    별도의 스레드/프로세스 풀을 관리합니다.

    Attributes:
        io_executor: I/O 바운드 작업용 스레드 풀
        cpu_executor: CPU 바운드 작업용 프로세스 풀
        gpu_executor: GPU 바운드 작업용 스레드 풀
        realtime_executor: 실시간 작업용 스레드 풀
    """

    def __init__(self) -> None:
        """WorkerPool 초기화"""
        # I/O 바운드 작업용 (스레드 풀)
        self.io_executor = ThreadPoolExecutor(
            max_workers=16,
            thread_name_prefix="IO-Worker"
        )

        # CPU 바운드 작업용 (프로세스 풀)
        self.cpu_executor = ProcessPoolExecutor(
            max_workers=4,
            initializer=self._cpu_worker_init,
            initargs=()
        )

        # GPU 바운드 작업용 (스레드 풀)
        self.gpu_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="GPU-Worker"
        )

        # 실시간 작업용 (별도 스레드)
        self.realtime_executor = ThreadPoolExecutor(
            max_workers=8,
            thread_name_prefix="RT-Worker"
        )

    def _cpu_worker_init(self) -> None:
        """CPU 워커 프로세스 초기화"""
        import os
        # CPU 워커 프로세스 설정
        os.nice(10)  # 낮은 우선순위

    async def execute_io_task(self, func: Callable, *args, **kwargs) -> Any:
        """I/O 바운드 작업 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.io_executor, func, *args, **kwargs
        )

    async def execute_cpu_task(self, func: Callable, *args, **kwargs) -> Any:
        """CPU 바운드 작업 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.cpu_executor, func, *args, **kwargs
        )

    async def execute_gpu_task(self, func: Callable, *args, **kwargs) -> Any:
        """GPU 바운드 작업 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.gpu_executor, func, *args, **kwargs
        )

    async def execute_realtime_task(self, func: Callable, *args, **kwargs) -> Any:
        """실시간 작업 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.realtime_executor, func, *args, **kwargs
        )

    def shutdown(self) -> None:
        """모든 실행기 종료"""
        self.io_executor.shutdown(wait=True)
        self.cpu_executor.shutdown(wait=True)
        self.gpu_executor.shutdown(wait=True)
        self.realtime_executor.shutdown(wait=True)

class AsyncTaskQueue(ICoreComponent):
    """
    비동기 작업 큐 - 우선순위 기반 작업 관리 시스템

    다양한 우선순위의 작업을 관리하고, 특화된 워커 풀을 통해
    효율적으로 실행합니다. 작업 완료 시 콜백을 지원합니다.

    Attributes:
        _component_type: 컴포넌트 타입 (DATA_FLOW)
        _health_status: 컴포넌트 건강 상태
        _running: 실행 상태
        _queues: 우선순위별 작업 큐들
        _worker_pool: 특화된 작업 실행기 풀
        _active_tasks: 현재 실행 중인 작업들
        _completed_tasks: 완료된 작업들
        _failed_tasks: 실패한 작업들
        _performance_stats: 성능 통계
        _worker_tasks: 워커 태스크들
        _monitor_task: 모니터링 태스크
    """

    def __init__(self):
        self._component_type = ComponentType.DATA_FLOW
        self._health_status = HealthStatus.HEALTHY
        self._running = False

        # 작업 큐들 (우선순위별)
        self._queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }

        # 작업 워커 풀
        self._worker_pool = WorkerPool()

        # 작업 추적
        self._active_tasks: Dict[str, Task] = {}
        self._completed_tasks: List[Task] = []
        self._failed_tasks: List[Task] = []

        # 성능 모니터링
        self._performance_stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "avg_completion_time": 0.0,
            "queue_sizes": {p.value: 0 for p in TaskPriority}
        }

        # 워커 태스크들
        self._worker_tasks: List[asyncio.Task] = []
        self._monitor_task: Optional[asyncio.Task] = None

    @property
    def component_type(self) -> ComponentType:
        return self._component_type

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """초기화"""
        try:
            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to initialize TaskQueue: {str(e)}")

    async def start(self) -> Result[bool, str]:
        """시작"""
        try:
            if self._running:
                return Result.ok(True)

            self._running = True

            # 워커 태스크 시작
            for priority in TaskPriority:
                worker_task = asyncio.create_task(
                    self._process_queue(priority),
                    name=f"TaskQueue-Worker-{priority.value}"
                )
                self._worker_tasks.append(worker_task)

            # 모니터링 태스크 시작
            self._monitor_task = asyncio.create_task(
                self._monitor_performance(),
                name="TaskQueue-Monitor"
            )

            self._health_status = HealthStatus.HEALTHY
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to start TaskQueue: {str(e)}")

    async def stop(self) -> Result[bool, str]:
        """중지"""
        try:
            if not self._running:
                return Result.ok(True)

            self._running = False

            # 모든 워커 태스크 취소
            for task in self._worker_tasks:
                task.cancel()
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

            # 모니터링 태스크 취소
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass

            self._health_status = HealthStatus.DEGRADED
            return Result.ok(True)
        except Exception as e:
            self._health_status = HealthStatus.UNHEALTHY
            return Result.err(f"Failed to stop TaskQueue: {str(e)}")

    async def shutdown(self) -> Result[bool, str]:
        """종료"""
        try:
            await self.stop()
            self._worker_pool.shutdown()
            self._active_tasks.clear()
            self._completed_tasks.clear()
            self._failed_tasks.clear()
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)
        except Exception as e:
            return Result.err(f"Failed to shutdown TaskQueue: {str(e)}")

    async def submit_task(self, task: Task) -> Result[str, str]:
        """
        작업 제출

        지정된 작업을 적절한 우선순위 큐에 제출합니다.

        Args:
            task: 제출할 작업 객체

        Returns:
            Result[str, str]: 성공 시 작업 ID, 실패 시 에러 메시지
        """
        try:
            if not self._running:
                return Result.err("TaskQueue is not running")

            await self._queues[task.priority].put(task)
            self._active_tasks[task.id] = task
            self._performance_stats["total_tasks"] += 1

            return Result.ok(task.id)
        except Exception as e:
            return Result.err(f"Failed to submit task: {str(e)}")

    async def get_task_status(self, task_id: str) -> Result[Optional[Task], str]:
        """
        작업 상태 조회

        지정된 ID의 작업 상태를 조회합니다.

        Args:
            task_id: 조회할 작업의 ID

        Returns:
            Result[Optional[Task], str]: 성공 시 작업 객체 (또는 None), 실패 시 에러 메시지
        """
        try:
            if task_id in self._active_tasks:
                return Result.ok(self._active_tasks[task_id])

            # 완료된 작업에서 찾기
            for task in self._completed_tasks + self._failed_tasks:
                if task.id == task_id:
                    return Result.ok(task)

            return Result.ok(None)
        except Exception as e:
            return Result.err(f"Failed to get task status: {str(e)}")

    async def cancel_task(self, task_id: str) -> Result[bool, str]:
        """작업 취소"""
        try:
            if task_id in self._active_tasks:
                task = self._active_tasks[task_id]
                # 실제 취소는 어려움 - 플래그만 설정
                task.error = Exception("Task cancelled")
                task.completed_at = time.time()
                return Result.ok(True)
            return Result.ok(False)
        except Exception as e:
            return Result.err(f"Failed to cancel task: {str(e)}")

    async def _process_queue(self, priority: TaskPriority):
        """큐 처리 워커"""
        while self._running:
            try:
                # 작업 가져오기 (타임아웃으로 중지 신호 확인)
                task = await asyncio.wait_for(
                    self._queues[priority].get(),
                    timeout=1.0
                )

                # 작업 실행
                await self._execute_task(task)
                self._queues[priority].task_done()

            except asyncio.TimeoutError:
                continue  # 타임아웃은 정상
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in queue processor: {str(e)}")

    async def _execute_task(self, task: Task):
        """작업 실행"""
        try:
            task.started_at = time.time()

            # 타임아웃 설정
            if task.timeout:
                result = await asyncio.wait_for(
                    task.coroutine(),
                    timeout=task.timeout
                )
            else:
                result = await task.coroutine()

            task.result = result
            task.completed_at = time.time()

            # 성공 처리
            self._completed_tasks.append(task)
            self._performance_stats["completed_tasks"] += 1

        except Exception as e:
            task.error = e
            task.completed_at = time.time()

            # 실패 처리
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                # 재시도 큐에 다시 넣기
                await self._queues[task.priority].put(task)
            else:
                self._failed_tasks.append(task)
                self._performance_stats["failed_tasks"] += 1

        finally:
            # 활성 작업에서 제거
            if task.id in self._active_tasks:
                del self._active_tasks[task.id]

    async def _monitor_performance(self):
        """성능 모니터링"""
        while self._running:
            try:
                await asyncio.sleep(5)  # 5초마다 모니터링

                # 큐 크기 업데이트
                for priority in TaskPriority:
                    self._performance_stats["queue_sizes"][priority.value] = \
                        self._queues[priority].qsize()

                # 평균 완료 시간 계산
                if self._completed_tasks:
                    total_time = sum(
                        task.duration for task in self._completed_tasks
                        if task.duration is not None
                    )
                    self._performance_stats["avg_completion_time"] = \
                        total_time / len(self._completed_tasks)

                # 오래된 완료 작업 정리 (메모리 관리)
                cutoff_time = time.time() - 3600  # 1시간 전
                self._completed_tasks = [
                    task for task in self._completed_tasks
                    if task.completed_at > cutoff_time
                ]
                self._failed_tasks = [
                    task for task in self._failed_tasks
                    if task.completed_at > cutoff_time
                ]

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Performance monitoring error: {str(e)}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        return self._performance_stats.copy()

    def get_queue_sizes(self) -> Dict[str, int]:
        """큐 크기 조회"""
        return self._performance_stats["queue_sizes"].copy()

    # === 편의 메서드들 ===

    async def submit_io_task(self, coroutine: Callable[[], Awaitable[Any]],
                           task_id: str, priority: TaskPriority = TaskPriority.NORMAL,
                           timeout: Optional[float] = None) -> Result[str, str]:
        """
        I/O 작업 제출

        I/O 바운드 작업을 쉽게 제출하기 위한 편의 메소드입니다.

        Args:
            coroutine: 실행할 코루틴 함수
            task_id: 작업 ID
            priority: 작업 우선순위 (기본값: NORMAL)
            timeout: 타임아웃 시간 (초, 기본값: None)

        Returns:
            Result[str, str]: 성공 시 작업 ID, 실패 시 에러 메시지
        """
        task = Task(
            id=task_id,
            type=TaskType.IO_BOUND,
            priority=priority,
            coroutine=coroutine,
            timeout=timeout
        )
        return await self.submit_task(task)

    async def submit_cpu_task(self, coroutine: Callable[[], Awaitable[Any]],
                            task_id: str, priority: TaskPriority = TaskPriority.NORMAL,
                            timeout: Optional[float] = None) -> Result[str, str]:
        """
        CPU 작업 제출

        CPU 바운드 작업을 쉽게 제출하기 위한 편의 메소드입니다.

        Args:
            coroutine: 실행할 코루틴 함수
            task_id: 작업 ID
            priority: 작업 우선순위 (기본값: NORMAL)
            timeout: 타임아웃 시간 (초, 기본값: None)

        Returns:
            Result[str, str]: 성공 시 작업 ID, 실패 시 에러 메시지
        """
        task = Task(
            id=task_id,
            type=TaskType.CPU_BOUND,
            priority=priority,
            coroutine=coroutine,
            timeout=timeout
        )
        return await self.submit_task(task)

    async def submit_realtime_task(self, coroutine: Callable[[], Awaitable[Any]],
                                 task_id: str, timeout: Optional[float] = None) -> Result[str, str]:
        """
        실시간 작업 제출

        실시간 작업을 쉽게 제출하기 위한 편의 메소드입니다.
        자동으로 HIGH 우선순위가 설정됩니다.

        Args:
            coroutine: 실행할 코루틴 함수
            task_id: 작업 ID
            timeout: 타임아웃 시간 (초, 기본값: None)

        Returns:
            Result[str, str]: 성공 시 작업 ID, 실패 시 에러 메시지
        """
        task = Task(
            id=task_id,
            type=TaskType.REAL_TIME,
            priority=TaskPriority.HIGH,
            coroutine=coroutine,
            timeout=timeout
        )
        return await self.submit_task(task)

    async def shutdown(self) -> Result[bool, str]:
        """리소스 정리 및 종료"""
        try:
            self._running = False

            # 모니터링 태스크 취소
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()

            # 워커 태스크들 취소
            for task in self._worker_tasks:
                if not task.done():
                    task.cancel()

            # 워커 풀 종료
            await self._worker_pool.shutdown()

            # 활성 태스크들 취소
            for task in self._active_tasks.values():
                # 태스크 취소 로직 (필요시 구현)

            self._active_tasks.clear()
            self._health_status = HealthStatus.UNHEALTHY
            return Result.ok(True)

        except Exception as e:
            return Result.err(f"Failed to shutdown AsyncTaskQueue: {str(e)}")
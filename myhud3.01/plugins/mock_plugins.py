#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
모의 플러그인 - GUI 없이 플러그인 시스템 테스트용
"""

from typing import Dict, Any, Optional
from .interfaces import IPlugin
from .poker_types import ComponentType, HealthStatus, Result, ComponentConfig

class MockHUDPlugin(IPlugin):
    """모의 HUD 플러그인"""

    def __init__(self):
        self._initialized = False
        self._started = False
        self._health_status = HealthStatus.HEALTHY

    def initialize(self, config: Dict[str, Any]) -> bool:
        """플러그인 초기화"""
        print(f"MockHUDPlugin 초기화: {config}")
        self._initialized = True
        return True

    def start(self) -> bool:
        """플러그인 시작"""
        if not self._initialized:
            return False
        print("MockHUDPlugin 시작")
        self._started = True
        return True

    def stop(self) -> bool:
        """플러그인 중지"""
        print("MockHUDPlugin 중지")
        self._started = False
        return True

    def shutdown(self) -> bool:
        """플러그인 종료"""
        print("MockHUDPlugin 종료")
        self._initialized = False
        return True

    @property
    def name(self) -> str:
        return "Mock HUD Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.PLUGIN_MANAGER  # 임시 값

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

class MockOCRPlugin(IPlugin):
    """모의 OCR 플러그인"""

    def __init__(self):
        self._initialized = False
        self._started = False
        self._health_status = HealthStatus.HEALTHY

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """플러그인 초기화"""
        print(f"MockOCRPlugin 초기화: {config}")
        self._initialized = True
        return Result.ok(True)

    async def start(self) -> Result[bool, str]:
        """플러그인 시작"""
        if not self._initialized:
            return Result.err("Plugin not initialized")
        print("MockOCRPlugin 시작")
        self._started = True
        return Result.ok(True)

    async def stop(self) -> Result[bool, str]:
        """플러그인 중지"""
        print("MockOCRPlugin 중지")
        self._started = False
        return Result.ok(True)

    async def shutdown(self) -> Result[bool, str]:
        """플러그인 종료"""
        print("MockOCRPlugin 종료")
        self._initialized = False
        return Result.ok(True)

    @property
    def name(self) -> str:
        return "Mock OCR Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.PLUGIN_MANAGER  # 임시 값

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status

class MockDataStorePlugin(IPlugin):
    """모의 데이터 저장소 플러그인"""

    def __init__(self):
        self._initialized = False
        self._started = False
        self._health_status = HealthStatus.HEALTHY

    async def initialize(self, config: ComponentConfig) -> Result[bool, str]:
        """플러그인 초기화"""
        print(f"MockDataStorePlugin 초기화: {config}")
        self._initialized = True
        return Result.ok(True)

    async def start(self) -> Result[bool, str]:
        """플러그인 시작"""
        if not self._initialized:
            return Result.err("Plugin not initialized")
        print("MockDataStorePlugin 시작")
        self._started = True
        return Result.ok(True)

    async def stop(self) -> Result[bool, str]:
        """플러그인 중지"""
        print("MockDataStorePlugin 중지")
        self._started = False
        return Result.ok(True)

    async def shutdown(self) -> Result[bool, str]:
        """플러그인 종료"""
        print("MockDataStorePlugin 종료")
        self._initialized = False
        return Result.ok(True)

    @property
    def name(self) -> str:
        return "Mock Data Store Plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def component_type(self) -> ComponentType:
        return ComponentType.PLUGIN_MANAGER  # 임시 값

    @property
    def health_status(self) -> HealthStatus:
        return self._health_status
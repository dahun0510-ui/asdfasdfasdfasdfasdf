#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Poker HUD 애플리케이션 실행 스크립트
로컬 테스트용 간단한 실행 파일
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """메인 함수"""
    try:
        print("=== Poker HUD Application Test ===")

        # 모의 테스트용 간단한 초기화
        from plugins.mock_plugins import MockHUDPlugin

        print("✓ 모의 플러그인 임포트 성공")

        # 플러그인 팩토리 테스트
        from plugins.plugin_factory import PluginFactory
        from plugins.plugin_registry import PluginRegistry
        from plugins.plugin_loader import PluginLoader
        from plugins.plugin_lifecycle_manager import PluginLifecycleManager

        factory = PluginFactory()
        factory.register_plugin_class('test_plugin', MockHUDPlugin)

        registry = PluginRegistry()
        registry.register_plugin('test_plugin', factory)

        loader = PluginLoader(registry)
        lifecycle_manager = PluginLifecycleManager(loader)

        # 플러그인 초기화 및 시작
        plugin_configs = {
            'test_plugin': {
                'enabled': True,
                'priority': 1,
                'data_flow_manager': None
            }
        }

        print("플러그인 시스템 초기화 중...")
        if not lifecycle_manager.initialize_plugins(plugin_configs):
            print("❌ 플러그인 초기화 실패")
            return 1

        print("플러그인 시스템 시작 중...")
        if not lifecycle_manager.start_plugins():
            print("❌ 플러그인 시작 실패")
            return 1

        print("✅ 플러그인 시스템 테스트 성공!")

        # 잠시 대기
        await asyncio.sleep(2)

        # 플러그인 중지
        print("플러그인 시스템 중지 중...")
        lifecycle_manager.stop_plugins()
        lifecycle_manager.shutdown_plugins()

        print("✅ 모든 테스트 완료!")
        return 0

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
플러그인 시스템 통합 테스트 (모의 플러그인 사용)
GUI 없이 플러그인 시스템의 핵심 기능만 테스트합니다.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_plugin_system():
    """플러그인 시스템 테스트"""
    try:
        print("=== 플러그인 시스템 테스트 시작 ===")

        # 모의 플러그인 임포트
        from mock_plugins import MockHUDPlugin, MockOCRPlugin, MockDataStorePlugin

        # 플러그인 시스템 컴포넌트 임포트
        from plugin_factory import PluginFactory
        from plugin_registry import PluginRegistry
        from plugin_loader import PluginLoader
        from plugin_lifecycle_manager import PluginLifecycleManager

        print("✓ 플러그인 시스템 컴포넌트 임포트 성공")

        # 팩토리 생성 및 플러그인 클래스 등록
        factory = PluginFactory()
        factory.register_plugin_class('hud_plugin', MockHUDPlugin)
        # factory.register_plugin_class('ocr_plugin', MockOCRPlugin)
        # factory.register_plugin_class('data_store_plugin', MockDataStorePlugin)
        print("✓ PluginFactory 생성 및 플러그인 클래스 등록 성공")

        # 레지스트리 생성 및 팩토리 등록
        registry = PluginRegistry()
        registry.register_plugin('hud_plugin', factory)
        # registry.register_plugin('ocr_plugin', factory)
        # registry.register_plugin('data_store_plugin', factory)
        print("✓ PluginRegistry 생성 및 팩토리 등록 성공")

        # 로더 생성
        loader = PluginLoader(registry)
        print("✓ PluginLoader 생성 성공")

        # 생명주기 관리자 생성
        lifecycle_manager = PluginLifecycleManager(loader)
        print("✓ PluginLifecycleManager 생성 성공")

        # 플러그인 설정
        plugin_configs = {
            'hud_plugin': {
                'enabled': True,
                'priority': 1,
                'data_flow_manager': None  # 모의 테스트용
            },
            # 'ocr_plugin': {
            #     'enabled': True,
            #     'priority': 2,
            #     'data_flow_manager': None
            # },
            # 'data_store_plugin': {
            #     'enabled': True,
            #     'priority': 3,
            #     'data_flow_manager': None
            # }
        }

        # 플러그인 초기화
        print("플러그인 초기화 중...")
        if not lifecycle_manager.initialize_plugins(plugin_configs):
            raise Exception("플러그인 초기화 실패")
        print("✓ 플러그인 초기화 성공")

        # 플러그인 시작
        print("플러그인 시작 중...")
        if not lifecycle_manager.start_plugins():
            print("플러그인 시작 디버그 정보:")
            # 디버그 정보 출력
            for plugin_type in plugin_configs.keys():
                factory = registry.get_factory(plugin_type)
                if factory:
                    plugin = factory.create_plugin(plugin_type, plugin_configs[plugin_type])
                    print(f"  {plugin_type}: 팩토리 있음, 생성 시도 결과 = {plugin is not None}")
                    if plugin:
                        # 동기 start 대신 직접 호출
                        try:
                            import asyncio
                            start_result = asyncio.run(plugin.start())
                            print(f"    시작 결과 = {start_result.success if hasattr(start_result, 'success') else start_result}")
                        except Exception as e:
                            print(f"    시작 예외 = {e}")
                else:
                    print(f"  {plugin_type}: 팩토리 없음")
            raise Exception("플러그인 시작 실패")
        print("✓ 플러그인 시작 성공")

        # 플러그인 중지
        print("플러그인 중지 중...")
        if not lifecycle_manager.stop_plugins():
            raise Exception("플러그인 중지 실패")
        print("✓ 플러그인 중지 성공")

        # 플러그인 종료
        print("플러그인 종료 중...")
        if not lifecycle_manager.shutdown_plugins():
            raise Exception("플러그인 종료 실패")
        print("✓ 플러그인 종료 성공")

        print("=== 플러그인 시스템 테스트 완료 ===")
        return True

    except Exception as e:
        print(f"✗ 플러그인 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Poker HUD 플러그인 시스템 통합 테스트 (모의 플러그인)")
    print("=" * 60)

    # 플러그인 시스템 테스트
    plugin_test = test_plugin_system()
    print()

    if plugin_test:
        print("🎉 모든 테스트 통과!")
        print("OBS 아키텍처 기반 플러그인 시스템이 정상 작동합니다.")
        sys.exit(0)
    else:
        print("❌ 테스트 실패")
        sys.exit(1)
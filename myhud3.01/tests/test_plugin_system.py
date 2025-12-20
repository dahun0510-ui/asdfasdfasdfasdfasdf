#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
플러그인 시스템 통합 테스트
GUI 없이 플러그인 시스템의 핵심 기능만 테스트합니다.
"""

import sys
import os
import logging
from pathlib import Path

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

        # 플러그인 시스템 컴포넌트 임포트
        from plugin_factory import PluginFactory
        from plugin_registry import PluginRegistry
        from plugin_loader import PluginLoader
        from plugin_lifecycle_manager import PluginLifecycleManager

        print("✓ 플러그인 시스템 컴포넌트 임포트 성공")

        # 팩토리 생성 및 플러그인 클래스 등록
        factory = PluginFactory()
        print("✓ PluginFactory 생성 성공")

        # 레지스트리 생성
        registry = PluginRegistry()
        print("✓ PluginRegistry 생성 성공")

        # 로더 생성
        loader = PluginLoader(registry)
        print("✓ PluginLoader 생성 성공")

        # 생명주기 관리자 생성
        lifecycle_manager = PluginLifecycleManager(loader)
        print("✓ PluginLifecycleManager 생성 성공")

        print("=== 플러그인 시스템 테스트 완료 ===")
        return True

    except Exception as e:
        print(f"✗ 플러그인 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_application_initialization():
    """애플리케이션 초기화 테스트"""
    try:
        print("=== 애플리케이션 초기화 테스트 시작 ===")

        # 메인 애플리케이션 임포트 (GUI 없이)
        from main import PokerHUDApplication

        print("✓ PokerHUDApplication 임포트 성공")

        # 애플리케이션 인스턴스 생성
        app = PokerHUDApplication()
        print("✓ PokerHUDApplication 인스턴스 생성 성공")

        # 기본 속성 확인
        print(f"✓ 애플리케이션 이름: {app.name}")
        print(f"✓ 애플리케이션 버전: {app.version}")

        print("=== 애플리케이션 초기화 테스트 완료 ===")
        return True

    except Exception as e:
        print(f"✗ 애플리케이션 초기화 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Poker HUD 플러그인 시스템 통합 테스트")
    print("=" * 50)

    # 플러그인 시스템 테스트
    plugin_test = test_plugin_system()
    print()

    # 애플리케이션 초기화 테스트
    app_test = test_application_initialization()
    print()

    if plugin_test and app_test:
        print("🎉 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("❌ 일부 테스트 실패")
        sys.exit(1)
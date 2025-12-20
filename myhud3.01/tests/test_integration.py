# === Standard Library Imports ===
import sys
import time
import signal

# === Local Imports ===
from main import PokerHUDApplication

def test_integration():
    """통합 테스트"""
    print("=== Poker HUD Integration Test Started ===")

    # 애플리케이션 초기화
    app = PokerHUDApplication()
    config = {
        "debug": True,
        "test_mode": True
    }

    try:
        # 초기화
        print("\n--- Initializing Application ---")
        if not app.initialize(config):
            print("❌ Failed to initialize application")
            return False

        # 시작
        print("\n--- Starting Application ---")
        if not app.start():
            print("❌ Failed to start application")
            return False

        # 상태 확인
        print("\n--- Checking Application Status ---")
        status = app.get_status()
        print(f"Application Status: {status}")

        # 플러그인 상태 확인
        if app.plugin_manager:
            active_plugins = app.plugin_manager.get_active_plugins()
            print(f"Active Plugins: {active_plugins}")

        # 데이터 플로우 상태 확인
        if app.data_flow_manager:
            stats = app.data_flow_manager.get_stats()
            print(f"Data Flow Stats: {stats}")

        # 테스트 데이터 처리
        print("\n--- Testing Data Flow ---")
        test_hud_data = {
            "position": "UTG",
            "stack": 1500,
            "action": "raise"
        }

        # 데이터 플로우로 HUD 데이터 전송
        if app.data_flow_manager:
            success = app.data_flow_manager.get_data_bus().send_data(
                "test_source", "hud_display", test_hud_data
            )
            print(f"HUD Data Send Success: {success}")

            # 상태 조회
            hud_state = app.data_flow_manager.get_hud_state("test_source")
            print(f"HUD State: {hud_state}")

        # 짧은 실행 후 중지
        print("\n--- Running for 2 seconds ---")
        time.sleep(2)

        print("\n--- Stopping Application ---")
        app.stop()

        print("\n=== Poker HUD Integration Test Completed Successfully ===")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        app.shutdown()

def test_plugin_lifecycle():
    """플러그인 생명주기 테스트"""
    print("=== Plugin Lifecycle Test ===")

    try:
        app = PokerHUDApplication()
        config = {
            "debug": True,
            "test_mode": True
        }

        # 초기화 및 시작
        if not app.initialize(config) or not app.start():
            print("❌ Failed to initialize/start application")
            return False

        # 플러그인 로드 확인
        if app.plugin_manager:
            active_plugins = app.plugin_manager.get_active_plugins()
            print(f"Active plugins: {active_plugins}")

            # 플러그인 재로드 테스트
            if active_plugins:
                plugin_name = list(active_plugins.keys())[0]
                success = app.plugin_manager.reload_plugin(plugin_name)
                print(f"Plugin reload success: {success}")

        time.sleep(1)
        app.stop()

        return True

    except Exception as e:
        print(f"Plugin lifecycle test failed: {e}")
        return False

    finally:
        app.shutdown()

def test_config_management():
    """설정 관리 테스트"""
    print("=== Configuration Management Test ===")

    try:
        from config import config_manager

        # 설정 조회
        hud_width = config_manager.get('hud_width')
        print(f"HUD width: {hud_width}")

        # 플러그인 설정 조회
        hud_plugin_config = config_manager.get_plugin_config('hud_plugin')
        print(f"HUD plugin config: {hud_plugin_config}")

        # 설정 변경 테스트
        success = config_manager.set('test_key', 'test_value')
        print(f"Set config: {'SUCCESS' if success else 'FAILED'}")

        # 변경된 값 확인
        test_value = config_manager.get('test_key')
        print(f"Retrieved test value: {test_value}")

        return True

    except Exception as e:
        print(f"Config management test failed: {e}")
        return False

def signal_handler(signum, frame):
    """시그널 핸들러"""
    print(f"\nReceived signal {signum}, stopping test...")
    sys.exit(0)

def main():
    """메인 함수"""
    # 시그널 핸들러 설정
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("Running Poker HUD Integration Tests...\n")

    # 설정 관리 테스트
    print("=" * 50)
    config_test = test_config_management()
    print(f"Configuration Test: {'PASSED' if config_test else 'FAILED'}\n")

    # 플러그인 생명주기 테스트
    print("=" * 50)
    plugin_test = test_plugin_lifecycle()
    print(f"Plugin Lifecycle Test: {'PASSED' if plugin_test else 'FAILED'}\n")

    # 통합 테스트
    print("=" * 50)
    integration_test = test_integration()
    print(f"Integration Test: {'PASSED' if integration_test else 'FAILED'}\n")

    # 최종 결과
    print("=" * 50)
    all_passed = config_test and plugin_test and integration_test
    print(f"Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
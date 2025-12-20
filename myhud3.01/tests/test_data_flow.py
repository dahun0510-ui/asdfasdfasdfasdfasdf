# === Standard Library Imports ===
import asyncio
from typing import Dict, Any

# === Local Imports ===
from data_flow_manager import DataFlowManager
from event_bus import EventType, Event
from state_manager import StateObserver, StateChange

class TestObserver(StateObserver):
    """테스트용 옵저버"""

    def __init__(self):
        self.changes = []

    def on_state_changed(self, change: StateChange):
        self.changes.append(change)
        print(f"State changed: {change.state_id} - {change.change_type.value}")

async def test_data_flow():
    """데이터 플로우 테스트"""
    print("=== Data Flow Test Started ===")

    # 데이터 플로우 관리자 초기화
    manager = DataFlowManager()
    config = {"cache_enabled": True}
    success = manager.initialize(config)

    if not success:
        print("Failed to initialize DataFlowManager")
        return

    # 옵저버 추가
    observer = TestObserver()
    manager.get_state_manager().add_observer(observer)

    # 데이터 라우트 설정
    manager.add_data_route("scanner", "hud_display")
    manager.add_data_route("scanner", "player_hud")

    # 테스트 데이터 처리 (동기 방식으로 직접 호출)
    print("\n--- Processing HUD Data ---")
    hud_data = {"position": "UTG", "stack": 1000, "action": "fold"}
    # 데이터 버스에 직접 전송
    success = manager.get_data_bus().send_data("table_scanner", "hud_display", hud_data)
    print(f"HUD data processing success: {success}")

    print("\n--- Processing Player Data ---")
    player_data = {"name": "Player1", "chips": 1500, "cards": ["Ah", "Ks"]}
    success = manager.get_data_bus().send_data("scanner", "player_hud", {"id": "player_1", **player_data})
    print(f"Player data processing success: {success}")

    # 상태 조회
    print("\n--- Retrieving States ---")
    hud_state = manager.get_hud_state("table_scanner")
    player_state = manager.get_player_state("player_1")

    print(f"HUD State: {hud_state}")
    print(f"Player State: {player_state}")

    # 모든 상태 조회
    all_states = manager.get_all_states()
    print(f"All States: {all_states}")

    # 통계 출력
    stats = manager.get_stats()
    print(f"\nStats: {stats}")

    # 이벤트 발행 테스트
    print("\n--- Publishing Custom Event ---")
    event_bus = manager.get_event_bus()
    custom_event = Event(EventType.CONFIG_CHANGED, {"setting": "theme", "value": "dark"})
    event_bus.publish(custom_event)

    # 정리
    manager.shutdown()

    print("\n=== Data Flow Test Completed ===")

if __name__ == "__main__":
    asyncio.run(test_data_flow())
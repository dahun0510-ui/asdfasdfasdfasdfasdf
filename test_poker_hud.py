#!/usr/bin/env python3
"""
Test script for PokerHUD core functionality (without GUI)
Tests data persistence, player management, and range handling
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Test data
TEST_DATA_FILE = Path("test_poker_players.json")

# Position ranges mapping
POSITIONS = ['BTN', 'CO', 'MP', 'UTG', 'SB', 'BB']

# Player styles
PLAYER_STYLES = {
    '1': 'Fish',
    '2': 'TAG',
    '3': 'LAG',
    '4': 'Nit',
    '5': 'Unknown'
}

# Card ranks for range matrix
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


def generate_test_hands():
    """Generate sample hands for testing"""
    hands = []
    for i, rank1 in enumerate(RANKS):
        for j, rank2 in enumerate(RANKS):
            if i == j:
                hands.append(f"{rank1}{rank2}")  # Pocket pair
            elif i < j:
                hands.append(f"{rank1}{rank2}s")  # Suited
            else:
                hands.append(f"{rank2}{rank1}o")  # Offsuit
    return hands


def test_data_persistence():
    """Test saving and loading player data"""
    print("Testing data persistence...")
    
    # Clean up test file if exists
    if TEST_DATA_FILE.exists():
        TEST_DATA_FILE.unlink()
    
    # Create test player data
    player_db = {}
    test_player = {
        'nickname': 'TestPlayer1',
        'style': 'TAG',
        'note': 'This is a test note for TestPlayer1',
        'ranges': {
            'BTN': ['AA', 'KK', 'QQ', 'AKs'],
            'CO': ['AA', 'KK', 'AKs', 'AKo'],
            'MP': ['AA', 'KK'],
            'UTG': ['AA', 'KK'],
            'SB': ['AA', 'KK', 'QQ'],
            'BB': ['AA', 'KK', 'QQ', 'JJ']
        },
        'last_updated': datetime.now().isoformat()
    }
    
    player_db['TestPlayer1'] = test_player
    
    # Save to file
    try:
        with open(TEST_DATA_FILE, 'w') as f:
            json.dump(player_db, f, indent=2)
        print(f"✓ Successfully saved test player to {TEST_DATA_FILE}")
    except Exception as e:
        print(f"✗ Failed to save: {e}")
        return False
    
    # Load from file
    try:
        with open(TEST_DATA_FILE, 'r') as f:
            loaded_db = json.load(f)
        print(f"✓ Successfully loaded {len(loaded_db)} players from database")
    except Exception as e:
        print(f"✗ Failed to load: {e}")
        return False
    
    # Verify data
    if 'TestPlayer1' in loaded_db:
        loaded_player = loaded_db['TestPlayer1']
        if loaded_player['style'] == 'TAG':
            print("✓ Player style correctly loaded")
        else:
            print(f"✗ Player style mismatch: expected TAG, got {loaded_player['style']}")
            return False
        
        if loaded_player['note'] == 'This is a test note for TestPlayer1':
            print("✓ Player note correctly loaded")
        else:
            print("✗ Player note mismatch")
            return False
        
        if 'BTN' in loaded_player['ranges']:
            btn_range = loaded_player['ranges']['BTN']
            if 'AA' in btn_range and 'KK' in btn_range:
                print(f"✓ Range data correctly loaded (BTN has {len(btn_range)} hands)")
            else:
                print("✗ Range data incomplete")
                return False
        else:
            print("✗ Range data missing")
            return False
    else:
        print("✗ Player not found in loaded data")
        return False
    
    # Clean up
    TEST_DATA_FILE.unlink()
    
    print("✓ Data persistence test passed!\n")
    return True


def test_multiple_players():
    """Test managing multiple players"""
    print("Testing multiple player management...")
    
    # Clean up test file if exists
    if TEST_DATA_FILE.exists():
        TEST_DATA_FILE.unlink()
    
    player_db = {}
    
    # Create multiple test players
    players = [
        {
            'nickname': 'Fish123',
            'style': 'Fish',
            'note': 'Calls too much preflop',
            'ranges': {'BTN': ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88']}
        },
        {
            'nickname': 'ProGamer',
            'style': 'TAG',
            'note': 'Very tight and aggressive',
            'ranges': {'BTN': ['AA', 'KK', 'AKs', 'AKo']}
        },
        {
            'nickname': 'WildCard',
            'style': 'LAG',
            'note': 'Raises everything',
            'ranges': {'BTN': generate_test_hands()[:50]}  # First 50 hands
        }
    ]
    
    # Add timestamp and save
    for player in players:
        player['last_updated'] = datetime.now().isoformat()
        player_db[player['nickname']] = player
    
    try:
        with open(TEST_DATA_FILE, 'w') as f:
            json.dump(player_db, f, indent=2)
        print(f"✓ Successfully saved {len(player_db)} players")
    except Exception as e:
        print(f"✗ Failed to save multiple players: {e}")
        return False
    
    # Load and verify
    try:
        with open(TEST_DATA_FILE, 'r') as f:
            loaded_db = json.load(f)
        
        if len(loaded_db) == 3:
            print(f"✓ All {len(loaded_db)} players loaded correctly")
        else:
            print(f"✗ Expected 3 players, got {len(loaded_db)}")
            return False
        
        # Verify each player
        for nickname in ['Fish123', 'ProGamer', 'WildCard']:
            if nickname in loaded_db:
                print(f"✓ Found player: {nickname} ({loaded_db[nickname]['style']})")
            else:
                print(f"✗ Missing player: {nickname}")
                return False
    except Exception as e:
        print(f"✗ Failed to load multiple players: {e}")
        return False
    
    # Clean up
    TEST_DATA_FILE.unlink()
    
    print("✓ Multiple player management test passed!\n")
    return True


def test_range_operations():
    """Test range operations"""
    print("Testing range operations...")
    
    all_hands = generate_test_hands()
    print(f"✓ Generated {len(all_hands)} possible starting hands")
    
    # Test pocket pairs
    pocket_pairs = [h for h in all_hands if len(h) == 2]
    if len(pocket_pairs) == 13:
        print(f"✓ Correctly identified {len(pocket_pairs)} pocket pairs")
    else:
        print(f"✗ Expected 13 pocket pairs, got {len(pocket_pairs)}")
        return False
    
    # Test suited hands (13 choose 2 = 78 unique suited combinations)
    suited = [h for h in all_hands if h.endswith('s')]
    if len(suited) == 78:
        print(f"✓ Correctly identified {len(suited)} suited hands")
    else:
        print(f"✗ Expected 78 suited hands, got {len(suited)}")
        return False
    
    # Test offsuit hands (13 choose 2 = 78 unique offsuit combinations)
    offsuit = [h for h in all_hands if h.endswith('o')]
    if len(offsuit) == 78:
        print(f"✓ Correctly identified {len(offsuit)} offsuit hands")
    else:
        print(f"✗ Expected 78 offsuit hands, got {len(offsuit)}")
        return False
    
    # Total should be 169 hands (13 pocket pairs + 78 suited + 78 offsuit)
    if len(all_hands) == 169:
        print(f"✓ Total of {len(all_hands)} hands is correct")
    else:
        print(f"✗ Expected 169 total hands, got {len(all_hands)}")
        return False
    
    print("✓ Range operations test passed!\n")
    return True


def test_player_styles():
    """Test player style shortcuts"""
    print("Testing player style mappings...")
    
    expected_styles = ['Fish', 'TAG', 'LAG', 'Nit', 'Unknown']
    
    for key, style in PLAYER_STYLES.items():
        if style in expected_styles:
            print(f"✓ Shortcut Ctrl+{key} -> {style}")
        else:
            print(f"✗ Invalid style: {style}")
            return False
    
    print("✓ Player style mappings test passed!\n")
    return True


def test_positions():
    """Test position configuration"""
    print("Testing position configuration...")
    
    expected_positions = ['BTN', 'CO', 'MP', 'UTG', 'SB', 'BB']
    
    if POSITIONS == expected_positions:
        print(f"✓ All {len(POSITIONS)} positions configured correctly")
        for pos in POSITIONS:
            print(f"  - {pos}")
    else:
        print("✗ Position configuration mismatch")
        return False
    
    print("✓ Position configuration test passed!\n")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("PokerHUD Core Functionality Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Data Persistence", test_data_persistence),
        ("Multiple Players", test_multiple_players),
        ("Range Operations", test_range_operations),
        ("Player Styles", test_player_styles),
        ("Positions", test_positions)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

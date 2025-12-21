#!/usr/bin/env python3
"""
Example usage of PokerHUD without GUI
Demonstrates data structures and operations programmatically
"""

import json
from pathlib import Path
from datetime import datetime

def create_sample_player_database():
    """Create a sample player database to demonstrate data structure"""
    
    # Sample player database
    players = {
        "Fish123": {
            "nickname": "Fish123",
            "style": "Fish",
            "note": "Very loose preflop, calls with weak hands. Overpays draws. Easy target.",
            "ranges": {
                "BTN": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "AKs", "AKo", "AQs", "AQo"],
                "CO": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs"],
                "MP": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"],
                "UTG": ["AA", "KK", "QQ", "AKs", "AKo"],
                "SB": ["AA", "KK", "QQ", "JJ", "TT", "99", "AKs", "AKo", "AQs"],
                "BB": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo"]
            },
            "last_updated": datetime.now().isoformat()
        },
        "ProGamer": {
            "nickname": "ProGamer",
            "style": "TAG",
            "note": "Tight aggressive player. 3-bets light from button. Watch for value bets on river.",
            "ranges": {
                "BTN": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs"],
                "CO": ["AA", "KK", "QQ", "JJ", "AKs", "AKo"],
                "MP": ["AA", "KK", "QQ", "AKs", "AKo"],
                "UTG": ["AA", "KK", "AKs"],
                "SB": ["AA", "KK", "QQ", "JJ", "AKs", "AKo"],
                "BB": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo"]
            },
            "last_updated": datetime.now().isoformat()
        },
        "WildCard": {
            "nickname": "WildCard",
            "style": "LAG",
            "note": "Plays almost any two cards. 4-bets bluff frequently. Hard to read but makes mistakes.",
            "ranges": {
                "BTN": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
                       "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s",
                       "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs", "T9s"],
                "CO": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
                       "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo", "KJs"],
                "MP": ["AA", "KK", "QQ", "JJ", "TT", "99", "88",
                       "AKs", "AKo", "AQs", "AQo", "AJs", "KQs"],
                "UTG": ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs"],
                "SB": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77",
                       "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "KQs", "KJs"],
                "BB": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66",
                       "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo"]
            },
            "last_updated": datetime.now().isoformat()
        },
        "NittyGritty": {
            "nickname": "NittyGritty",
            "style": "Nit",
            "note": "Only plays premium hands. Folds to any aggression. Easy to bluff postflop.",
            "ranges": {
                "BTN": ["AA", "KK", "QQ", "JJ", "AKs", "AKo"],
                "CO": ["AA", "KK", "QQ", "AKs", "AKo"],
                "MP": ["AA", "KK", "AKs"],
                "UTG": ["AA", "KK"],
                "SB": ["AA", "KK", "QQ", "AKs"],
                "BB": ["AA", "KK", "QQ", "JJ", "AKs", "AKo"]
            },
            "last_updated": datetime.now().isoformat()
        },
        "NewPlayer": {
            "nickname": "NewPlayer",
            "style": "Unknown",
            "note": "Just joined table. No reads yet. Playing standard until more information.",
            "ranges": {
                "BTN": [],
                "CO": [],
                "MP": [],
                "UTG": [],
                "SB": [],
                "BB": []
            },
            "last_updated": datetime.now().isoformat()
        }
    }
    
    return players


def save_example_database(filename="example_poker_players.json"):
    """Save example database to file"""
    players = create_sample_player_database()
    
    with open(filename, 'w') as f:
        json.dump(players, f, indent=2)
    
    print(f"✓ Created example database: {filename}")
    print(f"✓ Contains {len(players)} sample players")
    return players


def print_player_summary(player_data):
    """Print a summary of a player's data"""
    print(f"\n{'='*60}")
    print(f"Player: {player_data['nickname']}")
    print(f"{'='*60}")
    print(f"Style: {player_data['style']}")
    print(f"Note: {player_data['note']}")
    print(f"\nPosition Ranges:")
    
    for position, hands in player_data['ranges'].items():
        hand_count = len(hands)
        if hand_count > 0:
            hands_preview = ', '.join(hands[:5])
            if hand_count > 5:
                hands_preview += f"... (+{hand_count - 5} more)"
            print(f"  {position:4s}: {hand_count:3d} hands - {hands_preview}")
        else:
            print(f"  {position:4s}: No range defined")
    
    print(f"\nLast Updated: {player_data['last_updated']}")


def demonstrate_data_structure():
    """Demonstrate the PokerHUD data structure"""
    print("PokerHUD Example Usage - Data Structure Demo")
    print("=" * 60)
    
    # Create and save example database
    players = save_example_database()
    
    # Show summaries of each player type
    for nickname in ['ProGamer', 'Fish123', 'WildCard', 'NittyGritty', 'NewPlayer']:
        if nickname in players:
            print_player_summary(players[nickname])
    
    print(f"\n{'='*60}")
    print("Example database created successfully!")
    print("You can load this in the PokerHUD application or use it as a template.")
    print(f"{'='*60}\n")


def demonstrate_keyboard_shortcuts():
    """Demonstrate keyboard shortcuts"""
    print("\nKeyboard Shortcuts Reference:")
    print("=" * 60)
    print("\nPlayer Style Shortcuts:")
    print("  Ctrl+1 → Set player style to 'Fish'")
    print("  Ctrl+2 → Set player style to 'TAG'")
    print("  Ctrl+3 → Set player style to 'LAG'")
    print("  Ctrl+4 → Set player style to 'Nit'")
    print("  Ctrl+5 → Set player style to 'Unknown'")
    print("\nPlayer Management Shortcuts:")
    print("  Ctrl+S → Save current player")
    print("  Ctrl+N → Create new player")
    print("  Ctrl+L → Load player by nickname")
    print("\nOther Features:")
    print("  Click nickname field → Open note editor")
    print("  Press Enter in nickname field → Load player")
    print("  Click hand in range matrix → Toggle selection")
    print("=" * 60)


if __name__ == '__main__':
    print("\n" + "="*60)
    print(" PokerHUD - Example Usage and Data Structure")
    print("="*60 + "\n")
    
    # Demonstrate data structure
    demonstrate_data_structure()
    
    # Show keyboard shortcuts
    demonstrate_keyboard_shortcuts()
    
    print("\nTo use the actual PokerHUD application:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Run application: python poker_hud.py")
    print("\nNote: The GUI requires tkinter, which is included with most Python installations.")
    print()

# PokerHUD Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python poker_hud.py
```

## Basic Usage

### 1. Add a New Player
1. Type player nickname in the nickname field
2. Press Enter or click "Load Player" (will create new if not found)
3. Set player style: Use dropdown or press `Ctrl+1` through `Ctrl+5`
4. Click nickname field or "Edit Note" to add notes
5. Switch to range tabs and click hands to select them
6. Press `Ctrl+S` or click "Save Player"

### 2. Load Existing Player
1. Type player nickname
2. Press Enter or click "Load Player"
3. All data (style, note, ranges) loads automatically

### 3. Use OCR Scanning
1. Click "Scan OCR" button
2. Wait for scanning to complete
3. Select a player from the results dialog
4. Player data loads automatically if exists

## Keyboard Shortcuts

### Player Styles (Quick Annotation)
| Shortcut | Style | Description |
|----------|-------|-------------|
| `Ctrl+1` | Fish | Loose passive player |
| `Ctrl+2` | TAG | Tight aggressive player |
| `Ctrl+3` | LAG | Loose aggressive player |
| `Ctrl+4` | Nit | Very tight player |
| `Ctrl+5` | Unknown | No read yet |

### Player Management
| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save current player |
| `Ctrl+N` | Create new player (clears form) |
| `Ctrl+L` | Load player |

### Other Actions
| Action | Method |
|--------|--------|
| Open note editor | Click nickname field |
| Load player | Press Enter in nickname field |
| Toggle hand in range | Click hand button |
| Clear current range | Click "Clear Range" |

## Range Matrix Guide

### Position Tabs
- **BTN** (Button): Best position
- **CO** (Cutoff): One before button
- **MP** (Middle Position): Middle seats
- **UTG** (Under the Gun): First to act
- **SB** (Small Blind): Forced small bet
- **BB** (Big Blind): Forced big bet

### Hand Notation
- **AA, KK, QQ...** = Pocket pairs
- **AKs, AQs...** = Suited hands (same suit)
- **AKo, AQo...** = Offsuit hands (different suits)

### Using the Grid
- **White button** = Hand not in range
- **Green button** = Hand in range
- Click any button to toggle

## Data Storage

### Files Created
- `poker_players.json` - Player database
- `poker_hud.log` - Application log file

### Data Format (JSON)
```json
{
  "PlayerName": {
    "nickname": "PlayerName",
    "style": "TAG",
    "note": "3-bets light from button",
    "ranges": {
      "BTN": ["AA", "KK", "AKs"],
      "CO": ["AA", "KK"]
    },
    "last_updated": "2025-12-18T12:00:00"
  }
}
```

## Common Workflows

### Workflow 1: First Time Setup
```
1. Run: python poker_hud.py
2. Enter opponent nickname
3. Set style with Ctrl+1-5
4. Add notes about playing style
5. Select their range by position
6. Save with Ctrl+S
```

### Workflow 2: Quick Update During Game
```
1. Run application
2. Type nickname (or OCR scan)
3. Update note with new observation
4. Adjust ranges if needed
5. Ctrl+S to save
```

### Workflow 3: Review Multiple Players
```
1. Type first player nickname → Enter
2. Review their data
3. Ctrl+N for new player
4. Type next player nickname → Enter
5. Repeat as needed
```

## Tips & Tricks

### Efficient Range Selection
- Start with tight ranges and expand
- BTN should have widest range
- UTG should have tightest range
- Use consistent range building (AA, KK, QQ, etc.)

### Effective Note-Taking
- Note specific hands they showed down
- Track betting patterns
- Record position-specific tendencies
- Update after each session

### Using OCR Effectively
- Position poker table consistently
- Ensure good lighting on screen
- Click "Scan OCR" when new player joins
- Verify detected names before loading

## Troubleshooting

### OCR Not Working
```bash
# Install EasyOCR if missing
pip install easyocr

# Check logs
cat poker_hud.log | grep OCR
```

### Can't Save Data
```bash
# Check file permissions
ls -l poker_players.json

# View logs for errors
tail -20 poker_hud.log
```

### Application Won't Start
```bash
# Check Python version (need 3.7+)
python3 --version

# Verify tkinter installed
python3 -c "import tkinter"

# Check dependencies
pip list | grep easyocr
```

## Example Data

Run the example script to see sample player profiles:
```bash
python example_usage.py
```

This creates `example_poker_players.json` with 5 sample players:
- **Fish123** - Loose passive (Fish)
- **ProGamer** - Tight aggressive (TAG)
- **WildCard** - Loose aggressive (LAG)
- **NittyGritty** - Very tight (Nit)
- **NewPlayer** - Unknown style

You can rename this file to `poker_players.json` to use as starting data.

## Resources

- **Full Documentation**: See `README.md`
- **Feature List**: See `FEATURES.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Test Suite**: Run `python test_poker_hud.py`

## Support

Check the log file for debugging:
```bash
tail -f poker_hud.log
```

All major actions are logged with timestamps for troubleshooting.

---

**Happy tracking! 🎰♠️♥️♦️♣️**

# PokerHUD - Player Tracker Application

A comprehensive poker player tracking application with OCR scanning, range analysis, and player note management.

## Features

### 1. **OCR Scanning**
- Automatically scans for player nicknames using OCR (EasyOCR)
- Click "Scan OCR" button to detect players on screen
- Select detected players to load their profiles

### 2. **Player Information Management**
- **Reduced Height Nickname Field**: Compact design for better visibility
- **Clickable Nickname Field**: Click the nickname field to directly open the note editor
- **Player Styles**: Quick classification (Fish, TAG, LAG, Nit, Unknown)
- **Notes**: Detailed text notes for each player

### 3. **Range Matrix**
- Position-specific hand ranges (BTN, CO, MP, UTG, SB, BB)
- **Adjusted Tab Size**: Improved visibility for position tabs
- 13x13 grid for all possible starting hands
- Click to toggle hand selection
- Visual indication with color coding

### 4. **Keyboard Shortcuts**
Quick style annotation shortcuts:
- `Ctrl+1`: Set style to "Fish"
- `Ctrl+2`: Set style to "TAG"
- `Ctrl+3`: Set style to "LAG"
- `Ctrl+4`: Set style to "Nit"
- `Ctrl+5`: Set style to "Unknown"

Other shortcuts:
- `Ctrl+S`: Save player
- `Ctrl+N`: New player
- `Ctrl+L`: Load player

### 5. **Data Persistence**
- All player data saved to `poker_players.json`
- Includes nickname, style, notes, and position-specific ranges
- Automatic timestamp tracking

### 6. **Logging**
- Comprehensive logging to `poker_hud.log`
- Tracks all major actions (OCR results, data saves, loads)
- Helpful for debugging

## Installation

### Requirements
- Python 3.7+
- tkinter (usually included with Python)

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: EasyOCR installation may take some time as it downloads language models.

## Usage

### Starting the Application
```bash
python poker_hud.py
```

### Basic Workflow

1. **Enter Player Nickname**: Type or click to open note editor
2. **Set Player Style**: Use dropdown or keyboard shortcuts (Ctrl+1-5)
3. **Add Notes**: Click "Edit Note" or click the nickname field
4. **Define Ranges**: 
   - Switch between position tabs
   - Click hands to add/remove from range
   - Green = selected, White = not selected
5. **Save Player**: Click "Save Player" or press Ctrl+S
6. **Load Player**: Enter nickname and click "Load Player" or press Enter

### OCR Scanning
1. Click "Scan OCR" button
2. Application will detect player names (simulated in current version)
3. Select a player from the results dialog to load their profile

### Managing Multiple Players
- Use "New Player" to clear the form
- Save each player before switching
- Player data persists across sessions

## File Structure

```
.
├── poker_hud.py          # Main application
├── requirements.txt      # Python dependencies
├── poker_players.json    # Player database (created on first save)
├── poker_hud.log        # Application log file (created on first run)
└── README.md            # This file
```

## Troubleshooting

### OCR Not Working
- Ensure EasyOCR is installed: `pip install easyocr`
- Check `poker_hud.log` for error messages
- First run may be slow as language models download

### Data Not Saving
- Check file permissions in the application directory
- Verify `poker_players.json` can be created/modified
- Check logs for error messages

## Development

### Adding New Features
The application is structured with clear separation:
- UI setup in dedicated methods
- Data persistence through JSON
- Thread-safe OCR operations
- Comprehensive logging

### Customization
- Modify `POSITIONS` to add/remove positions
- Update `PLAYER_STYLES` for different classifications
- Extend `RANKS` for different card notations

## License

This project is provided as-is for poker player tracking purposes.
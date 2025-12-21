#!/usr/bin/env python3
"""
PokerHUD Application - Complete Rewrite
Features:
- OCR scanning for player nicknames
- Range matrix with position-specific ranges
- Shortcut keys for quick player style annotation
- Data persistence to JSON database
- Logging for debugging
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import logging
from pathlib import Path
from datetime import datetime
import threading
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('poker_hud.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

# Card ranks and suits for range matrix
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


class PokerHUD:
    """Main PokerHUD Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PokerHUD - Player Tracker")
        self.root.geometry("900x700")
        
        # Data file path
        self.data_file = Path("poker_players.json")
        
        # Load player database
        self.player_db = self.load_database()
        
        # Current player data
        self.current_player = None
        
        # OCR queue for thread-safe operations
        self.ocr_queue = queue.Queue()
        self.ocr_running = False
        
        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        
        # Start OCR check timer
        self.root.after(100, self.check_ocr_queue)
        
        logger.info("PokerHUD application started")
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Player info section
        self.setup_player_info_section(main_frame)
        
        # Range matrix section
        self.setup_range_matrix_section(main_frame)
        
        # Control buttons
        self.setup_control_buttons(main_frame)
        
        # Status bar
        self.setup_status_bar(main_frame)
    
    def setup_player_info_section(self, parent):
        """Setup player information section"""
        info_frame = ttk.LabelFrame(parent, text="Player Information", padding="10")
        info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Nickname field (reduced height, clickable)
        ttk.Label(info_frame, text="Nickname:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.nickname_var = tk.StringVar()
        self.nickname_entry = ttk.Entry(info_frame, textvariable=self.nickname_var, width=30)
        self.nickname_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        self.nickname_entry.bind('<Return>', lambda e: self.load_player())
        self.nickname_entry.bind('<Button-1>', lambda e: self.open_note_editor())
        
        # Style selector
        ttk.Label(info_frame, text="Style:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=2)
        self.style_var = tk.StringVar(value='Unknown')
        style_combo = ttk.Combobox(info_frame, textvariable=self.style_var, 
                                   values=list(PLAYER_STYLES.values()), 
                                   width=15, state='readonly')
        style_combo.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # OCR button
        self.ocr_button = ttk.Button(info_frame, text="Scan OCR", command=self.start_ocr_scan)
        self.ocr_button.grid(row=0, column=4, padx=(10, 0), pady=2)
        
        # Note display (compact)
        ttk.Label(info_frame, text="Note:").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=2)
        self.note_display = tk.Text(info_frame, height=2, width=40, wrap=tk.WORD)
        self.note_display.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        self.note_display.config(state=tk.DISABLED)
        
        # Edit note button
        ttk.Button(info_frame, text="Edit Note", command=self.open_note_editor).grid(
            row=1, column=4, padx=(10, 0), pady=2
        )
        
        info_frame.columnconfigure(1, weight=1)
    
    def setup_range_matrix_section(self, parent):
        """Setup range matrix section with position tabs"""
        range_frame = ttk.LabelFrame(parent, text="Range Matrix", padding="10")
        range_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(1, weight=1)
        
        # Create notebook for position tabs (adjusted tab size)
        self.range_notebook = ttk.Notebook(range_frame)
        self.range_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        range_frame.rowconfigure(0, weight=1)
        range_frame.columnconfigure(0, weight=1)
        
        # Create range grids for each position
        self.range_grids = {}
        for position in POSITIONS:
            tab_frame = ttk.Frame(self.range_notebook, padding="5")
            self.range_notebook.add(tab_frame, text=f"  {position}  ")
            
            # Create 13x13 grid for hand ranges
            grid_frame = ttk.Frame(tab_frame)
            grid_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            self.range_grids[position] = {}
            for i, rank1 in enumerate(RANKS):
                for j, rank2 in enumerate(RANKS):
                    # Determine hand type
                    if i == j:
                        hand = f"{rank1}{rank2}"  # Pocket pair
                    elif i < j:
                        hand = f"{rank1}{rank2}s"  # Suited
                    else:
                        hand = f"{rank2}{rank1}o"  # Offsuit
                    
                    # Create button for hand
                    btn = tk.Button(grid_frame, text=hand, width=5, height=2,
                                   relief=tk.RAISED, bg='white',
                                   command=lambda h=hand, p=position: self.toggle_hand(p, h))
                    btn.grid(row=i, column=j, padx=1, pady=1)
                    self.range_grids[position][hand] = btn
            
            tab_frame.rowconfigure(0, weight=1)
            tab_frame.columnconfigure(0, weight=1)
    
    def setup_control_buttons(self, parent):
        """Setup control buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        ttk.Button(button_frame, text="Load Player", command=self.load_player).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save Player", command=self.save_player).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="New Player", command=self.new_player).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Clear Range", command=self.clear_range).grid(row=0, column=3, padx=5)
    
    def setup_status_bar(self, parent):
        """Setup status bar"""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Style shortcuts
        for key, style in PLAYER_STYLES.items():
            self.root.bind(f'<Control-Key-{key}>', lambda e, s=style: self.set_style(s))
        
        # Other shortcuts
        self.root.bind('<Control-s>', lambda e: self.save_player())
        self.root.bind('<Control-n>', lambda e: self.new_player())
        self.root.bind('<Control-l>', lambda e: self.load_player())
        
        logger.info("Keyboard shortcuts configured")
    
    def toggle_hand(self, position, hand):
        """Toggle hand selection in range matrix"""
        btn = self.range_grids[position][hand]
        if btn['bg'] == 'white':
            btn.config(bg='lightgreen', relief=tk.SUNKEN)
        else:
            btn.config(bg='white', relief=tk.RAISED)
    
    def get_selected_range(self, position):
        """Get list of selected hands for a position"""
        selected = []
        for hand, btn in self.range_grids[position].items():
            if btn['bg'] == 'lightgreen':
                selected.append(hand)
        return selected
    
    def set_range(self, position, hands):
        """Set the selected hands for a position"""
        # Clear all first
        for hand, btn in self.range_grids[position].items():
            btn.config(bg='white', relief=tk.RAISED)
        
        # Set selected hands
        for hand in hands:
            if hand in self.range_grids[position]:
                self.range_grids[position][hand].config(bg='lightgreen', relief=tk.SUNKEN)
    
    def clear_range(self):
        """Clear current position's range"""
        current_tab = self.range_notebook.index(self.range_notebook.select())
        position = POSITIONS[current_tab]
        self.set_range(position, [])
        self.update_status(f"Cleared range for {position}")
        logger.info(f"Cleared range for {position}")
    
    def set_style(self, style):
        """Set player style"""
        self.style_var.set(style)
        self.update_status(f"Set style to: {style}")
        logger.info(f"Style set to: {style}")
    
    def open_note_editor(self):
        """Open note editor window"""
        if not self.nickname_var.get():
            messagebox.showwarning("No Player", "Please enter a player nickname first.")
            return
        
        editor = tk.Toplevel(self.root)
        editor.title(f"Edit Note - {self.nickname_var.get()}")
        editor.geometry("500x300")
        
        # Note text area
        note_text = scrolledtext.ScrolledText(editor, wrap=tk.WORD, width=60, height=15)
        note_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Load current note
        if self.current_player and 'note' in self.current_player:
            note_text.insert('1.0', self.current_player['note'])
        
        # Save button
        def save_note():
            note_content = note_text.get('1.0', tk.END).strip()
            if self.current_player is None:
                self.current_player = {
                    'nickname': self.nickname_var.get(),
                    'style': self.style_var.get(),
                    'note': note_content,
                    'ranges': {}
                }
            else:
                self.current_player['note'] = note_content
            
            # Update display
            self.note_display.config(state=tk.NORMAL)
            self.note_display.delete('1.0', tk.END)
            self.note_display.insert('1.0', note_content)
            self.note_display.config(state=tk.DISABLED)
            
            editor.destroy()
            self.update_status("Note saved")
            logger.info(f"Note saved for player: {self.nickname_var.get()}")
        
        ttk.Button(editor, text="Save Note", command=save_note).pack(pady=5)
    
    def load_player(self):
        """Load player data"""
        nickname = self.nickname_var.get().strip()
        if not nickname:
            messagebox.showwarning("No Nickname", "Please enter a player nickname.")
            return
        
        if nickname in self.player_db:
            self.current_player = self.player_db[nickname]
            
            # Load style
            self.style_var.set(self.current_player.get('style', 'Unknown'))
            
            # Load note
            note = self.current_player.get('note', '')
            self.note_display.config(state=tk.NORMAL)
            self.note_display.delete('1.0', tk.END)
            self.note_display.insert('1.0', note)
            self.note_display.config(state=tk.DISABLED)
            
            # Load ranges
            ranges = self.current_player.get('ranges', {})
            for position in POSITIONS:
                hands = ranges.get(position, [])
                self.set_range(position, hands)
            
            self.update_status(f"Loaded player: {nickname}")
            logger.info(f"Loaded player: {nickname}")
        else:
            self.new_player()
            self.update_status(f"Player not found: {nickname}. Created new player.")
            logger.info(f"New player created: {nickname}")
    
    def save_player(self):
        """Save current player data"""
        nickname = self.nickname_var.get().strip()
        if not nickname:
            messagebox.showwarning("No Nickname", "Please enter a player nickname.")
            return
        
        # Collect range data
        ranges = {}
        for position in POSITIONS:
            ranges[position] = self.get_selected_range(position)
        
        # Create/update player data
        player_data = {
            'nickname': nickname,
            'style': self.style_var.get(),
            'note': self.note_display.get('1.0', tk.END).strip(),
            'ranges': ranges,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save to database
        self.player_db[nickname] = player_data
        self.current_player = player_data
        self.save_database()
        
        self.update_status(f"Saved player: {nickname}")
        logger.info(f"Saved player: {nickname}")
    
    def new_player(self):
        """Create new player"""
        nickname = self.nickname_var.get().strip()
        
        # Clear form
        self.style_var.set('Unknown')
        self.note_display.config(state=tk.NORMAL)
        self.note_display.delete('1.0', tk.END)
        self.note_display.config(state=tk.DISABLED)
        
        # Clear all ranges
        for position in POSITIONS:
            self.set_range(position, [])
        
        self.current_player = None
        
        if nickname:
            self.update_status(f"New player form ready: {nickname}")
        else:
            self.update_status("New player form ready")
        logger.info("New player form initialized")
    
    def start_ocr_scan(self):
        """Start OCR scan in background thread"""
        if self.ocr_running:
            self.update_status("OCR scan already running...")
            return
        
        self.ocr_running = True
        self.ocr_button.config(state=tk.DISABLED)
        self.update_status("Starting OCR scan...")
        logger.info("OCR scan initiated")
        
        # Run OCR in background thread
        thread = threading.Thread(target=self.perform_ocr_scan, daemon=True)
        thread.start()
    
    def perform_ocr_scan(self):
        """Perform OCR scan (runs in background thread)"""
        try:
            # Import easyocr (lazy import to avoid startup delay)
            import easyocr
            
            logger.info("Initializing EasyOCR reader...")
            reader = easyocr.Reader(['en'], gpu=False)
            
            # For demonstration, we'll simulate OCR scanning
            # TODO: In production, capture screen region and process it with reader.readtext()
            # Example: result = reader.readtext(screen_image)
            # Then extract text: result = [text for (bbox, text, prob) in result if prob > 0.5]
            logger.info("OCR scanning (simulated - replace with actual screen capture in production)...")
            
            # Simulated result for demonstration purposes
            # In production, replace this with actual OCR results from screen capture
            result = ['Player1', 'Player2', 'Fish123', 'ProGamer']
            
            logger.info(f"OCR detected players: {result}")
            
            # Put result in queue
            self.ocr_queue.put(('success', result))
            
        except ImportError:
            error_msg = "EasyOCR not installed. Install with: pip install easyocr"
            logger.error(error_msg)
            self.ocr_queue.put(('error', error_msg))
        except Exception as e:
            error_msg = f"OCR error: {str(e)}"
            logger.error(error_msg)
            self.ocr_queue.put(('error', error_msg))
    
    def check_ocr_queue(self):
        """Check OCR queue for results (runs in main thread)"""
        try:
            while not self.ocr_queue.empty():
                status, data = self.ocr_queue.get_nowait()
                
                if status == 'success':
                    # Show OCR results dialog
                    self.show_ocr_results(data)
                    self.update_status(f"OCR completed: {len(data)} players detected")
                else:
                    messagebox.showerror("OCR Error", data)
                    self.update_status("OCR scan failed")
                
                self.ocr_running = False
                self.ocr_button.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_ocr_queue)
    
    def show_ocr_results(self, players):
        """Show OCR results in dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("OCR Results")
        dialog.geometry("300x400")
        
        ttk.Label(dialog, text="Detected Players:", font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(dialog, width=40, height=15)
        listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        for player in players:
            listbox.insert(tk.END, player)
        
        def select_player():
            selection = listbox.curselection()
            if selection:
                nickname = listbox.get(selection[0])
                self.nickname_var.set(nickname)
                self.load_player()
                dialog.destroy()
        
        ttk.Button(dialog, text="Load Selected", command=select_player).pack(pady=5)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=5)
    
    def load_database(self):
        """Load player database from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"Loaded database with {len(data)} players")
                return data
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                return {}
        return {}
    
    def save_database(self):
        """Save player database to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.player_db, f, indent=2)
            logger.info(f"Saved database with {len(self.player_db)} players")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
            messagebox.showerror("Save Error", f"Failed to save database: {e}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = PokerHUD(root)
    root.mainloop()


if __name__ == '__main__':
    main()

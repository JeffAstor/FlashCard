"""
View Mode Interface - Study interface for flash card learning
"""

import random
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QFrame, QLabel, QComboBox, QScrollArea, QMessageBox,
                            QProgressBar, QDialog, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import QShortcut


class ViewModeWidget(QWidget):
    """Study interface for flash card learning"""
    
    mode_change_requested = pyqtSignal(str, str)  # mode, data
    
    def __init__(self, app_controller, vault_manager):
        super().__init__()
        self.app_controller = app_controller
        self.vault_manager = vault_manager
        self.current_set = None
        self.current_card_index = 0
        self.current_side = "information"  # "information" or "answer"
        self.study_mode = "sequential"  # "sequential", "random", "review"
        self.card_order = []  # Order for current study mode
        self.session_manager = None
        self.setup_ui()
        self.setup_shortcuts()
        
    def setup_ui(self):
        """Create study interface layout"""
        layout = QVBoxLayout()
        
        # Menu bar
        self.setup_view_menu_bar()
        layout.addWidget(self.menu_bar)
        
        # Progress bar
        self.setup_progress_bar()
        layout.addWidget(self.progress_frame)
        
        # Card display area
        self.setup_card_display()
        layout.addWidget(self.card_display_area, 1)
        
        # Status bar with session info
        self.setup_status_bar()
        layout.addWidget(self.status_bar)
        
        self.setLayout(layout)
        
    def setup_view_menu_bar(self):
        """Create view-specific menu bar with navigation and study controls"""
        self.menu_bar = QFrame()
        self.menu_bar.setFrameStyle(QFrame.StyledPanel)
        self.menu_bar.setMaximumHeight(50)
        
        layout = QHBoxLayout()
        
        # Navigation controls
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.on_previous_clicked)
        layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.on_next_clicked)
        layout.addWidget(self.next_button)
        
        self.random_button = QPushButton("Random")
        self.random_button.clicked.connect(self.on_random_clicked)
        layout.addWidget(self.random_button)
        
        self.flip_button = QPushButton("Flip Card")
        self.flip_button.clicked.connect(self.on_flip_card_clicked)
        layout.addWidget(self.flip_button)
        
        layout.addStretch()
        
        # Study mode selector
        layout.addWidget(QLabel("Mode:"))
        self.study_mode_selector = QComboBox()
        self.study_mode_selector.addItems(["Sequential", "Random", "Review Only"])
        self.study_mode_selector.currentTextChanged.connect(self.on_study_mode_changed)
        layout.addWidget(self.study_mode_selector)
        
        layout.addStretch()
        
        # Card status buttons
        self.known_button = QPushButton("Mark Known (K)")
        self.known_button.clicked.connect(self.on_mark_known_clicked)
        self.known_button.setStyleSheet("background-color: lightgreen;")
        layout.addWidget(self.known_button)
        
        self.review_button = QPushButton("Mark Review (R)")
        self.review_button.clicked.connect(self.on_mark_review_clicked)
        self.review_button.setStyleSheet("background-color: lightyellow;")
        layout.addWidget(self.review_button)
        
        self.unknown_button = QPushButton("Mark Unknown (U)")
        self.unknown_button.clicked.connect(self.on_mark_unknown_clicked)
        self.unknown_button.setStyleSheet("background-color: lightcoral;")
        layout.addWidget(self.unknown_button)
        
        layout.addStretch()
        
        # Session controls
        self.stats_button = QPushButton("Session Stats")
        self.stats_button.clicked.connect(self.on_session_stats_clicked)
        layout.addWidget(self.stats_button)
        
        self.return_button = QPushButton("Return to Vault")
        self.return_button.clicked.connect(self.on_return_to_vault_clicked)
        layout.addWidget(self.return_button)
        
        self.menu_bar.setLayout(layout)
        
    def setup_progress_bar(self):
        """Create progress indicators"""
        self.progress_frame = QFrame()
        self.progress_frame.setFrameStyle(QFrame.StyledPanel)
        self.progress_frame.setMaximumHeight(30)

        layout = QHBoxLayout()

        self.card_position_label = QLabel("Card 1 of 1")
        layout.addWidget(self.card_position_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.side_indicator = QLabel("Information Side")
        self.side_indicator.setFont(QFont("Arial", 9, QFont.Bold))
        layout.addWidget(self.side_indicator)

        self.progress_frame.setLayout(layout)
        
    def setup_card_display(self):
        """Create card display area"""
        self.card_display_area = QScrollArea()
        self.card_display_area.setWidgetResizable(True)
        self.card_display_area.setStyleSheet("border: 2px solid gray; background-color: white;")
        
        # Card content widget
        self.card_widget = CardDisplayWidget()
        self.card_widget.card_clicked.connect(self.on_flip_card_clicked)
        self.card_display_area.setWidget(self.card_widget)
        
    def setup_status_bar(self):
        """Create status bar with session info"""
        self.status_bar = QFrame()
        self.status_bar.setFrameStyle(QFrame.StyledPanel)
        self.status_bar.setMaximumHeight(30)
        
        layout = QHBoxLayout()
        
        self.session_time_label = QLabel("Session: 00:00")
        layout.addWidget(self.session_time_label)
        
        layout.addStretch()
        
        self.cards_studied_label = QLabel("Studied: 0")
        layout.addWidget(self.cards_studied_label)
        
        self.status_bar.setLayout(layout)
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Navigation shortcuts
        QShortcut(Qt.Key_Left, self, self.on_previous_clicked)
        QShortcut(Qt.Key_Right, self, self.on_next_clicked)
        QShortcut(Qt.Key_Space, self, self.on_flip_card_clicked)
        
        # Status shortcuts
        QShortcut(Qt.Key_K, self, self.on_mark_known_clicked)
        QShortcut(Qt.Key_R, self, self.on_mark_review_clicked)
        QShortcut(Qt.Key_U, self, self.on_mark_unknown_clicked)
        
    def load_set(self, set_name):
        """Load set for studying"""
        try:
            self.current_set = self.vault_manager.load_set(set_name)
            self.current_card_index = 0
            self.current_side = "information"
            
            # Initialize session manager
            self.session_manager = StudySessionManager(self.current_set, self.study_mode)
            self.session_manager.start_session()
            
            # Setup card order based on study mode
            self.setup_card_order()
            
            # Start session timer
            self.session_timer = QTimer()
            self.session_timer.timeout.connect(self.update_session_time)
            self.session_timer.start(1000)  # Update every second
            
            # Display first card
            self.display_current_card()
            self.update_progress()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load set: {str(e)}")
            
    def setup_card_order(self):
        """Setup card order based on study mode"""
        if not self.current_set:
            return
            
        if self.study_mode == "sequential":
            self.card_order = list(range(len(self.current_set.cards)))
        elif self.study_mode == "random":
            self.card_order = list(range(len(self.current_set.cards)))
            random.shuffle(self.card_order)
        elif self.study_mode == "review":
            # Only cards marked for review
            self.card_order = []
            for i, card in enumerate(self.current_set.cards):
                if card.status == "Review":
                    self.card_order.append(i)
                    
        # Reset to first card in order
        self.current_card_index = 0
        
    def display_current_card(self):
        """Show current card content"""
        if not self.current_set or not self.card_order:
            self.card_widget.set_blocks([])
            return
            
        if 0 <= self.current_card_index < len(self.card_order):
            actual_card_index = self.card_order[self.current_card_index]
            card = self.current_set.cards[actual_card_index]
            blocks = card.get_side_blocks(self.current_side)
            
            self.card_widget.set_blocks(blocks, self.vault_manager, self.current_set)
            self.update_side_indicator()
            self.update_status_buttons(card.status)
            
    def update_side_indicator(self):
        """Update side indicator"""
        if self.current_side == "information":
            self.side_indicator.setText("Information Side")
        else:
            self.side_indicator.setText("Answer Side")
            
    def update_status_buttons(self, current_status):
        """Update status button highlighting"""
        # Reset all buttons
        self.known_button.setStyleSheet("background-color: lightgreen;")
        self.review_button.setStyleSheet("background-color: lightyellow;")
        self.unknown_button.setStyleSheet("background-color: lightcoral;")
        
        # Highlight current status
        if current_status == "Known":
            self.known_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        elif current_status == "Review":
            self.review_button.setStyleSheet("background-color: orange; color: white; font-weight: bold;")
        elif current_status == "Unknown":
            self.unknown_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
            
    def update_progress(self):
        """Update progress indicators"""
        if not self.card_order:
            self.card_position_label.setText("No cards")
            self.progress_bar.setValue(0)
            return
            
        position = self.current_card_index + 1
        total = len(self.card_order)
        
        self.card_position_label.setText(f"Card {position} of {total}")
        
        if total > 0:
            progress = (position / total) * 100
            self.progress_bar.setValue(int(progress))
        else:
            self.progress_bar.setValue(0)
            
    def update_session_time(self):
        """Update session time display"""
        if self.session_manager:
            duration = self.session_manager.get_session_duration()
            minutes = duration // 60
            seconds = duration % 60
            self.session_time_label.setText(f"Session: {minutes:02d}:{seconds:02d}")
            
            # Update cards studied
            stats = self.session_manager.get_basic_statistics()
            self.cards_studied_label.setText(f"Studied: {stats['cards_studied']}")
            
    def on_previous_clicked(self):
        """Navigate to previous card"""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.current_side = "information"  # Reset to information side
            self.display_current_card()
            self.update_progress()
            
    def on_next_clicked(self):
        """Navigate to next card"""
        if self.current_card_index < len(self.card_order) - 1:
            self.current_card_index += 1
            self.current_side = "information"  # Reset to information side
            self.display_current_card()
            self.update_progress()
        else:
            # End of study session
            self.show_session_complete()
            
    def on_random_clicked(self):
        """Jump to random card"""
        if self.card_order:
            self.current_card_index = random.randint(0, len(self.card_order) - 1)
            self.current_side = "information"
            self.display_current_card()
            self.update_progress()
            
    def on_flip_card_clicked(self):
        """Switch between card sides"""
        self.current_side = "answer" if self.current_side == "information" else "information"
        self.display_current_card()
        
    def on_mark_known_clicked(self):
        """Mark card as Known"""
        self.set_card_status("Known")
        
    def on_mark_review_clicked(self):
        """Mark card as Need Review"""
        self.set_card_status("Review")
        
    def on_mark_unknown_clicked(self):
        """Mark card as Unknown"""
        self.set_card_status("Unknown")
        
    def set_card_status(self, status):
        """Update current card status"""
        if not self.current_set or not self.card_order:
            return
            
        if 0 <= self.current_card_index < len(self.card_order):
            actual_card_index = self.card_order[self.current_card_index]
            card = self.current_set.cards[actual_card_index]
            card.set_status(status)
            
            # Update session manager
            if self.session_manager:
                self.session_manager.record_card_study(card.card_id, status)
                
            # Update display
            self.update_status_buttons(status)
            
            # Auto-save changes
            try:
                self.vault_manager.save_set(self.current_set)
            except Exception as e:
                print(f"Failed to save card status: {e}")
                
    def on_study_mode_changed(self, mode_text):
        """Switch study mode"""
        mode_map = {
            "Sequential": "sequential",
            "Random": "random", 
            "Review Only": "review"
        }
        
        new_mode = mode_map.get(mode_text, "sequential")
        if new_mode != self.study_mode:
            self.study_mode = new_mode
            self.setup_card_order()
            self.display_current_card()
            self.update_progress()
            
    def on_session_stats_clicked(self):
        """Display session statistics"""
        if self.session_manager:
            dialog = SessionStatsDialog(self.session_manager, self)
            dialog.exec_()
            
    def on_return_to_vault_clicked(self):
        """Return to vault mode"""
        if self.session_manager:
            self.session_manager.end_session()
            
        if hasattr(self, 'session_timer'):
            self.session_timer.stop()
            
        self.mode_change_requested.emit("vault", None)
        
    def show_session_complete(self):
        """Show session completion dialog"""
        if self.session_manager:
            stats = self.session_manager.get_basic_statistics()
            duration = self.session_manager.get_session_duration()
            
            minutes = duration // 60
            seconds = duration % 60
            
            message = f"""Study Session Complete!
            
Time spent: {minutes:02d}:{seconds:02d}
Cards studied: {stats['cards_studied']}
Known: {stats['cards_known']}
Review: {stats['cards_review']}
Unknown: {stats['cards_unknown']}

Would you like to continue studying or return to the vault?"""
            
            reply = QMessageBox.question(
                self, "Session Complete", message,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Reset to beginning
                self.current_card_index = 0
                self.current_side = "information"
                self.display_current_card()
                self.update_progress()
            else:
                self.on_return_to_vault_clicked()


class CardDisplayWidget(QWidget):
    """Widget for displaying card content during study"""
    
    card_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_blocks = []
        self.vault_manager = None
        self.flash_set = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize card display"""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMinimumHeight(400)
        
        # Default message
        self.no_content_label = QLabel("No content to display")
        self.no_content_label.setAlignment(Qt.AlignCenter)
        self.no_content_label.setStyleSheet("color: gray; font-size: 16px;")
        self.layout.addWidget(self.no_content_label)
        
    def set_blocks(self, blocks, vault_manager=None, flash_set=None):
        """Set blocks for display"""
        self.current_blocks = blocks
        self.vault_manager = vault_manager
        self.flash_set = flash_set
        
        # Clear existing content
        self.clear_content()
        
        if not blocks:
            self.no_content_label.show()
            return
            
        self.no_content_label.hide()
        
        # Add block display widgets
        for block in blocks:
            try:
                if vault_manager and flash_set:
                    widget = block.get_display_widget(vault_manager.vault_path, flash_set.name)
                else:
                    widget = block.get_display_widget()
                    
                if widget:
                    self.layout.addWidget(widget)
            except Exception as e:
                # Show error for problematic blocks
                error_label = QLabel(f"Error displaying block: {str(e)}")
                error_label.setStyleSheet("color: red;")
                self.layout.addWidget(error_label)
                
        # Add stretch to push content to top
        self.layout.addStretch()
        
    def clear_content(self):
        """Remove all content widgets except the no-content label"""
        while self.layout.count() > 1:
            child = self.layout.takeAt(1)  # Skip the no-content label
            if child.widget():
                child.widget().deleteLater()
                
    def mousePressEvent(self, event):
        """Handle click to flip card"""
        self.card_clicked.emit()
        super().mousePressEvent(event)


class StudySessionManager:
    """Manages study session state and basic statistics"""
    
    def __init__(self, card_set, study_mode):
        self.card_set = card_set
        self.study_mode = study_mode
        self.session_start_time = None
        self.cards_studied = 0
        self.cards_known = 0
        self.cards_review = 0
        self.cards_unknown = 0
        self.studied_cards = set()  # Track which cards have been studied
        
    def start_session(self):
        """Begin study session"""
        self.session_start_time = datetime.now()
        
    def end_session(self):
        """Complete study session"""
        # Could save session data to file here
        pass
        
    def record_card_study(self, card_id, status):
        """Record card interaction"""
        # Add to studied cards set
        self.studied_cards.add(card_id)
        self.cards_studied = len(self.studied_cards)
        
        # Update status counts (count all cards, not just studied ones)
        self.cards_known = len([c for c in self.card_set.cards if c.status == "Known"])
        self.cards_review = len([c for c in self.card_set.cards if c.status == "Review"])
        self.cards_unknown = len([c for c in self.card_set.cards if c.status == "Unknown"])
        
    def get_session_duration(self):
        """Return session time in seconds"""
        if self.session_start_time:
            return int((datetime.now() - self.session_start_time).total_seconds())
        return 0
        
    def get_progress_percentage(self):
        """Return completion percentage"""
        total_cards = len(self.card_set.cards)
        if total_cards == 0:
            return 0
        return (self.cards_studied / total_cards) * 100
        
    def get_basic_statistics(self):
        """Return simple session stats"""
        return {
            "cards_studied": self.cards_studied,
            "cards_known": self.cards_known,
            "cards_review": self.cards_review,
            "cards_unknown": self.cards_unknown,
            "total_cards": len(self.card_set.cards),
            "session_duration": self.get_session_duration(),
            "progress": self.get_progress_percentage()
        }


class SessionStatsDialog(QDialog):
    """Dialog showing session statistics"""
    
    def __init__(self, session_manager, parent=None):
        super().__init__(parent)
        self.session_manager = session_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Session Statistics")
        self.setModal(True)
        self.resize(300, 200)
        
        layout = QVBoxLayout()
        
        stats = self.session_manager.get_basic_statistics()
        duration = stats["session_duration"]
        minutes = duration // 60
        seconds = duration % 60
        
        stats_text = f"""Session Statistics

Time: {minutes:02d}:{seconds:02d}
Cards Studied: {stats['cards_studied']} / {stats['total_cards']}
Progress: {stats['progress']:.1f}%

Card Status:
  Known: {stats['cards_known']}
  Review: {stats['cards_review']}
  Unknown: {stats['cards_unknown']}
"""
        
        stats_label = QLabel(stats_text)
        stats_label.setFont(QFont("Courier", 10))
        layout.addWidget(stats_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
"""
Edit Mode Interface - Interface for editing flash card sets and individual cards
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QComboBox, QScrollArea, QFrame, QLabel, QMessageBox,
                            QSpinBox, QTabWidget, QDialog, QTextEdit, QProgressDialog,
                            QDialogButtonBox, QFormLayout, QSlider, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt5.QtGui import QFont
from models.content_blocks import create_block_from_type, TextBlock
from models.flashcard import FlashCard
import json
import requests
import random
import ssl
import urllib3
import os


class EditModeWidget(QWidget):
    """Interface for editing flash card sets and individual cards"""
    
    mode_change_requested = pyqtSignal(str, str)  # mode, data
    
    def __init__(self, app_controller, vault_manager):
        super().__init__()
        self.app_controller = app_controller
        self.vault_manager = vault_manager
        self.current_set = None
        self.current_card_index = 0
        self.current_side = "information"  # "information" or "answer"
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        self.setup_ui()
        
    def setup_ui(self):
        """Create interface layout and widgets"""
        layout = QVBoxLayout()
        
        # Menu bar
        self.setup_edit_menu_bar()
        layout.addWidget(self.menu_bar)
        
        # Side selector (tabs)
        self.setup_side_selector()
        layout.addWidget(self.side_selector)
        
        # Block editor
        self.setup_block_editor()
        layout.addWidget(self.block_editor, 1)
        
        self.setLayout(layout)
        
    def setup_edit_menu_bar(self):
        """Create edit-specific menu bar with navigation and controls"""
        self.menu_bar = QFrame()
        self.menu_bar.setFrameStyle(QFrame.StyledPanel)
        self.menu_bar.setMaximumHeight(50)
        
        layout = QHBoxLayout()
        
        # Navigation controls
        self.prev_card_button = QPushButton("Previous Card")
        self.prev_card_button.clicked.connect(self.on_previous_card_clicked)
        layout.addWidget(self.prev_card_button)
        
        self.next_card_button = QPushButton("Next Card")
        self.next_card_button.clicked.connect(self.on_next_card_clicked)
        layout.addWidget(self.next_card_button)
        
        self.new_card_button = QPushButton("New Card")
        self.new_card_button.clicked.connect(self.on_new_card_clicked)
        layout.addWidget(self.new_card_button)
        
        self.ai_new_card_button = QPushButton("AI - New Card")
        self.ai_new_card_button.clicked.connect(self.on_ai_new_card_clicked)
        layout.addWidget(self.ai_new_card_button)
        
        # Card selector dropdown
        self.card_selector = QComboBox()
        self.card_selector.currentIndexChanged.connect(self.on_card_selector_changed)
        layout.addWidget(self.card_selector)
        
        layout.addStretch()
        
        # Side indicator
        self.side_indicator = QLabel("Information Side")
        self.side_indicator.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.side_indicator)
        
        # Flip side button
        self.flip_side_button = QPushButton("Switch to Answer")
        self.flip_side_button.clicked.connect(self.on_flip_side_clicked)
        layout.addWidget(self.flip_side_button)
        
        layout.addStretch()
        
        # Save and exit controls
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.on_save_changes_clicked)
        layout.addWidget(self.save_button)
        
        self.return_button = QPushButton("Return to Vault")
        self.return_button.clicked.connect(self.on_return_to_vault_clicked)
        layout.addWidget(self.return_button)
        
        self.menu_bar.setLayout(layout)
        
    def setup_side_selector(self):
        """Create side selection tabs"""
        self.side_selector = QTabWidget()
        self.side_selector.addTab(QWidget(), "Information Side")
        self.side_selector.addTab(QWidget(), "Answer Side")
        self.side_selector.currentChanged.connect(self.on_side_tab_changed)
        self.side_selector.setMaximumHeight(35)
        
    def setup_block_editor(self):
        """Create block editing interface"""
        self.block_editor = BlockEditorWidget(self.vault_manager, self.current_set)
        self.block_editor.blocks_modified.connect(self.on_blocks_modified)
        
    def load_set(self, set_name):
        """Load set for editing"""
        ## DEBUG START
        print(f"DEBUG: EditModeWidget.load_set called with: {set_name}")
        ## DEBUG END
        try:
            self.current_set = self.vault_manager.load_set(set_name)
            self.current_card_index = 0
            self.current_side = "information"
            
            ## DEBUG START
            print(f"DEBUG: Set loaded successfully, {len(self.current_set.cards)} cards")
            if self.current_set.cards:
                card = self.current_set.cards[0]
                info_blocks = card.get_side_blocks("information")
                print(f"DEBUG: First card has {len(info_blocks)} information blocks")
                for i, block in enumerate(info_blocks):
                    print(f"  Block {i}: type={block.block_type}")
                    if hasattr(block, 'image_path'):
                        print(f"    image_path={block.image_path}")
            ## DEBUG END
            
            # Update block editor with set context FIRST
            self.block_editor.set_context(self.vault_manager, self.current_set)
            
            # Update UI
            self.update_card_selector()
            self.display_current_card()
            self.update_navigation_buttons()
            self.update_side_indicator()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load set: {str(e)}")
            
    def display_current_card(self):
        """Show current card content"""
        ## DEBUG START
        print(f"DEBUG: display_current_card called")
        print(f"  current_card_index: {self.current_card_index}")
        print(f"  current_side: {self.current_side}")
        ## DEBUG END
        
        if not self.current_set or not self.current_set.cards:
            self.block_editor.set_blocks([])
            return
            
        if 0 <= self.current_card_index < len(self.current_set.cards):
            card = self.current_set.cards[self.current_card_index]
            blocks = card.get_side_blocks(self.current_side)
            
            ## DEBUG START
            print(f"DEBUG: Displaying {len(blocks)} blocks for {self.current_side} side")
            for i, block in enumerate(blocks):
                print(f"  Block {i}: type={block.block_type}")
                if hasattr(block, 'image_path'):
                    print(f"    image_path={block.image_path}")
            ## DEBUG END
            
            self.block_editor.set_blocks(blocks, self.current_card_index, self.current_side)
            
    def update_card_selector(self):
        """Update card selector dropdown"""
        self.card_selector.blockSignals(True)
        self.card_selector.clear()
        
        if self.current_set:
            for i in range(len(self.current_set.cards)):
                self.card_selector.addItem(f"Card {i + 1}")
            self.card_selector.setCurrentIndex(self.current_card_index)
            
        self.card_selector.blockSignals(False)
        
    def update_navigation_buttons(self):
        """Update navigation button states"""
        if not self.current_set:
            self.prev_card_button.setEnabled(False)
            self.next_card_button.setEnabled(False)
            return
            
        card_count = len(self.current_set.cards)
        self.prev_card_button.setEnabled(self.current_card_index > 0)
        self.next_card_button.setEnabled(self.current_card_index < card_count - 1)
        
    def update_side_indicator(self):
        """Update side indicator and flip button"""
        if self.current_side == "information":
            self.side_indicator.setText("Information Side")
            self.flip_side_button.setText("Switch to Answer")
            self.side_selector.setCurrentIndex(0)
        else:
            self.side_indicator.setText("Answer Side")
            self.flip_side_button.setText("Switch to Information")
            self.side_selector.setCurrentIndex(1)
            
    def on_previous_card_clicked(self):
        """Navigate to previous card"""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.display_current_card()
            self.update_card_selector()
            self.update_navigation_buttons()
            
    def on_next_card_clicked(self):
        """Navigate to next card"""
        if self.current_set and self.current_card_index < len(self.current_set.cards) - 1:
            self.current_card_index += 1
            self.display_current_card()
            self.update_card_selector()
            self.update_navigation_buttons()
            
    def on_new_card_clicked(self):
        """Create new blank card"""
        if not self.current_set:
            return
            
        new_card = self.current_set.create_empty_card()
        self.current_card_index = len(self.current_set.cards) - 1
        self.current_side = "information"
        
        self.update_card_selector()
        self.display_current_card()
        self.update_navigation_buttons()
        self.update_side_indicator()
        
    def on_ai_new_card_clicked(self):
        """Create new card using AI generation"""
        if not self.current_set:
            QMessageBox.warning(self, "No Set Loaded", "Please load a set before generating AI cards.")
            return
            
        # Show AI generation dialog
        dialog = AICardGenerationDialog(self.current_set, self)
        if dialog.exec_() == QDialog.Accepted:
            card_data = dialog.get_card_data()
            if card_data:
                # Create a new card with the AI-generated content
                new_card = self.current_set.create_empty_card()
                
                # Create text blocks for information and answer sides
                info_text = card_data.get("information", "")
                answer_text = card_data.get("answer", "")
                
                if info_text:
                    info_block = TextBlock()
                    info_block.set_text(info_text)
                    new_card.add_block_to_side("information", info_block)
                
                if answer_text:
                    answer_block = TextBlock()
                    answer_block.set_text(answer_text)
                    new_card.add_block_to_side("answer", answer_block)
                
                # Navigate to the new card
                self.current_card_index = len(self.current_set.cards) - 1
                self.current_side = "information"
                
                self.update_card_selector()
                self.display_current_card()
                self.update_navigation_buttons()
                self.update_side_indicator()
                
                # Auto-save the changes
                self.auto_save()
        
    def on_card_selector_changed(self, index):
        """Handle dropdown card selection"""
        if 0 <= index < len(self.current_set.cards):
            self.current_card_index = index
            self.display_current_card()
            self.update_navigation_buttons()
            
    def on_flip_side_clicked(self):
        """Switch between information and answer sides"""
        self.current_side = "answer" if self.current_side == "information" else "information"
        self.display_current_card()
        self.update_side_indicator()
        
    def on_side_tab_changed(self, index):
        """Handle side tab change"""
        self.current_side = "information" if index == 0 else "answer"
        self.display_current_card()
        self.update_side_indicator()
        
    def on_blocks_modified(self):
        """Handle block modifications"""
        # Mark set as modified (could add dirty flag here)
        pass
        
    def on_save_changes_clicked(self):
        """Save changes to vault"""
        if self.current_set:
            try:
                self.vault_manager.save_set(self.current_set)
                QMessageBox.information(self, "Saved", "Changes saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
                
    def on_return_to_vault_clicked(self):
        """Return to vault mode"""
        # Auto-save before returning
        self.auto_save()
        self.mode_change_requested.emit("vault", None)
        
    def auto_save(self):
        """Automatically save changes"""
        if self.current_set:
            try:
                self.vault_manager.save_set(self.current_set)
            except Exception as e:
                print(f"Auto-save failed: {e}")


class BlockEditorWidget(QWidget):
    """Interface for managing content blocks on card sides"""
    
    blocks_modified = pyqtSignal()
    
    def __init__(self, vault_manager=None, flash_set=None):
        super().__init__()
        self.vault_manager = vault_manager
        self.flash_set = flash_set
        self.current_blocks = []
        self.current_card_index = 0
        self.current_side = "information"
        self.max_blocks = 10
        self.setup_ui()
        
    def setup_ui(self):
        """Create editor layout"""
        layout = QVBoxLayout()
        
        # Block creation controls
        self.setup_block_creation()
        layout.addWidget(self.creation_frame)
        
        # Block list (scrollable)
        self.setup_block_list()
        layout.addWidget(self.block_scroll_area, 1)
        
        self.setLayout(layout)
        
    def setup_block_creation(self):
        """Create block creation controls"""
        self.creation_frame = QFrame()
        self.creation_frame.setFrameStyle(QFrame.StyledPanel)
        self.creation_frame.setMaximumHeight(60)
        
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Add Block:"))
        
        # Block type selector
        self.block_type_dropdown = QComboBox()
        self.block_type_dropdown.addItems(["Text", "Image", "Audio", "Video"])
        layout.addWidget(self.block_type_dropdown)
        
        # Create button
        self.create_button = QPushButton("Create")
        self.create_button.clicked.connect(self.on_create_block_clicked)
        layout.addWidget(self.create_button)
        
        # Block count info
        self.block_count_label = QLabel("0/10 blocks")
        layout.addWidget(self.block_count_label)
        
        layout.addStretch()
        self.creation_frame.setLayout(layout)
        
    def setup_block_list(self):
        """Create scrollable block list"""
        self.block_scroll_area = QScrollArea()
        self.block_scroll_area.setWidgetResizable(True)
        self.block_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for blocks
        self.block_container = QWidget()
        self.block_layout = QVBoxLayout()
        self.block_layout.addStretch()  # Push blocks to top
        self.block_container.setLayout(self.block_layout)
        
        self.block_scroll_area.setWidget(self.block_container)
        
    def set_context(self, vault_manager, flash_set):
        """Set vault manager and flash set context"""
        self.vault_manager = vault_manager
        self.flash_set = flash_set
        
    def set_blocks(self, blocks, card_index=0, side="information"):
        """Display blocks for editing"""
        ## DEBUG START
        print(f"DEBUG: BlockEditorWidget.set_blocks called")
        print(f"  blocks count: {len(blocks)}")
        print(f"  card_index: {card_index}")
        print(f"  side: {side}")
        ## DEBUG END
        
        self.current_blocks = blocks
        self.current_card_index = card_index
        self.current_side = side
        
        # Clear existing block widgets
        self.clear_block_widgets()
        
        # Create widgets for each block
        for i, block in enumerate(blocks):
            ## DEBUG START
            print(f"DEBUG: Creating widget for block {i}, type: {block.block_type}")
            ## DEBUG END
            
            block_widget = BlockEditItemWidget(
                block, i, self.vault_manager, self.flash_set
            )
            block_widget.move_up_requested.connect(self.on_block_move_up)
            block_widget.move_down_requested.connect(self.on_block_move_down)
            block_widget.delete_requested.connect(self.on_block_delete)
            block_widget.content_changed.connect(self.on_block_content_changed)
            
            # Insert before the stretch
            self.block_layout.insertWidget(self.block_layout.count() - 1, block_widget)
            
        self.update_block_count()
        self.update_move_buttons()
        
    def clear_block_widgets(self):
        """Remove all block widgets except stretch"""
        while self.block_layout.count() > 1:
            child = self.block_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
    def on_create_block_clicked(self):
        """Handle new block creation"""
        if len(self.current_blocks) >= self.max_blocks:
            QMessageBox.warning(self, "Block Limit", f"Maximum of {self.max_blocks} blocks per side")
            return
            
        block_type_text = self.block_type_dropdown.currentText().lower()
        
        try:
            new_block = create_block_from_type(block_type_text)
            
            # Add to current card
            if self.flash_set and self.current_card_index < len(self.flash_set.cards):
                card = self.flash_set.cards[self.current_card_index]
                card.add_block_to_side(self.current_side, new_block)
                
                # Refresh display
                updated_blocks = card.get_side_blocks(self.current_side)
                self.set_blocks(updated_blocks, self.current_card_index, self.current_side)
                
                self.blocks_modified.emit()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create block: {str(e)}")
            
    def on_block_move_up(self, block_index):
        """Handle block move up"""
        if block_index > 0 and self.flash_set:
            card = self.flash_set.cards[self.current_card_index]
            card.move_block(self.current_side, block_index, block_index - 1)
            
            # Refresh display
            updated_blocks = card.get_side_blocks(self.current_side)
            self.set_blocks(updated_blocks, self.current_card_index, self.current_side)
            
            self.blocks_modified.emit()
            
    def on_block_move_down(self, block_index):
        """Handle block move down"""
        if block_index < len(self.current_blocks) - 1 and self.flash_set:
            card = self.flash_set.cards[self.current_card_index]
            card.move_block(self.current_side, block_index, block_index + 1)
            
            # Refresh display
            updated_blocks = card.get_side_blocks(self.current_side)
            self.set_blocks(updated_blocks, self.current_card_index, self.current_side)
            
            self.blocks_modified.emit()
            
    def on_block_delete(self, block_index):
        """Handle block deletion"""
        if self.flash_set:
            reply = QMessageBox.question(
                self, "Delete Block", 
                "Are you sure you want to delete this block?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                card = self.flash_set.cards[self.current_card_index]
                
                # Get the block being deleted for media cleanup
                deleted_block = card.get_side_blocks(self.current_side)[block_index]
                
                # Clean up media files if it's a media block
                if hasattr(deleted_block, 'image_path') and deleted_block.image_path:
                    try:
                        image_path = deleted_block.get_full_path(self.vault_manager.vault_path, self.flash_set.name)
                        if image_path and image_path.exists():
                            image_path.unlink()
                    except Exception as e:
                        print(f"Error cleaning up image: {e}")
                elif hasattr(deleted_block, 'audio_path') and deleted_block.audio_path:
                    try:
                        audio_path = deleted_block.get_full_path(self.vault_manager.vault_path, self.flash_set.name)
                        if audio_path and audio_path.exists():
                            audio_path.unlink()
                    except Exception as e:
                        print(f"Error cleaning up audio: {e}")
                elif hasattr(deleted_block, 'video_path') and deleted_block.video_path:
                    try:
                        video_path = deleted_block.get_full_path(self.vault_manager.vault_path, self.flash_set.name)
                        if video_path and video_path.exists():
                            video_path.unlink()
                    except Exception as e:
                        print(f"Error cleaning up video: {e}")
                
                # Remove the block from the card
                card.remove_block_from_side(self.current_side, block_index)
                
                # Refresh display
                updated_blocks = card.get_side_blocks(self.current_side)
                self.set_blocks(updated_blocks, self.current_card_index, self.current_side)
                
                self.blocks_modified.emit()
                
    def on_block_content_changed(self, block_index):
        """Handle block content changes"""
        self.blocks_modified.emit()
        
    def update_block_count(self):
        """Update block count display"""
        count = len(self.current_blocks)
        self.block_count_label.setText(f"{count}/{self.max_blocks} blocks")
        
        # Enable/disable create button based on limit
        self.create_button.setEnabled(count < self.max_blocks)
        
    def update_move_buttons(self):
        """Update move button states for all block widgets"""
        for i in range(self.block_layout.count() - 1):  # Exclude stretch
            widget = self.block_layout.itemAt(i).widget()
            if isinstance(widget, BlockEditItemWidget):
                can_move_up = i > 0
                can_move_down = i < len(self.current_blocks) - 1
                widget.update_move_buttons(can_move_up, can_move_down)


class BlockEditItemWidget(QWidget):
    """Individual block editing widget with controls"""
    
    move_up_requested = pyqtSignal(int)  # block_index
    move_down_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    content_changed = pyqtSignal(int)
    
    def __init__(self, block, block_index, vault_manager=None, flash_set=None):
        super().__init__()
        self.block = block
        self.block_index = block_index
        self.vault_manager = vault_manager
        self.flash_set = flash_set
        self.setup_ui()
        
    def setup_ui(self):
        """Create item layout with controls"""
        layout = QHBoxLayout()
        
        # Move controls
        move_layout = QVBoxLayout()
        
        self.move_up_button = QPushButton("↑")
        self.move_up_button.setMaximumSize(30, 30)
        self.move_up_button.clicked.connect(self.on_move_up_clicked)
        move_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("↓")
        self.move_down_button.setMaximumSize(30, 30)
        self.move_down_button.clicked.connect(self.on_move_down_clicked)
        move_layout.addWidget(self.move_down_button)
        
        layout.addLayout(move_layout)
        
        # Content editor
        self.content_widget = self.create_content_widget()
        layout.addWidget(self.content_widget, 1)
        
        # Delete button
        self.delete_button = QPushButton("✕")
        self.delete_button.setMaximumSize(30, 30)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.delete_button.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.delete_button)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.StyledPanel)
        
    def create_content_widget(self):
        """Create block-specific editor widget"""
        set_name = self.flash_set.name if self.flash_set else None
        vault_path = self.vault_manager.vault_path if self.vault_manager else None
        
        ## DEBUG START
        print(f"DEBUG: create_content_widget called (BlockEditItemWidget)")
        print(f"  block type: {self.block.block_type}")
        print(f"  set_name: {set_name}")
        print(f"  vault_path: {vault_path}")
        if hasattr(self.block, 'image_path'):
            print(f"  block.image_path: {self.block.image_path}")
        ## DEBUG END
        
        widget = self.block.get_edit_widget(vault_path, set_name, self.vault_manager)
        
        # Connect content change signal if available
        if hasattr(widget, 'content_changed'):
            widget.content_changed.connect(self.on_content_changed)
            
        # For image widgets, ensure preview is refreshed after widget is fully set up
        if hasattr(widget, 'refresh_preview') and hasattr(self.block, 'image_path'):
            from PyQt5.QtCore import QTimer
            ## DEBUG START
            print(f"DEBUG: Scheduling refresh_preview for image widget")
            ## DEBUG END
            QTimer.singleShot(100, widget.refresh_preview)  # Delay to ensure widget is rendered
            
        return widget
        
    def on_move_up_clicked(self):
        """Signal block move up"""
        self.move_up_requested.emit(self.block_index)
        
    def on_move_down_clicked(self):
        """Signal block move down"""
        self.move_down_requested.emit(self.block_index)
        
    def on_delete_clicked(self):
        """Signal block deletion"""
        self.delete_requested.emit(self.block_index)
        
    def on_content_changed(self):
        """Signal content modification"""
        self.content_changed.emit(self.block_index)
        
    def update_move_buttons(self, can_move_up, can_move_down):
        """Update button states"""
        self.move_up_button.setEnabled(can_move_up)
        self.move_down_button.setEnabled(can_move_down)


# Make BlockEditItemWidget inherit from QFrame for styling
class BlockEditItemWidget(QFrame):
    """Individual block editing widget with controls"""
    
    move_up_requested = pyqtSignal(int)  # block_index
    move_down_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    content_changed = pyqtSignal(int)
    
    def __init__(self, block, block_index, vault_manager=None, flash_set=None):
        super().__init__()
        self.block = block
        self.block_index = block_index
        self.vault_manager = vault_manager
        self.flash_set = flash_set
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setup_ui()
        
    def setup_ui(self):
        """Create item layout with controls"""
        layout = QHBoxLayout()
        
        # Move controls
        move_layout = QVBoxLayout()
        
        self.move_up_button = QPushButton("↑")
        self.move_up_button.setMaximumSize(30, 30)
        self.move_up_button.clicked.connect(self.on_move_up_clicked)
        move_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("↓")
        self.move_down_button.setMaximumSize(30, 30)
        self.move_down_button.clicked.connect(self.on_move_down_clicked)
        move_layout.addWidget(self.move_down_button)
        
        layout.addLayout(move_layout)
        
        # Content editor
        self.content_widget = self.create_content_widget()
        layout.addWidget(self.content_widget, 1)
        
        # Delete button
        self.delete_button = QPushButton("✕")
        self.delete_button.setMaximumSize(30, 30)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.delete_button.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.delete_button)
        
        self.setLayout(layout)
        
    def create_content_widget(self):
        """Create block-specific editor widget"""
        set_name = self.flash_set.name if self.flash_set else None
        vault_path = self.vault_manager.vault_path if self.vault_manager else None
        
        ## DEBUG START
        print(f"DEBUG: create_content_widget called (BlockEditItemWidget #2)")
        print(f"  block type: {self.block.block_type}")
        print(f"  set_name: {set_name}")
        print(f"  vault_path: {vault_path}")
        if hasattr(self.block, 'image_path'):
            print(f"  block.image_path: {self.block.image_path}")
        ## DEBUG END
        
        widget = self.block.get_edit_widget(vault_path, set_name, self.vault_manager)
        
        # Connect content change signal if available
        if hasattr(widget, 'content_changed'):
            widget.content_changed.connect(self.on_content_changed)
            
        # For image widgets, ensure preview is refreshed after widget is fully set up
        if hasattr(widget, 'refresh_preview') and hasattr(self.block, 'image_path'):
            from PyQt5.QtCore import QTimer
            ## DEBUG START
            print(f"DEBUG: Scheduling refresh_preview for image widget #2")
            ## DEBUG END
            QTimer.singleShot(100, widget.refresh_preview)  # Delay to ensure widget is rendered
            
        return widget
        
    def on_move_up_clicked(self):
        """Signal block move up"""
        self.move_up_requested.emit(self.block_index)
        
    def on_move_down_clicked(self):
        """Signal block move down"""
        self.move_down_requested.emit(self.block_index)
        
    def on_delete_clicked(self):
        """Signal block deletion"""
        self.delete_requested.emit(self.block_index)
        
    def on_content_changed(self):
        """Signal content modification"""
        self.content_changed.emit(self.block_index)
        
    def update_move_buttons(self, can_move_up, can_move_down):
        """Update button states"""
        self.move_up_button.setEnabled(can_move_up)
        self.move_down_button.setEnabled(can_move_down)
class AICardGenerationWorker(QThread):
    """Worker thread for AI card generation requests"""
    
    finished = pyqtSignal(dict)  # Emits the result dictionary
    error = pyqtSignal(str)      # Emits error message
    
    def __init__(self, request_data, server_url="https://firettripperjeff.pythonanywhere.com"):
        super().__init__()
        self.request_data = request_data
        self.server_url = server_url
        
    def setup_ssl_handling(self):
        """Setup SSL certificate handling for corporate environments"""
        # Common locations for Zscaler certificates
        zscaler_cert_paths = [
            "/opt/zscaler/cert/cacert.pem",
            "/usr/local/share/ca-certificates/zscaler.crt", 
            "/etc/ssl/certs/zscaler.pem",
            os.path.expanduser("~/zscaler_cert.pem"),
            "./zscaler_cert.pem"
        ]
        
        cert_file = None
        for path in zscaler_cert_paths:
            if os.path.exists(path):
                cert_file = path
                break
        
        if cert_file:
            # Set the certificate bundle for requests
            os.environ['REQUESTS_CA_BUNDLE'] = cert_file
            os.environ['SSL_CERT_FILE'] = cert_file
        else:
            # Fallback: try to disable SSL verification if we can't find certificates
            try:
                # Disable SSL warnings
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                # Set environment variable to disable SSL verification
                os.environ['PYTHONHTTPSVERIFY'] = '0'
            except Exception:
                pass  # If this fails, we'll rely on system certificates
        
    def run(self):
        """Execute the AI request in background thread"""
        try:
            # Setup SSL handling for corporate environments
            self.setup_ssl_handling()
            
            # Prepare the request payload
            payload = {
                "app_code": "flashcards_app_001",
                "request_type": "generate_card_from_description",
                "request": json.dumps(self.request_data)
            }
            
            # Make the request with timeout and SSL handling
            try:
                response = requests.post(
                    f"{self.server_url}/ai_request", 
                    json=payload, 
                    timeout=30,  # 30 second timeout
                    verify=True  # Try SSL verification first
                )
            except requests.exceptions.SSLError:
                # If SSL verification fails, try without verification
                response = requests.post(
                    f"{self.server_url}/ai_request", 
                    json=payload, 
                    timeout=30,
                    verify=False  # Disable SSL verification as fallback
                )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    # Parse the AI response JSON
                    ai_response = result.get("ai_response", "{}")
                    try:
                        card_data = json.loads(ai_response)
                        self.finished.emit({
                            "status": "success",
                            "card_data": card_data,
                            "full_response": result
                        })
                    except json.JSONDecodeError as e:
                        self.error.emit(f"AI returned invalid JSON: {str(e)}\nResponse: {ai_response}")
                else:
                    self.error.emit(f"AI request failed: {result.get('error_message', 'Unknown error')}")
            else:
                self.error.emit(f"Server error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            self.error.emit("Request timed out. Please check your internet connection and try again.")
        except requests.exceptions.SSLError as e:
            self.error.emit(f"SSL Certificate error: {str(e)}\n\nThis may be due to corporate firewall/proxy settings. Please contact your IT department for assistance.")
        except requests.exceptions.ConnectionError as e:
            self.error.emit(f"Cannot connect to AI server: {str(e)}\n\nPlease check your internet connection and try again.")
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")


class AICardGenerationDialog(QDialog):
    """Dialog for generating flash cards using AI"""
    
    def __init__(self, current_set, parent=None):
        super().__init__(parent)
        self.current_set = current_set
        self.worker = None
        self.result_card_data = None
        self.setup_ui()
        self.populate_fields()
        
    def setup_ui(self):
        """Create dialog layout and widgets"""
        self.setWindowTitle("AI - Generate New Card")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Generate a new flashcard using AI based on your set description and existing cards.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Set description (editable)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setPlaceholderText("Description of your flashcard set...")
        form_layout.addRow("Set Description:", self.description_input)
        
        # Sample percentage slider
        slider_layout = QHBoxLayout()
        self.sample_slider = QSlider(Qt.Horizontal)
        self.sample_slider.setMinimum(0)
        self.sample_slider.setMaximum(100)
        self.sample_slider.setValue(50)  # Default 50%
        self.sample_slider.valueChanged.connect(self.update_sample_label)
        slider_layout.addWidget(self.sample_slider)
        
        self.sample_label = QLabel("50%")
        self.sample_label.setMinimumWidth(40)
        slider_layout.addWidget(self.sample_label)
        
        sample_widget = QWidget()
        sample_widget.setLayout(slider_layout)
        form_layout.addRow("Sample Cards %:", sample_widget)
        
        # Sample cards count
        self.sample_count_label = QLabel()
        form_layout.addRow("Cards to sample:", self.sample_count_label)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addStretch()
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.start_generation)
        self.generate_button.setDefault(True)
        button_layout.addWidget(self.generate_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def populate_fields(self):
        """Populate form fields with set data"""
        if self.current_set:
            self.description_input.setPlainText(self.current_set.description)
            self.update_sample_count()
    
    def update_sample_label(self, value):
        """Update sample percentage label"""
        self.sample_label.setText(f"{value}%")
        self.update_sample_count()
        
    def update_sample_count(self):
        """Update sample count label"""
        if not self.current_set:
            self.sample_count_label.setText("No set loaded")
            return
            
        total_cards = len(self.current_set.cards)
        sample_percentage = self.sample_slider.value()
        sample_count = max(1, int(total_cards * sample_percentage / 100)) if total_cards > 0 else 0
        
        self.sample_count_label.setText(f"{sample_count} of {total_cards} cards")
        
    def get_sample_cards(self):
        """Get sample cards based on percentage"""
        if not self.current_set or not self.current_set.cards:
            return []
            
        total_cards = len(self.current_set.cards)
        sample_percentage = self.sample_slider.value()
        sample_count = max(1, int(total_cards * sample_percentage / 100))
        
        # Randomly sample cards
        if sample_count >= total_cards:
            selected_cards = self.current_set.cards[:]
        else:
            selected_cards = random.sample(self.current_set.cards, sample_count)
        
        # Extract text content from selected cards
        sample_data = []
        for card in selected_cards:
            info_text = self.extract_text_content(card, "information")
            answer_text = self.extract_text_content(card, "answer")
            
            if info_text or answer_text:  # Only include cards with text content
                sample_data.append({
                    "information": info_text,
                    "answer": answer_text
                })
                
        return sample_data
        
    def extract_text_content(self, card, side):
        """Extract text content from card side"""
        blocks = card.get_side_blocks(side)
        text_content = []
        
        for block in blocks:
            if block.block_type == "text" and hasattr(block, 'text_content'):
                if block.text_content.strip():
                    text_content.append(block.text_content.strip())
                    
        return " ".join(text_content) if text_content else ""
        
    def start_generation(self):
        """Start AI card generation process"""
        # Validate input
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Missing Description", 
                              "Please enter a description for your flashcard set.")
            return
            
        # Prepare request data
        request_data = {
            "set_description": description,
            "example_cards": self.get_sample_cards()
        }
        
        # Disable UI and show progress
        self.generate_button.setEnabled(False)
        self.cancel_button.setText("Cancel")
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog("Generating card with AI...", "Cancel", 0, 0, self)
        self.progress_dialog.setModal(True)
        self.progress_dialog.show()
        self.progress_dialog.canceled.connect(self.cancel_generation)
        
        # Start worker thread
        self.worker = AICardGenerationWorker(request_data)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()
        
    def cancel_generation(self):
        """Cancel the AI generation process"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self.cleanup_generation()
        
    def cleanup_generation(self):
        """Cleanup after generation (success or failure)"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        self.generate_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        
    @pyqtSlot(dict)
    def on_generation_finished(self, result):
        """Handle successful AI generation"""
        self.cleanup_generation()
        
        card_data = result.get("card_data", {})
        information = card_data.get("information", "")
        answer = card_data.get("answer", "")
        
        if information and answer:
            self.result_card_data = card_data
            QMessageBox.information(self, "Success", 
                                  f"Card generated successfully!\n\n"
                                  f"Information: {information[:100]}{'...' if len(information) > 100 else ''}\n\n"
                                  f"Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid Response", 
                              "AI generated an incomplete card. Please try again.")
            
    @pyqtSlot(str)
    def on_generation_error(self, error_message):
        """Handle AI generation error"""
        self.cleanup_generation()
        QMessageBox.critical(self, "Generation Error", 
                           f"Failed to generate card:\n\n{error_message}")
        
    def get_card_data(self):
        """Return the generated card data"""
        return self.result_card_data
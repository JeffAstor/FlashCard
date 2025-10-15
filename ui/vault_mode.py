"""
Vault Mode Interface - Main vault interface for set management
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLabel, QDialog, 
                            QFormLayout, QLineEdit, QTextEdit, QComboBox, 
                            QSpinBox, QDialogButtonBox, QMessageBox, QFileDialog,
                            QScrollArea, QFrame, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from pathlib import Path
import json
import zipfile
import tempfile


class VaultModeWidget(QWidget):
    """Main vault interface for set management"""
    
    mode_change_requested = pyqtSignal(str, str)  # mode, data
    
    def __init__(self, app_controller, vault_manager):
        super().__init__()
        self.app_controller = app_controller
        self.vault_manager = vault_manager
        self.selected_set = None
        self.setup_ui()
        self.refresh_set_list()
        
    def setup_ui(self):
        """Create interface layout and widgets"""
        layout = QVBoxLayout()
        
        # Menu bar
        self.setup_vault_menu_bar()
        layout.addWidget(self.menu_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Set list
        self.setup_set_list()
        content_layout.addWidget(self.set_list_widget, 3)
        
        # Set details panel
        self.setup_details_panel()
        content_layout.addWidget(self.details_panel, 1)
        
        layout.addLayout(content_layout)
        self.setLayout(layout)
        
    def setup_vault_menu_bar(self):
        """Create vault-specific menu buttons"""
        self.menu_bar = QFrame()
        self.menu_bar.setFrameStyle(QFrame.StyledPanel)
        self.menu_bar.setMaximumHeight(50)
        
        layout = QHBoxLayout()
        
        # New card set button
        self.new_set_button = QPushButton("New Card Set")
        self.new_set_button.clicked.connect(self.on_new_set_clicked)
        layout.addWidget(self.new_set_button)
        
        # Load selected button
        self.load_set_button = QPushButton("Load Selected")
        self.load_set_button.setEnabled(False)
        self.load_set_button.clicked.connect(self.on_load_set_clicked)
        layout.addWidget(self.load_set_button)
        
        # Edit selected button
        self.edit_set_button = QPushButton("Edit Selected")
        self.edit_set_button.setEnabled(False)
        self.edit_set_button.clicked.connect(self.on_edit_set_clicked)
        layout.addWidget(self.edit_set_button)
        
        # Export selected button
        self.export_set_button = QPushButton("Export Selected")
        self.export_set_button.setEnabled(False)
        self.export_set_button.clicked.connect(self.on_export_set_clicked)
        layout.addWidget(self.export_set_button)
        
        # Import cards button
        self.import_cards_button = QPushButton("Import Cards")
        self.import_cards_button.clicked.connect(self.on_import_cards_clicked)
        layout.addWidget(self.import_cards_button)
        
        # Delete selected button
        self.delete_set_button = QPushButton("Delete Set")
        self.delete_set_button.setEnabled(False)
        self.delete_set_button.clicked.connect(self.on_delete_set_clicked)
        self.delete_set_button.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.delete_set_button)
        
        layout.addStretch()
        
        # Import vault button
        self.import_vault_button = QPushButton("Import Vault")
        self.import_vault_button.clicked.connect(self.on_import_vault_clicked)
        layout.addWidget(self.import_vault_button)
        
        # Export vault button
        self.export_vault_button = QPushButton("Export Vault")
        self.export_vault_button.clicked.connect(self.on_export_vault_clicked)
        layout.addWidget(self.export_vault_button)
        
        self.menu_bar.setLayout(layout)
        
    def setup_set_list(self):
        """Create set display area"""
        self.set_list_widget = SetListWidget()
        self.set_list_widget.set_selected.connect(self.on_set_selected)
        
    def setup_details_panel(self):
        """Create set details panel"""
        self.details_panel = QFrame()
        self.details_panel.setFrameStyle(QFrame.StyledPanel)
        self.details_panel.setMinimumWidth(250)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Set Details")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Icon display
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(128, 128)
        self.icon_label.setScaledContents(True)
        self.icon_label.setStyleSheet("border: 1px solid gray;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)
        
        # Set info
        self.name_label = QLabel("No set selected")
        self.name_label.setWordWrap(True)
        self.name_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.name_label)
        
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        self.stats_label = QLabel("")
        layout.addWidget(self.stats_label)
        
        # Edit Details button
        self.edit_details_button = QPushButton("Edit Details")
        self.edit_details_button.setEnabled(False)
        self.edit_details_button.clicked.connect(self.on_edit_details_clicked)
        layout.addWidget(self.edit_details_button)
        
        layout.addStretch()
        self.details_panel.setLayout(layout)
        
    def refresh_set_list(self):
        """Reload and display available sets"""
        try:
            sets = self.vault_manager.get_available_sets()
            set_data = []
            
            for set_name in sets:
                try:
                    metadata = self.vault_manager.get_set_metadata(set_name)
                    set_data.append(metadata)
                except Exception as e:
                    print(f"Error loading metadata for {set_name}: {e}")
                    
            self.set_list_widget.set_sets_data(set_data)
            self.update_details_panel(None)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load vault: {str(e)}")
            
    def on_set_selected(self, set_name):
        """Handle set selection"""
        self.selected_set = set_name
        
        # Update button states
        has_selection = set_name is not None
        self.load_set_button.setEnabled(has_selection)
        self.edit_set_button.setEnabled(has_selection)
        self.export_set_button.setEnabled(has_selection)
        self.delete_set_button.setEnabled(has_selection)
        self.edit_details_button.setEnabled(has_selection)
        
        # Update details panel
        self.update_details_panel(set_name)
        
    def update_details_panel(self, set_name):
        """Update the details panel with set information"""
        if not set_name:
            self.icon_label.clear()
            self.icon_label.setText("No Icon")
            self.name_label.setText("No set selected")
            self.description_label.setText("")
            self.stats_label.setText("")
            return
            
        try:
            metadata = self.vault_manager.get_set_metadata(set_name)
            
            # Update icon
            icon_set = metadata.get('icon_set', 'default')
            icon = self.app_controller.icon_manager.get_icon_pixmap(icon_set, 128)
            if not icon.isNull():
                self.icon_label.setPixmap(icon)
            else:
                self.icon_label.setText("No Icon")
                
            # Update text info
            self.name_label.setText(metadata.get('name', 'Unknown'))
            self.description_label.setText(metadata.get('description', 'No description'))
            
            # Update stats
            card_count = metadata.get('card_count', 0)
            difficulty = metadata.get('difficulty_level', 1)
            tags = metadata.get('tags', [])
            
            stats_text = f"Cards: {card_count}\nDifficulty: {difficulty}/5"
            if tags:
                stats_text += f"\nTags: {', '.join(tags)}"
                
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            print(f"Error updating details for {set_name}: {e}")
            
    def on_new_set_clicked(self):
        """Handle new set creation"""
        dialog = SetCreationDialog(self.app_controller.icon_manager, self.vault_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            set_data = dialog.get_set_data()
            try:
                flash_set = self.vault_manager.create_set(
                    set_data['name'],
                    set_data['description'],
                    set_data['icon_set'],
                    set_data['tags'],
                    set_data['difficulty']
                )
                self.refresh_set_list()
                
                # Switch to edit mode for the new set
                self.mode_change_requested.emit("edit", set_data['name'])
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create set: {str(e)}")
                
    def on_load_set_clicked(self):
        """Handle load set for study"""
        if not self.selected_set:
            QMessageBox.information(self, "No Selection", "Please select a set to study")
            return
            
        self.mode_change_requested.emit("view", self.selected_set)
        
    def on_edit_set_clicked(self):
        """Handle edit set"""
        if not self.selected_set:
            QMessageBox.information(self, "No Selection", "Please select a set to edit")
            return
            
        self.mode_change_requested.emit("edit", self.selected_set)
        
    def on_export_set_clicked(self):
        """Handle set export"""
        if not self.selected_set:
            QMessageBox.information(self, "No Selection", "Please select a set to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Set", f"{self.selected_set}.zip", "ZIP files (*.zip)"
        )
        
        if file_path:
            try:
                self.vault_manager.export_set(self.selected_set, file_path)
                QMessageBox.information(self, "Success", f"Set exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export set: {str(e)}")
                
    def on_import_cards_clicked(self):
        """Handle card import"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Cards", "", "ZIP files (*.zip)"
        )
        
        if file_path:
            try:
                dialog = CardImportDialog(file_path, self.vault_manager, self.app_controller.icon_manager, self)
                if dialog.exec_() == QDialog.Accepted:
                    # Import was successful, refresh the list
                    self.refresh_set_list()
                    import_name = dialog.get_import_name()
                    QMessageBox.information(self, "Success", f"Cards imported successfully as '{import_name}'")
            except ValueError as e:
                QMessageBox.warning(self, "Import Warning", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import cards: {str(e)}")
                
    def on_delete_set_clicked(self):
        """Handle set deletion"""
        if not self.selected_set:
            QMessageBox.information(self, "No Selection", "Please select a set to delete")
            return
            
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Delete Set", 
            f"Are you sure you want to delete the set '{self.selected_set}'?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.vault_manager.delete_set(self.selected_set)
                QMessageBox.information(self, "Success", f"Set '{self.selected_set}' has been deleted")
                
                # Clear selection and refresh the vault display
                self.selected_set = None
                self.refresh_set_list()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete set: {str(e)}")
                
    def on_edit_details_clicked(self):
        """Handle edit set details"""
        if not self.selected_set:
            QMessageBox.information(self, "No Selection", "Please select a set to edit")
            return
            
        try:
            metadata = self.vault_manager.get_set_metadata(self.selected_set)
            dialog = SetEditDialog(
                self.app_controller.icon_manager, 
                self.vault_manager, 
                self.selected_set,
                metadata,
                self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                updated_data = dialog.get_set_data()
                try:
                    # Update the set metadata
                    self.vault_manager.update_set_metadata(self.selected_set, updated_data)
                    
                    # If the name changed, we need to rename the set
                    if updated_data['name'] != self.selected_set:
                        self.vault_manager.rename_set(self.selected_set, updated_data['name'])
                        self.selected_set = updated_data['name']
                    
                    # Refresh the display
                    self.refresh_set_list()
                    self.update_details_panel(self.selected_set)
                    
                    QMessageBox.information(self, "Success", "Set details updated successfully")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to update set details: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load set details: {str(e)}")
                
    def on_export_vault_clicked(self):
        """Handle entire vault export"""
        from datetime import datetime
        default_name = f"FlashCard_Vault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Vault", default_name, "ZIP files (*.zip)"
        )
        
        if file_path:
            try:
                self.vault_manager.export_entire_vault(file_path)
                QMessageBox.information(self, "Success", f"Vault exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export vault: {str(e)}")
                
    def on_import_vault_clicked(self):
        """Handle vault import with merge options"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Vault", "", "ZIP files (*.zip)"
        )
        
        if file_path:
            dialog = VaultImportDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                merge_mode = dialog.get_merge_mode()
                
                try:
                    self.vault_manager.import_vault(file_path, merge_mode)
                    self.refresh_set_list()
                    QMessageBox.information(self, "Success", "Vault imported successfully")
                except ValueError as e:
                    QMessageBox.warning(self, "Import Warning", str(e))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to import vault: {str(e)}")


class SetListWidget(QListWidget):
    """Custom widget for displaying flash card sets"""
    
    set_selected = pyqtSignal(str)  # set_name
    
    def __init__(self):
        super().__init__()
        self.sets_data = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the list widget"""
        self.setSelectionMode(self.SingleSelection)
        self.itemClicked.connect(self.on_item_clicked)
        
    def set_sets_data(self, sets_data):
        """Update displayed sets"""
        self.sets_data = sets_data
        self.clear()
        
        for set_data in sets_data:
            item = QListWidgetItem()
            widget = SetListItemWidget(set_data, self.parent().app_controller.icon_manager)
            item.setSizeHint(widget.sizeHint())
            
            self.addItem(item)
            self.setItemWidget(item, widget)
            
    def on_item_clicked(self, item):
        """Handle item selection"""
        row = self.row(item)
        if 0 <= row < len(self.sets_data):
            set_name = self.sets_data[row].get('name')
            self.set_selected.emit(set_name)


class SetListItemWidget(QWidget):
    """Individual set item widget"""
    
    def __init__(self, set_data, icon_manager):
        super().__init__()
        self.set_data = set_data
        self.icon_manager = icon_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the item widget"""
        layout = QHBoxLayout()
        
        # Icon (smaller size for list)
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        icon_label.setScaledContents(True)
        icon_label.setStyleSheet("border: 1px solid gray;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        # Load actual icon
        icon_set = self.set_data.get('icon_set', 'default')
        icon_pixmap = self.icon_manager.get_icon_pixmap(icon_set, 64)
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap)
        else:
            icon_label.setText("No Icon")
        
        layout.addWidget(icon_label)
        
        # Set info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.set_data.get('name', 'Unknown'))
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        info_layout.addWidget(name_label)
        
        description = self.set_data.get('description', '')
        if len(description) > 100:
            description = description[:100] + "..."
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        # Stats
        card_count = self.set_data.get('card_count', 0)
        difficulty = self.set_data.get('difficulty_level', 1)
        stats_label = QLabel(f"Cards: {card_count} | Difficulty: {difficulty}/5")
        stats_label.setStyleSheet("color: gray;")
        info_layout.addWidget(stats_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        self.setLayout(layout)


class SetCreationDialog(QDialog):
    """Dialog for creating new flash card sets"""
    
    def __init__(self, icon_manager, vault_manager, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.vault_manager = vault_manager
        self.setup_ui()
        
    def setup_ui(self):
        """Create dialog layout and widgets"""
        self.setWindowTitle("Create New Flash Card Set")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(128)
        self.name_input.textChanged.connect(self.validate_input)
        form_layout.addRow("Name*:", self.name_input)
        
        # Description field
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        # Icon selector
        self.icon_selector = QComboBox()
        self.populate_icon_selector()
        form_layout.addRow("Icon Set:", self.icon_selector)
        
        # Tags field
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Enter tags separated by commas")
        form_layout.addRow("Tags:", self.tags_input)
        
        # Difficulty selector
        self.difficulty_selector = QSpinBox()
        self.difficulty_selector.setRange(1, 5)
        self.difficulty_selector.setValue(1)
        form_layout.addRow("Difficulty:", self.difficulty_selector)
        
        layout.addLayout(form_layout)
        
        # Custom icon section
        custom_icon_layout = QHBoxLayout()
        self.custom_icon_button = QPushButton("Browse for Custom Icon")
        self.custom_icon_button.clicked.connect(self.browse_custom_icon)
        custom_icon_layout.addWidget(self.custom_icon_button)
        
        self.custom_icon_label = QLabel("No custom icon selected")
        custom_icon_layout.addWidget(self.custom_icon_label)
        
        layout.addLayout(custom_icon_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Initially disable OK button
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        
    def populate_icon_selector(self):
        """Populate icon selector with available icon sets"""
        available_sets = self.icon_manager.get_available_icon_sets()
        self.icon_selector.addItems(available_sets)
        
        # Set default as selected
        if "default" in available_sets:
            self.icon_selector.setCurrentText("default")
            
    def browse_custom_icon(self):
        """Browse for custom icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.custom_icon_label.setText(f"Selected: {Path(file_path).name}")
            self.custom_icon_path = file_path
        else:
            self.custom_icon_label.setText("No custom icon selected")
            self.custom_icon_path = None
            
    def validate_input(self):
        """Validate user input"""
        name = self.name_input.text().strip()
        
        # Check if name is valid
        is_valid = True
        
        if not name:
            is_valid = False
        else:
            # Check name validity
            valid, error_msg = self.vault_manager.validate_set_name(name)
            if not valid:
                is_valid = False
                
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(is_valid)
        
    def get_set_data(self):
        """Return entered set data"""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        icon_set = self.icon_selector.currentText()
        difficulty = self.difficulty_selector.value()
        
        # Parse tags
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []
        
        # Handle custom icon if selected
        if hasattr(self, 'custom_icon_path') and self.custom_icon_path:
            try:
                # Create custom icon set
                custom_icon_name = f"custom_{name.lower().replace(' ', '_')}"
                self.icon_manager.install_custom_icon(self.custom_icon_path, custom_icon_name)
                icon_set = custom_icon_name
            except Exception as e:
                print(f"Error installing custom icon: {e}")
                # Fall back to selected icon set
                
        return {
            'name': name,
            'description': description,
            'icon_set': icon_set,
            'tags': tags,
            'difficulty': difficulty
        }


class SetEditDialog(QDialog):
    """Dialog for editing existing flash card sets"""
    
    def __init__(self, icon_manager, vault_manager, set_name, current_metadata, parent=None):
        super().__init__(parent)
        self.icon_manager = icon_manager
        self.vault_manager = vault_manager
        self.set_name = set_name
        self.current_metadata = current_metadata
        self.original_name = set_name
        self.setup_ui()
        self.populate_fields()
        
    def setup_ui(self):
        """Create dialog layout and widgets"""
        self.setWindowTitle(f"Edit Set Details - {self.set_name}")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # Form layout
        form_layout = QFormLayout()
        
        # Name field
        self.name_input = QLineEdit()
        self.name_input.setMaxLength(128)
        self.name_input.textChanged.connect(self.validate_input)
        form_layout.addRow("Name*:", self.name_input)
        
        # Description field
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_input)
        
        # Icon selector
        self.icon_selector = QComboBox()
        self.populate_icon_selector()
        form_layout.addRow("Icon Set:", self.icon_selector)
        
        # Tags field
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Enter tags separated by commas")
        form_layout.addRow("Tags:", self.tags_input)
        
        # Difficulty selector
        self.difficulty_selector = QSpinBox()
        self.difficulty_selector.setRange(1, 5)
        self.difficulty_selector.setValue(1)
        form_layout.addRow("Difficulty:", self.difficulty_selector)
        
        layout.addLayout(form_layout)
        
        # Custom icon section
        custom_icon_layout = QHBoxLayout()
        self.custom_icon_button = QPushButton("Browse for Custom Icon")
        self.custom_icon_button.clicked.connect(self.browse_custom_icon)
        custom_icon_layout.addWidget(self.custom_icon_button)
        
        self.custom_icon_label = QLabel("No custom icon selected")
        custom_icon_layout.addWidget(self.custom_icon_label)
        
        layout.addLayout(custom_icon_layout)
        
        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        layout.addWidget(self.button_box)
        self.setLayout(layout)
        
    def populate_icon_selector(self):
        """Populate icon selector with available icon sets"""
        available_sets = self.icon_manager.get_available_icon_sets()
        self.icon_selector.addItems(available_sets)
        
    def populate_fields(self):
        """Populate form fields with current set data"""
        self.name_input.setText(self.current_metadata.get('name', ''))
        self.description_input.setPlainText(self.current_metadata.get('description', ''))
        
        # Set icon selector
        icon_set = self.current_metadata.get('icon_set', 'default')
        index = self.icon_selector.findText(icon_set)
        if index >= 0:
            self.icon_selector.setCurrentIndex(index)
        
        # Set tags
        tags = self.current_metadata.get('tags', [])
        if tags:
            self.tags_input.setText(', '.join(tags))
        
        # Set difficulty
        difficulty = self.current_metadata.get('difficulty_level', 1)
        self.difficulty_selector.setValue(difficulty)
        
    def browse_custom_icon(self):
        """Browse for custom icon file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.custom_icon_label.setText(f"Selected: {Path(file_path).name}")
            self.custom_icon_path = file_path
        else:
            self.custom_icon_label.setText("No custom icon selected")
            self.custom_icon_path = None
            
    def validate_input(self):
        """Validate user input"""
        name = self.name_input.text().strip()
        
        # Check if name is valid
        is_valid = True
        
        if not name:
            is_valid = False
        else:
            # Only validate name if it's different from the original
            if name != self.original_name:
                valid, error_msg = self.vault_manager.validate_set_name(name)
                if not valid:
                    is_valid = False
                
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(is_valid)
        
    def get_set_data(self):
        """Return entered set data"""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        icon_set = self.icon_selector.currentText()
        difficulty = self.difficulty_selector.value()
        
        # Parse tags
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()] if tags_text else []
        
        # Handle custom icon if selected
        if hasattr(self, 'custom_icon_path') and self.custom_icon_path:
            try:
                # Create custom icon set
                custom_icon_name = f"custom_{name.lower().replace(' ', '_')}"
                self.icon_manager.install_custom_icon(self.custom_icon_path, custom_icon_name)
                icon_set = custom_icon_name
            except Exception as e:
                print(f"Error installing custom icon: {e}")
                # Fall back to selected icon set
                
        return {
            'name': name,
            'description': description,
            'icon_set': icon_set,
            'tags': tags,
            'difficulty': difficulty
        }


class VaultImportDialog(QDialog):
    """Dialog for vault import options"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Import Vault")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Instructions
        info_label = QLabel("Choose how to handle the imported vault:")
        layout.addWidget(info_label)
        
        # Options
        from PyQt5.QtWidgets import QRadioButton, QButtonGroup
        
        self.option_group = QButtonGroup()
        
        self.merge_radio = QRadioButton("Merge: Add imported sets to existing vault")
        self.merge_radio.setChecked(True)
        self.option_group.addButton(self.merge_radio)
        layout.addWidget(self.merge_radio)
        
        self.replace_radio = QRadioButton("Replace: Replace entire vault (backup will be created)")
        self.option_group.addButton(self.replace_radio)
        layout.addWidget(self.replace_radio)
        
        # Warning
        warning_label = QLabel("Warning: Replace mode will backup your current vault but completely replace it.")
        warning_label.setStyleSheet("color: red;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def get_merge_mode(self):
        """Get selected merge mode"""
        if self.replace_radio.isChecked():
            return "replace"
        else:
            return "merge"


class CardImportDialog(QDialog):
    """Dialog for importing cards from ZIP file"""
    
    def __init__(self, zip_path, vault_manager, icon_manager, parent=None):
        super().__init__(parent)
        self.zip_path = zip_path
        self.vault_manager = vault_manager
        self.icon_manager = icon_manager
        self.set_data = None
        self.original_name = ""
        self.icon_pixmap = None
        
        self.setWindowTitle("Import Cards")
        self.setModal(True)
        self.resize(400, 300)
        
        # Validate and load set data from ZIP
        if not self.validate_and_load_set():
            return
            
        self.setup_ui()
        
    def validate_and_load_set(self):
        """Validate ZIP file and load set metadata"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract ZIP file
                with zipfile.ZipFile(self.zip_path, 'r') as zipf:
                    zipf.extractall(temp_path)
                
                # Find set.json
                set_json_files = list(temp_path.rglob('set.json'))
                if not set_json_files:
                    QMessageBox.critical(self, "Invalid ZIP", "No set.json found in ZIP file")
                    return False
                    
                # Check for cards.json
                cards_json_files = list(temp_path.rglob('cards.json'))
                if not cards_json_files:
                    QMessageBox.critical(self, "Invalid ZIP", "No cards.json found in ZIP file")
                    return False
                
                # Load set metadata
                set_json_path = set_json_files[0]
                with open(set_json_path, 'r', encoding='utf-8') as f:
                    self.set_data = json.load(f)
                
                self.original_name = self.set_data.get('name', 'Unknown')
                
                # Validate icon set
                icon_set_name = self.set_data.get('icon_set', 'default')
                
                # Check if icon exists in ZIP file first
                icon_found = False
                icons_in_zip = list(temp_path.rglob(f'icons/{icon_set_name}/*.png'))
                
                if icons_in_zip:
                    # Icon found in ZIP, load it for preview
                    icon_256_files = [f for f in icons_in_zip if f.name == '256.png']
                    if icon_256_files:
                        self.icon_pixmap = QPixmap(str(icon_256_files[0]))
                        icon_found = True
                
                # If not in ZIP, check local icon manager
                if not icon_found and self.icon_manager:
                    if icon_set_name in self.icon_manager.get_available_icon_sets():
                        self.icon_pixmap = self.icon_manager.get_icon_pixmap(icon_set_name, 256)
                        icon_found = True
                
                if not icon_found:
                    QMessageBox.critical(self, "Invalid Set", 
                                       f"Icon set '{icon_set_name}' not found in ZIP file or locally")
                    return False
                
                return True
                
        except zipfile.BadZipFile:
            QMessageBox.critical(self, "Invalid File", "Selected file is not a valid ZIP file")
            return False
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Invalid Set", "set.json contains invalid JSON")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to validate ZIP file: {str(e)}")
            return False
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout()
        
        # Icon and basic info section
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QHBoxLayout()
        
        # Icon display
        icon_label = QLabel()
        if self.icon_pixmap and not self.icon_pixmap.isNull():
            # Scale icon to a reasonable size
            scaled_pixmap = self.icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
        else:
            icon_label.setText("No Icon")
            icon_label.setStyleSheet("border: 1px solid gray; padding: 20px;")
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(icon_label)
        
        # Set info
        details_layout = QVBoxLayout()
        
        # Name (editable)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(self.original_name)
        name_layout.addWidget(self.name_edit)
        details_layout.addLayout(name_layout)
        
        # Description (read-only)
        description = self.set_data.get('description', 'No description')
        desc_label = QLabel(f"Description: {description}")
        desc_label.setWordWrap(True)
        details_layout.addWidget(desc_label)
        
        # Card count
        card_count = self.set_data.get('card_count', 0)
        count_label = QLabel(f"Cards: {card_count}")
        details_layout.addWidget(count_label)
        
        # Icon set
        icon_set = self.set_data.get('icon_set', 'default')
        icon_set_label = QLabel(f"Icon Set: {icon_set}")
        details_layout.addWidget(icon_set_label)
        
        info_layout.addLayout(details_layout)
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # Name conflict warning
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: orange; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)
        
        # Connect name change to validation
        self.name_edit.textChanged.connect(self.validate_name)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.import_button = button_box.button(QDialogButtonBox.Ok)
        self.import_button.setText("Import")
        button_box.accepted.connect(self.import_set)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Initial name validation
        self.validate_name()
    
    def validate_name(self):
        """Validate the current name and show warnings"""
        current_name = self.name_edit.text().strip()
        
        if not current_name:
            self.warning_label.setText("Name cannot be empty")
            self.warning_label.show()
            self.import_button.setEnabled(False)
            return
        
        if current_name in self.vault_manager.get_available_sets():
            self.warning_label.setText(f"A set named '{current_name}' already exists. Please choose a different name.")
            self.warning_label.show()
            self.import_button.setEnabled(False)
            return
        
        # Name is valid
        self.warning_label.hide()
        self.import_button.setEnabled(True)
    
    def import_set(self):
        """Import the set with the specified name"""
        import_name = self.name_edit.text().strip()
        
        try:
            # Use vault manager to import the set
            imported_name = self.vault_manager.import_set(self.zip_path, import_name)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import set: {str(e)}")
    
    def get_import_name(self):
        """Return the name to use for importing"""
        return self.name_edit.text().strip()
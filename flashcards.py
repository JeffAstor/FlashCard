#!/usr/bin/env python3
"""
FlashCard Application - Main Entry Point
A PyQt5-based flash card application for creating, editing, and studying flash card sets.
"""

import sys
import os
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

# Import core application modules
from models.flashcard import FlashCard, FlashCardSet
from models.content_blocks import TextBlock, ImageBlock, AudioBlock, VideoBlock
from vault.vault_manager import VaultManager
from vault.icon_manager import IconManager
from utils.config_manager import ConfigManager
from utils.error_logger import ErrorLogger
from utils.file_manager import FileManager
from ui.vault_mode import VaultModeWidget
from ui.edit_mode import EditModeWidget
from ui.view_mode import ViewModeWidget


class SignalManager(QObject):
    """Centralized signal management for component communication"""
    mode_change_requested = pyqtSignal(str, object)
    set_modified = pyqtSignal(str)
    card_status_changed = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str, str)
    operation_completed = pyqtSignal(str, bool)


class MainWindow(QMainWindow):
    """Primary window container that hosts different mode interfaces"""
    
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.current_widget = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize main window UI"""
        self.setWindowTitle("FlashCard Application")
        self.setMinimumSize(800, 600)
        
        # Set window icon
        window_icon = self.app_controller.create_app_icon()
        if window_icon:
            self.setWindowIcon(window_icon)
        
        # Load window configuration
        config = self.app_controller.config_manager.get_setting('window', {})
        self.resize(config.get('width', 1024), config.get('height', 768))
        
        if config.get('maximized', False):
            self.showMaximized()
            
        self.setup_status_bar()
        
    def setup_status_bar(self):
        """Create status bar with loading indicators"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def set_mode_widget(self, widget):
        """Replace current interface with new mode widget"""
        if self.current_widget:
            self.current_widget.setParent(None)
        
        self.current_widget = widget
        self.setCentralWidget(widget)
        
    def show_loading(self, message):
        """Display loading indicator"""
        self.status_bar.showMessage(f"Loading: {message}")
        QApplication.processEvents()
        
    def hide_loading(self):
        """Hide loading indicator"""
        self.status_bar.showMessage("Ready")
        
    def update_status(self, message):
        """Update status text"""
        self.status_bar.showMessage(message)
        
    def closeEvent(self, event):
        """Handle application shutdown"""
        # Save window configuration
        config = self.app_controller.config_manager.config_data
        config['window']['width'] = self.width()
        config['window']['height'] = self.height()
        config['window']['maximized'] = self.isMaximized()
        
        self.app_controller.config_manager.save_config()
        event.accept()


class FlashCardApplication(QApplication):
    """Main application controller managing mode transitions and global state"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("FlashCard Application")
        self.setApplicationVersion("1.0.0")
        
        # Initialize core components
        self.setup_directories()
        self.config_manager = ConfigManager(self.get_config_path())
        self.error_logger = ErrorLogger(self.get_logs_path() / "error.log")
        self.icon_manager = IconManager(self.get_icons_path())
        self.vault_manager = VaultManager(self.get_vault_path(), self.icon_manager)
        self.file_manager = FileManager()
        self.signal_manager = SignalManager()
        
        # Set application icon
        app_icon = self.create_app_icon()
        if app_icon:
            self.setWindowIcon(app_icon)
        
        # Initialize main window
        self.main_window = MainWindow(self)
        
        # Connect signals
        self.setup_signals()
        
        # Start in vault mode
        self.switch_to_vault_mode()
        
    def setup_directories(self):
        """Create required directory structure"""
        base_path = Path(__file__).parent
        
        directories = [
            base_path / "config",
            base_path / "vault" / "sets", 
            base_path / "icons" / "default",
            base_path / "cache" / "thumbnails",
            base_path / "logs",
            base_path / "temp" / "exports",
            base_path / "documentation"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def setup_signals(self):
        """Connect application signals"""
        self.signal_manager.mode_change_requested.connect(self.handle_mode_change)
        self.signal_manager.error_occurred.connect(self.handle_error)
        
    def handle_mode_change(self, mode, data=None):
        """Handle mode change requests"""
        try:
            if mode == "vault":
                self.switch_to_vault_mode()
            elif mode == "edit":
                self.switch_to_edit_mode(data)
            elif mode == "view":
                self.switch_to_view_mode(data)
        except Exception as e:
            self.handle_error(str(e), f"Mode change to {mode}")
            
    def handle_error(self, error_message, context=""):
        """Handle application errors"""
        self.error_logger.log_error(error_message, context, "ERROR")
        self.show_error_dialog(error_message)
        
    def switch_to_vault_mode(self):
        """Transition to vault interface"""
        self.main_window.show_loading("Loading vault")
        try:
            vault_widget = VaultModeWidget(self, self.vault_manager)
            vault_widget.mode_change_requested.connect(self.handle_mode_change)
            self.main_window.set_mode_widget(vault_widget)
            self.main_window.update_status("Vault loaded successfully")
        except Exception as e:
            self.handle_error(str(e), "Loading vault mode")
        finally:
            self.main_window.hide_loading()
            
    def switch_to_edit_mode(self, set_name):
        """Transition to edit interface"""
        if not set_name:
            self.show_error_dialog("No set specified for editing")
            return
            
        self.main_window.show_loading(f"Loading set: {set_name}")
        try:
            edit_widget = EditModeWidget(self, self.vault_manager)
            edit_widget.mode_change_requested.connect(self.handle_mode_change)
            edit_widget.load_set(set_name)
            self.main_window.set_mode_widget(edit_widget)
            self.main_window.update_status(f"Editing set: {set_name}")
        except Exception as e:
            self.handle_error(str(e), f"Loading edit mode for {set_name}")
        finally:
            self.main_window.hide_loading()
            
    def switch_to_view_mode(self, set_name):
        """Transition to study interface"""
        if not set_name:
            self.show_error_dialog("No set specified for studying")
            return
            
        self.main_window.show_loading(f"Loading set: {set_name}")
        try:
            view_widget = ViewModeWidget(self, self.vault_manager)
            view_widget.mode_change_requested.connect(self.handle_mode_change)
            view_widget.load_set(set_name)
            self.main_window.set_mode_widget(view_widget)
            self.main_window.update_status(f"Studying set: {set_name}")
        except Exception as e:
            self.handle_error(str(e), f"Loading view mode for {set_name}")
        finally:
            self.main_window.hide_loading()
            
    def get_config_path(self):
        """Return path to config directory"""
        return Path(__file__).parent / "config" / "app_config.json"
        
    def get_vault_path(self):
        """Return path to vault directory"""
        return Path(__file__).parent / "vault"
        
    def get_icons_path(self):
        """Return path to icons directory"""
        return Path(__file__).parent / "icons"
        
    def get_logs_path(self):
        """Return path to logs directory"""
        return Path(__file__).parent / "logs"
        
    def create_app_icon(self):
        """Create application icon with multiple sizes"""
        icon = QIcon()
        icon_sizes = [16, 32, 64, 128, 256]
        icons_base_path = Path(__file__).parent / "icons" / "app"
        
        for size in icon_sizes:
            icon_path = icons_base_path / f"{size}.png"
            if icon_path.exists():
                icon.addFile(str(icon_path), QSize(size, size))
        
        return icon if not icon.isNull() else None
        
    def show_error_dialog(self, message):
        """Display error to user"""
        QMessageBox.critical(self.main_window, "Error", message)
        
    def run(self):
        """Start the application"""
        self.main_window.show()
        return self.exec_()


def main():
    """Application entry point"""
    app = FlashCardApplication(sys.argv)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
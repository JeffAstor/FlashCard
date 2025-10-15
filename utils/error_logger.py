"""
Error Logger - Centralized error logging and management
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QMessageBox


class ErrorLogger:
    """Centralized error logging and management"""
    
    def __init__(self, log_file_path):
        self.log_file_path = Path(log_file_path)
        self.error_history = []
        self.max_history = 100  # Keep last 100 errors in memory
        
        # Ensure log directory exists
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
    def log_error(self, error, context="", severity="ERROR"):
        """Log error with context"""
        timestamp = datetime.now().isoformat()
        
        # Create error entry
        error_entry = {
            "timestamp": timestamp,
            "error": str(error),
            "context": context,
            "severity": severity
        }
        
        # Add to memory history
        self.error_history.append(error_entry)
        
        # Keep only last max_history entries
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
            
        # Log to file
        log_message = f"{context} - {error}" if context else str(error)
        
        if severity == "ERROR":
            logging.error(log_message)
        elif severity == "WARNING":
            logging.warning(log_message)
        else:
            logging.info(log_message)
            
    def get_error_history(self):
        """Return recent errors"""
        return self.error_history.copy()
        
    def clear_log(self):
        """Clear error log"""
        self.error_history.clear()
        
        # Clear file log
        try:
            with open(self.log_file_path, 'w') as f:
                f.write("")
        except IOError:
            pass
            
    def show_error_dialog(self, parent, error_list=None):
        """Display error dialog"""
        if error_list is None:
            error_list = self.error_history
            
        dialog = ErrorLogDialog(parent, error_list, self)
        dialog.exec_()


class ErrorLogDialog(QDialog):
    """Dialog for displaying error log"""
    
    def __init__(self, parent, error_list, error_logger):
        super().__init__(parent)
        self.error_list = error_list
        self.error_logger = error_logger
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Error Log")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        
        # Error display
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.populate_error_text()
        
        layout.addWidget(self.error_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_errors)
        
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_log)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def populate_error_text(self):
        """Populate the error text display"""
        if not self.error_list:
            self.error_text.setText("No errors logged.")
            return
            
        error_text = ""
        for entry in reversed(self.error_list):  # Most recent first
            timestamp = entry["timestamp"]
            context = entry.get("context", "")
            error = entry["error"]
            severity = entry.get("severity", "ERROR")
            
            error_text += f"[{timestamp}] {severity}\n"
            if context:
                error_text += f"Context: {context}\n"
            error_text += f"Error: {error}\n"
            error_text += "-" * 50 + "\n\n"
            
        self.error_text.setText(error_text)
        
    def refresh_errors(self):
        """Refresh the error display"""
        self.error_list = self.error_logger.get_error_history()
        self.populate_error_text()
        
    def clear_log(self):
        """Clear the error log"""
        reply = QMessageBox.question(
            self, "Clear Log", 
            "Are you sure you want to clear the error log?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.error_logger.clear_log()
            self.error_list = []
            self.populate_error_text()
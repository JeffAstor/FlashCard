#!/usr/bin/env python3
"""
Test script for the enhanced TextBlockEditWidget formatting controls
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from models.content_blocks import TextBlock, TextBlockEditWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Block Formatting Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create a test text block
        self.text_block = TextBlock()
        self.text_block.set_text("Sample text for testing formatting")
        self.text_block.font_size = 16
        self.text_block.alignment = "center"
        
        # Create the edit widget
        self.edit_widget = TextBlockEditWidget(self.text_block)
        self.edit_widget.content_changed.connect(self.on_content_changed)
        
        # Set as central widget
        self.setCentralWidget(self.edit_widget)
        
    def on_content_changed(self):
        print(f"Content changed:")
        print(f"  Text: {self.text_block.text_content}")
        print(f"  Font size: {self.text_block.font_size}")
        print(f"  Alignment: {self.text_block.alignment}")
        print(f"  JSON: {self.text_block.to_dict()}")
        print("---")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    
    print("Text Block Formatting Test")
    print("==========================")
    print("Initial state:")
    print(f"  Text: {window.text_block.text_content}")
    print(f"  Font size: {window.text_block.font_size}")
    print(f"  Alignment: {window.text_block.alignment}")
    print("---")
    print("Try changing the font size and alignment in the UI!")
    
    sys.exit(app.exec_())
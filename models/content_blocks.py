"""
Content Block Models - Base classes and implementations for flash card content blocks
"""

import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QApplication, QFrame, QSpinBox, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QFont


class ContentBlock(ABC):
    """Base class for all content block types"""
    
    def __init__(self, block_type):
        self.block_id = str(uuid.uuid4())
        self.block_type = block_type
        self.created_date = datetime.now().isoformat()
        
    @abstractmethod
    def to_dict(self):
        """Serialize block to dictionary"""
        pass
        
    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        pass
        
    @abstractmethod
    def validate(self):
        """Validate block content"""
        pass
        
    @abstractmethod
    def get_display_widget(self, vault_path=None, set_name=None):
        """Return widget for display"""
        pass
        
    @abstractmethod
    def get_edit_widget(self, vault_path=None, set_name=None, vault_manager=None):
        """Return widget for editing"""
        pass


class TextBlock(ContentBlock):
    """Text content with rich formatting"""
    
    def __init__(self):
        super().__init__("text")
        self.text_content = ""
        self.font_size = 12
        self.alignment = "left"  # left, center, right
        self.max_chars = 1024
        
    def set_text(self, content):
        """Update text content with validation"""
        if len(content) > self.max_chars:
            raise ValueError(f"Text content exceeds maximum length of {self.max_chars} characters")
        self.text_content = content
        
    def set_formatting(self, font_size, alignment):
        """Update text formatting"""
        self.font_size = font_size
        self.alignment = alignment
        
    def get_plain_text(self):
        """Return plain text without formatting"""
        # Simple HTML tag removal for basic implementation
        import re
        return re.sub('<[^<]+?>', '', self.text_content)
        
    def to_dict(self):
        """Serialize block to dictionary"""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "text_content": self.text_content,
            "font_size": self.font_size,
            "alignment": self.alignment,
            "created_date": self.created_date
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        block = cls()
        block.block_id = data.get("block_id", block.block_id)
        block.text_content = data.get("text_content", "")
        block.font_size = data.get("font_size", 12)
        block.alignment = data.get("alignment", "left")
        block.created_date = data.get("created_date", block.created_date)
        return block
        
    def validate(self):
        """Validate block content"""
        if len(self.text_content) > self.max_chars:
            return False, f"Text exceeds {self.max_chars} characters"
        return True, ""
        
    def get_display_widget(self, vault_path=None, set_name=None):
        """Return QLabel for display"""
        label = QLabel(self.text_content)
        label.setWordWrap(True)
        
        # Set font size
        font = label.font()
        font.setPointSize(self.font_size)
        label.setFont(font)
        
        # Set alignment
        if self.alignment == "center":
            label.setAlignment(Qt.AlignCenter)
        elif self.alignment == "right":
            label.setAlignment(Qt.AlignRight)
        else:
            label.setAlignment(Qt.AlignLeft)
            
        return label
        
    def get_edit_widget(self, vault_path=None, set_name=None, vault_manager=None):
        """Return QTextEdit for editing"""
        edit_widget = TextBlockEditWidget(self)
        return edit_widget


class ImageBlock(ContentBlock):
    """Image content block with size validation"""
    
    def __init__(self):
        super().__init__("image")
        self.image_path = ""
        self.original_filename = ""
        self.width = 0
        self.height = 0
        self.max_width = 3840
        self.max_height = 2160
        
    def set_image(self, file_path, vault_manager=None, set_name=None):
        """Set image file with dimension validation"""
        from PIL import Image
        
        ## DEBUG START
        print(f"DEBUG: set_image called with:")
        print(f"  file_path: {file_path}")
        print(f"  vault_manager: {vault_manager}")
        print(f"  set_name: {set_name}")
        ## DEBUG END
        
        try:
            with Image.open(file_path) as img:
                self.width, self.height = img.size
                
            # Validate dimensions
            if self.width > self.max_width or self.height > self.max_height:
                raise ValueError(f"Image dimensions ({self.width}x{self.height}) exceed maximum allowed size ({self.max_width}x{self.max_height})")
                
            self.original_filename = Path(file_path).name
            
            ## DEBUG START
            print(f"DEBUG: Image validation passed:")
            print(f"  dimensions: {self.width}x{self.height}")
            print(f"  original_filename: {self.original_filename}")
            ## DEBUG END
            
            # If we have vault manager and set name, copy the file to vault
            if vault_manager and set_name:
                ## DEBUG START
                print(f"DEBUG: Attempting to copy file to vault...")
                ## DEBUG END
                
                # Store old path for cleanup
                old_image_path = self.image_path
                
                # Copy new file to vault
                copied_filename = vault_manager.copy_media_file(file_path, set_name, "image")
                self.image_path = copied_filename
                
                ## DEBUG START
                print(f"DEBUG: File copied successfully:")
                print(f"  old_image_path: {old_image_path}")
                print(f"  copied_filename: {copied_filename}")
                print(f"  new image_path: {self.image_path}")
                ## DEBUG END
                
                # Clean up old file if it exists and is different
                if old_image_path and old_image_path != copied_filename:
                    old_full_path = self.get_full_path(vault_manager.vault_path, set_name)
                    if old_full_path and old_full_path.exists():
                        ## DEBUG START
                        print(f"DEBUG: Cleaning up old file: {old_full_path}")
                        ## DEBUG END
                        old_full_path.unlink()
            else:
                ## DEBUG START
                print(f"DEBUG: No vault_manager or set_name, using fallback")
                ## DEBUG END
                # Fallback - just store the filename (for backwards compatibility)
                self.image_path = self.original_filename
            
        except Exception as e:
            ## DEBUG START
            print(f"DEBUG: Exception in set_image: {e}")
            ## DEBUG END
            raise ValueError(f"Invalid image file: {str(e)}")
            
    def get_full_path(self, vault_path, set_name):
        """Return full path to image"""
        if vault_path and set_name and self.image_path:
            return Path(vault_path) / "sets" / set_name / "images" / self.image_path
        return Path(self.image_path) if self.image_path else None
        
    def to_dict(self):
        """Serialize block to dictionary"""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "image_path": self.image_path,
            "original_filename": self.original_filename,
            "width": self.width,
            "height": self.height,
            "created_date": self.created_date
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        block = cls()
        block.block_id = data.get("block_id", block.block_id)
        block.image_path = data.get("image_path", "")
        block.original_filename = data.get("original_filename", "")
        block.width = data.get("width", 0)
        block.height = data.get("height", 0)
        block.created_date = data.get("created_date", block.created_date)
        return block
        
    def validate(self):
        """Validate block content"""
        if not self.image_path:
            return False, "No image file specified"
        if self.width > self.max_width or self.height > self.max_height:
            return False, f"Image dimensions exceed maximum size"
        return True, ""
        
    def get_display_widget(self, vault_path=None, set_name=None):
        """Return QLabel with scaled image"""
        label = QLabel()
        
        if self.image_path and vault_path and set_name:
            full_path = self.get_full_path(vault_path, set_name)
            if full_path and full_path.exists():
                pixmap = QPixmap(str(full_path))
                if not pixmap.isNull():
                    # We'll set a minimum width and let the parent container determine final size
                    # The scaling will be handled by a custom widget that can measure its container
                    scaled_pixmap = pixmap.scaled(600, 450, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    label.setPixmap(scaled_pixmap)
                else:
                    label.setText("Could not load image")
            else:
                label.setText("Image not found")
        else:
            label.setText("No image")
            
        label.setAlignment(Qt.AlignCenter)
        label.setScaledContents(False)  # We handle scaling manually
        return ImageDisplayLabel(label, self, vault_path, set_name)  # Return custom widget
        
    def get_edit_widget(self, vault_path=None, set_name=None, vault_manager=None):
        """Return image selection interface"""
        edit_widget = ImageBlockEditWidget(self, vault_path, set_name, vault_manager)
        return edit_widget


class AudioBlock(ContentBlock):
    """Audio file content block"""
    
    def __init__(self):
        super().__init__("audio")
        self.audio_path = ""
        self.original_filename = ""
        self.duration = 0
        
    def set_audio(self, file_path, vault_manager=None, set_name=None):
        """Set audio file with validation"""
        # Basic validation for audio file extensions
        valid_extensions = ['.wav', '.mp3', '.m4a', '.ogg']
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in valid_extensions:
            raise ValueError(f"Unsupported audio format: {file_ext}")
            
        self.original_filename = Path(file_path).name
        
        # If we have vault manager and set name, copy the file to vault
        if vault_manager and set_name:
            # Store old path for cleanup
            old_audio_path = self.audio_path
            
            # Copy new file to vault
            copied_filename = vault_manager.copy_media_file(file_path, set_name, "audio")
            self.audio_path = copied_filename
            
            # Clean up old file if it exists and is different
            if old_audio_path and old_audio_path != copied_filename:
                old_full_path = self.get_full_path(vault_manager.vault_path, set_name)
                if old_full_path and old_full_path.exists():
                    old_full_path.unlink()
        else:
            # Fallback - just store the filename (for backwards compatibility)
            self.audio_path = self.original_filename
        
    def get_full_path(self, vault_path, set_name):
        """Return full path to audio"""
        if vault_path and set_name and self.audio_path:
            return Path(vault_path) / "sets" / set_name / "sounds" / self.audio_path
        return Path(self.audio_path) if self.audio_path else None
        
    def to_dict(self):
        """Serialize block to dictionary"""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "audio_path": self.audio_path,
            "original_filename": self.original_filename,
            "duration": self.duration,
            "created_date": self.created_date
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        block = cls()
        block.block_id = data.get("block_id", block.block_id)
        block.audio_path = data.get("audio_path", "")
        block.original_filename = data.get("original_filename", "")
        block.duration = data.get("duration", 0)
        block.created_date = data.get("created_date", block.created_date)
        return block
        
    def validate(self):
        """Validate block content"""
        if not self.audio_path:
            return False, "No audio file specified"
        return True, ""
        
    def get_display_widget(self, vault_path=None, set_name=None):
        """Return audio player widget"""
        from ui.media_widgets import AudioPlayerWidget
        player = AudioPlayerWidget()
        if self.audio_path and vault_path and set_name:
            full_path = self.get_full_path(vault_path, set_name)
            if full_path.exists():
                player.load_media(str(full_path))
        return player
        
    def get_edit_widget(self, vault_path=None, set_name=None, vault_manager=None):
        """Return audio selection interface"""
        edit_widget = AudioBlockEditWidget(self, vault_path, set_name, vault_manager)
        return edit_widget


class VideoBlock(ContentBlock):
    """Video file content block (max 5 minutes)"""
    
    def __init__(self):
        super().__init__("video")
        self.video_path = ""
        self.original_filename = ""
        self.duration = 0
        self.thumbnail_path = ""
        self.max_duration = 300  # 5 minutes in seconds
        
    def set_video(self, file_path, vault_manager=None, set_name=None):
        """Set video file with validation"""
        # Basic validation for video file extensions
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in valid_extensions:
            raise ValueError(f"Unsupported video format: {file_ext}")
            
        # TODO: Add duration validation when media info library is available
        
        self.original_filename = Path(file_path).name
        
        # If we have vault manager and set name, copy the file to vault
        if vault_manager and set_name:
            # Store old path for cleanup
            old_video_path = self.video_path
            
            # Copy new file to vault
            copied_filename = vault_manager.copy_media_file(file_path, set_name, "video")
            self.video_path = copied_filename
            
            # Clean up old file if it exists and is different
            if old_video_path and old_video_path != copied_filename:
                old_full_path = self.get_full_path(vault_manager.vault_path, set_name)
                if old_full_path and old_full_path.exists():
                    old_full_path.unlink()
        else:
            # Fallback - just store the filename (for backwards compatibility)
            self.video_path = self.original_filename
        
    def get_full_path(self, vault_path, set_name):
        """Return full path to video"""
        if vault_path and set_name and self.video_path:
            return Path(vault_path) / "sets" / set_name / "sounds" / self.video_path
        return Path(self.video_path) if self.video_path else None
        
    def to_dict(self):
        """Serialize block to dictionary"""
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "video_path": self.video_path,
            "original_filename": self.original_filename,
            "duration": self.duration,
            "thumbnail_path": self.thumbnail_path,
            "created_date": self.created_date
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary"""
        block = cls()
        block.block_id = data.get("block_id", block.block_id)
        block.video_path = data.get("video_path", "")
        block.original_filename = data.get("original_filename", "")
        block.duration = data.get("duration", 0)
        block.thumbnail_path = data.get("thumbnail_path", "")
        block.created_date = data.get("created_date", block.created_date)
        return block
        
    def validate(self):
        """Validate block content"""
        if not self.video_path:
            return False, "No video file specified"
        if self.duration > self.max_duration:
            return False, f"Video duration exceeds {self.max_duration} seconds"
        return True, ""
        
    def get_display_widget(self, vault_path=None, set_name=None):
        """Return video player widget"""
        from ui.media_widgets import VideoPlayerWidget
        player = VideoPlayerWidget()
        if self.video_path and vault_path and set_name:
            full_path = self.get_full_path(vault_path, set_name)
            if full_path.exists():
                player.load_media(str(full_path))
        return player
        
    def get_edit_widget(self, vault_path=None, set_name=None, vault_manager=None):
        """Return video selection interface"""
        edit_widget = VideoBlockEditWidget(self, vault_path, set_name, vault_manager)
        return edit_widget


# Edit widget implementations

class TextBlockEditWidget(QWidget):
    """Edit widget for text blocks"""
    content_changed = pyqtSignal()
    
    def __init__(self, text_block):
        super().__init__()
        self.text_block = text_block
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Formatting controls
        format_frame = QFrame()
        format_frame.setFrameStyle(QFrame.StyledPanel)
        format_layout = QHBoxLayout()
        
        # Font size control
        format_layout.addWidget(QLabel("Font Size:"))
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72)
        self.font_size_spinbox.setValue(self.text_block.font_size)
        self.font_size_spinbox.valueChanged.connect(self.on_font_size_changed)
        format_layout.addWidget(self.font_size_spinbox)
        
        format_layout.addStretch()
        
        # Alignment control
        format_layout.addWidget(QLabel("Alignment:"))
        self.alignment_combo = QComboBox()
        self.alignment_combo.addItems(["left", "center", "right"])
        self.alignment_combo.setCurrentText(self.text_block.alignment)
        self.alignment_combo.currentTextChanged.connect(self.on_alignment_changed)
        format_layout.addWidget(self.alignment_combo)
        
        format_frame.setLayout(format_layout)
        layout.addWidget(format_frame)
        
        # Text content editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.text_block.text_content)
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        # Update preview with current formatting
        self.update_text_preview()
        
    def on_text_changed(self):
        self.text_block.text_content = self.text_edit.toPlainText()
        self.content_changed.emit()
        
    def on_font_size_changed(self, value):
        self.text_block.font_size = value
        self.update_text_preview()
        self.content_changed.emit()
        
    def on_alignment_changed(self, alignment):
        self.text_block.alignment = alignment
        self.update_text_preview()
        self.content_changed.emit()
        
    def update_text_preview(self):
        """Update the text edit widget to show formatting preview"""
        # Set font size in the editor for preview
        font = self.text_edit.font()
        font.setPointSize(self.text_block.font_size)
        self.text_edit.setFont(font)
        
        # Set alignment in the editor for preview
        if self.text_block.alignment == "center":
            self.text_edit.setAlignment(Qt.AlignCenter)
        elif self.text_block.alignment == "right":
            self.text_edit.setAlignment(Qt.AlignRight)
        else:
            self.text_edit.setAlignment(Qt.AlignLeft)


class ImageBlockEditWidget(QWidget):
    """Edit widget for image blocks"""
    content_changed = pyqtSignal()
    
    def __init__(self, image_block, vault_path=None, set_name=None, vault_manager=None):
        super().__init__()
        self.image_block = image_block
        self.vault_path = vault_path
        self.set_name = set_name
        self.vault_manager = vault_manager
        
        ## DEBUG START
        print(f"DEBUG: ImageBlockEditWidget created with:")
        print(f"  vault_path: {vault_path}")
        print(f"  set_name: {set_name}")
        print(f"  vault_manager: {vault_manager}")
        print(f"  image_block.image_path: {getattr(image_block, 'image_path', 'NONE')}")
        print(f"  image_block.original_filename: {getattr(image_block, 'original_filename', 'NONE')}")
        ## DEBUG END
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.preview_label = QLabel("No image selected")
        self.preview_label.setMinimumHeight(450)
        self.preview_label.setMinimumWidth(200)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.preview_label.setScaledContents(False)  # We'll handle scaling manually
        
        self.select_button = QPushButton("Select Image")
        self.select_button.clicked.connect(self.select_image)
        
        layout.addWidget(self.preview_label)
        layout.addWidget(self.select_button)
        self.setLayout(layout)
        
        # Don't call update_preview here, it will be called in showEvent
        
    def showEvent(self, event):
        """Called when the widget is shown - ensure preview is updated"""
        ## DEBUG START
        print(f"DEBUG: ImageBlockEditWidget.showEvent called")
        print(f"  widget size: {self.size()}")
        print(f"  preview_label size: {self.preview_label.size()}")
        ## DEBUG END
        super().showEvent(event)
        # Delay the update slightly to ensure the widget is fully rendered
        QTimer.singleShot(50, self.update_preview)  # 50ms delay
        
    def resizeEvent(self, event):
        """Called when the widget is resized - update image scaling"""
        super().resizeEvent(event)
        # Only update if we have an image loaded
        if self.image_block.image_path:
            # Delay slightly to ensure layout is complete
            QTimer.singleShot(10, self.update_preview)
        
    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                ## DEBUG START
                print(f"DEBUG: ImageBlockEditWidget.select_image called with: {file_path}")
                ## DEBUG END
                self.image_block.set_image(file_path, self.vault_manager, self.set_name)
                self.update_preview()
                self.content_changed.emit()
            except ValueError as e:
                # TODO: Show error dialog
                print(f"Error: {e}")
                
    def update_preview(self):
        ## DEBUG START
        print(f"DEBUG: update_preview called")
        print(f"  image_path: {self.image_block.image_path}")
        print(f"  vault_path: {self.vault_path}")
        print(f"  set_name: {self.set_name}")
        ## DEBUG END
        
        if self.image_block.image_path:
            # Try to display the actual image
            full_path = None
            if self.vault_path and self.set_name:
                full_path = self.image_block.get_full_path(self.vault_path, self.set_name)
                ## DEBUG START
                print(f"DEBUG: full_path from vault: {full_path}")
                print(f"DEBUG: file exists: {full_path.exists() if full_path else 'N/A'}")
                ## DEBUG END
            
            if full_path and full_path.exists():
                try:
                    # Load and scale the image
                    pixmap = QPixmap(str(full_path))
                    if not pixmap.isNull():
                        # Scale to fit the available space while maintaining aspect ratio
                        # Use most of the preview label size but leave some margin
                        available_width = self.preview_label.width() - 20  # 10px margin on each side
                        available_height = self.preview_label.height() - 20  # 10px margin top/bottom
                        
                        # If the label hasn't been rendered yet, use reasonable defaults
                        if available_width <= 20:
                            available_width = 180  # Fallback width
                        if available_height <= 20:
                            available_height = 430  # Fallback height (450 - 20 margin)
                        
                        # Scale to fit within available space while keeping aspect ratio
                        scaled_pixmap = pixmap.scaled(
                            available_width, available_height, 
                            Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        
                        self.preview_label.setPixmap(scaled_pixmap)
                        ## DEBUG START
                        print(f"DEBUG: Image scaled to fit {available_width}x{available_height}, result: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
                        ## DEBUG END
                    else:
                        self.preview_label.setText(f"Image: {self.image_block.original_filename}\n(Could not load image)")
                        ## DEBUG START
                        print(f"DEBUG: Could not load pixmap from: {full_path}")
                        ## DEBUG END
                except Exception as e:
                    ## DEBUG START
                    print(f"DEBUG: Exception loading image: {e}")
                    ## DEBUG END
                    self.preview_label.setText(f"Image: {self.image_block.original_filename}\n(Error loading image)")
            else:
                # File doesn't exist yet or no vault path, just show filename
                self.preview_label.setText(f"Image: {self.image_block.original_filename}")
                ## DEBUG START
                print(f"DEBUG: File not found, showing filename only")
                ## DEBUG END
        else:
            self.preview_label.setText("No image selected")
            self.preview_label.clear()  # Clear any existing pixmap
            
    def refresh_preview(self):
        """Public method to force a preview refresh"""
        ## DEBUG START
        print(f"DEBUG: refresh_preview called")
        ## DEBUG END
        QTimer.singleShot(10, self.update_preview)


class AudioBlockEditWidget(QWidget):
    """Edit widget for audio blocks"""
    content_changed = pyqtSignal()
    
    def __init__(self, audio_block, vault_path=None, set_name=None, vault_manager=None):
        super().__init__()
        self.audio_block = audio_block
        self.vault_path = vault_path
        self.set_name = set_name
        self.vault_manager = vault_manager
        self.audio_player = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Audio preview area
        self.preview_frame = QFrame()
        self.preview_frame.setFrameStyle(QFrame.StyledPanel)
        self.preview_frame.setMinimumHeight(150)
        self.preview_frame.setStyleSheet("background-color: #f0f0f0;")
        
        preview_layout = QVBoxLayout()
        
        self.info_label = QLabel("No audio selected")
        self.info_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.info_label)
        
        # Container for audio player (will be added when audio is loaded)
        self.player_container = QWidget()
        self.player_layout = QVBoxLayout()
        self.player_container.setLayout(self.player_layout)
        preview_layout.addWidget(self.player_container)
        
        self.preview_frame.setLayout(preview_layout)
        layout.addWidget(self.preview_frame)
        
        # File selection button
        self.select_button = QPushButton("Select Audio")
        self.select_button.clicked.connect(self.select_audio)
        layout.addWidget(self.select_button)
        
        self.setLayout(layout)
        
        # Initialize with current audio if available
        self.update_preview()
        
    def select_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio", "", "Audio Files (*.wav *.mp3 *.m4a *.ogg)"
        )
        
        if file_path:
            try:
                self.audio_block.set_audio(file_path, self.vault_manager, self.set_name)
                self.update_preview()
                self.content_changed.emit()
            except ValueError as e:
                # TODO: Show error dialog
                print(f"Error: {e}")
                
    def update_preview(self):
        """Update the audio preview"""
        # Clear existing player
        if self.audio_player:
            self.player_layout.removeWidget(self.audio_player)
            self.audio_player.deleteLater()
            self.audio_player = None
            
        if self.audio_block.audio_path:
            self.info_label.setText(f"Audio: {self.audio_block.original_filename}")
            
            # Try to create audio player if audio file exists
            if self.vault_path and self.set_name:
                full_path = self.audio_block.get_full_path(self.vault_path, self.set_name)
                if full_path and full_path.exists():
                    try:
                        # Import here to avoid circular imports
                        from ui.media_widgets import SimpleMediaPlayerWidget
                        
                        self.audio_player = SimpleMediaPlayerWidget("audio")
                        self.audio_player.load_media(str(full_path))
                        self.player_layout.addWidget(self.audio_player)
                        
                        # Show the audio player and hide/minimize the info label
                        self.info_label.hide()
                        
                    except Exception as e:
                        print(f"Error creating audio player: {e}")
                        self.info_label.setText(f"Audio: {self.audio_block.original_filename}\n(Preview not available)")
                        self.info_label.show()
                else:
                    self.info_label.setText(f"Audio: {self.audio_block.original_filename}\n(File not found)")
                    self.info_label.show()
            else:
                self.info_label.setText(f"Audio: {self.audio_block.original_filename}\n(Preview not available)")
                self.info_label.show()
        else:
            self.info_label.setText("No audio selected")
            self.info_label.show()


class VideoBlockEditWidget(QWidget):
    """Edit widget for video blocks"""
    content_changed = pyqtSignal()
    
    def __init__(self, video_block, vault_path=None, set_name=None, vault_manager=None):
        super().__init__()
        self.video_block = video_block
        self.vault_path = vault_path
        self.set_name = set_name
        self.vault_manager = vault_manager
        self.video_player = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Video preview area
        self.preview_frame = QFrame()
        self.preview_frame.setFrameStyle(QFrame.StyledPanel)
        self.preview_frame.setMinimumHeight(500)
        self.preview_frame.setStyleSheet("background-color: #f0f0f0;")
        
        preview_layout = QVBoxLayout()
        
        self.info_label = QLabel("No video selected")
        self.info_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.info_label)
        
        # Container for video player (will be added when video is loaded)
        self.player_container = QWidget()
        self.player_layout = QVBoxLayout()
        self.player_container.setLayout(self.player_layout)
        preview_layout.addWidget(self.player_container)
        
        self.preview_frame.setLayout(preview_layout)
        layout.addWidget(self.preview_frame)
        
        # File selection button
        self.select_button = QPushButton("Select Video")
        self.select_button.clicked.connect(self.select_video)
        layout.addWidget(self.select_button)
        
        self.setLayout(layout)
        
        # Initialize with current video if available
        self.update_preview()
        
    def select_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if file_path:
            try:
                self.video_block.set_video(file_path, self.vault_manager, self.set_name)
                self.update_preview()
                self.content_changed.emit()
            except ValueError as e:
                # TODO: Show error dialog
                print(f"Error: {e}")
                
    def update_preview(self):
        """Update the video preview"""
        # Clear existing player
        if self.video_player:
            self.player_layout.removeWidget(self.video_player)
            self.video_player.deleteLater()
            self.video_player = None
            
        if self.video_block.video_path:
            self.info_label.setText(f"Video: {self.video_block.original_filename}")
            
            # Try to create video player if video file exists
            if self.vault_path and self.set_name:
                full_path = self.video_block.get_full_path(self.vault_path, self.set_name)
                if full_path and full_path.exists():
                    try:
                        # Import here to avoid circular imports
                        from ui.media_widgets import SimpleMediaPlayerWidget
                        
                        self.video_player = SimpleMediaPlayerWidget("video")
                        self.video_player.load_media(str(full_path))
                        self.player_layout.addWidget(self.video_player)
                        
                        # Show the video player and hide/minimize the info label
                        self.info_label.hide()
                        
                    except Exception as e:
                        print(f"Error creating video player: {e}")
                        self.info_label.setText(f"Video: {self.video_block.original_filename}\n(Preview not available)")
                        self.info_label.show()
                else:
                    self.info_label.setText(f"Video: {self.video_block.original_filename}\n(File not found)")
                    self.info_label.show()
            else:
                self.info_label.setText(f"Video: {self.video_block.original_filename}\n(Preview not available)")
                self.info_label.show()
        else:
            self.info_label.setText("No video selected")
            self.info_label.show()


def create_block_from_type(block_type):
    """Factory function to create blocks from type string"""
    if block_type == "text":
        return TextBlock()
    elif block_type == "image":
        return ImageBlock()
    elif block_type == "audio":
        return AudioBlock()
    elif block_type == "video":
        return VideoBlock()
    else:
        raise ValueError(f"Unknown block type: {block_type}")


def create_block_from_dict(data):
    """Factory function to create blocks from dictionary data"""
    block_type = data.get("block_type")
    
    if block_type == "text":
        return TextBlock.from_dict(data)
    elif block_type == "image":
        return ImageBlock.from_dict(data)
    elif block_type == "audio":
        return AudioBlock.from_dict(data)
    elif block_type == "video":
        return VideoBlock.from_dict(data)
    else:
        raise ValueError(f"Unknown block type: {block_type}")


class ImageDisplayLabel(QLabel):
    """Custom label that scales images to 90% of container width"""
    
    def __init__(self, original_label, image_block, vault_path, set_name):
        super().__init__()
        self.image_block = image_block
        self.vault_path = vault_path
        self.set_name = set_name
        
        # Copy properties from original label
        self.setAlignment(original_label.alignment())
        self.setScaledContents(False)
        
        # Load the image
        self.original_pixmap = None
        self.load_image()
        
    def load_image(self):
        """Load the original image"""
        if self.image_block.image_path and self.vault_path and self.set_name:
            full_path = self.image_block.get_full_path(self.vault_path, self.set_name)
            if full_path and full_path.exists():
                self.original_pixmap = QPixmap(str(full_path))
                if self.original_pixmap.isNull():
                    self.setText("Could not load image")
                    self.original_pixmap = None
            else:
                self.setText("Image not found")
        else:
            self.setText("No image")
            
    def resizeEvent(self, event):
        """Handle resize events to scale image appropriately"""
        super().resizeEvent(event)
        if self.original_pixmap and not self.original_pixmap.isNull():
            self.scale_image()
            
    def scale_image(self):
        """Scale image to 90% of widget width while maintaining aspect ratio"""
        if not self.original_pixmap:
            return
            
        # Get 90% of the widget width
        target_width = int(self.width() * 0.9)
        
        # Don't scale if image is smaller than target
        if self.original_pixmap.width() <= target_width:
            scaled_pixmap = self.original_pixmap
        else:
            # Scale to target width while maintaining aspect ratio
            scaled_pixmap = self.original_pixmap.scaledToWidth(target_width, Qt.SmoothTransformation)
            
        self.setPixmap(scaled_pixmap)
        
    def showEvent(self, event):
        """Handle show events to ensure proper initial scaling"""
        super().showEvent(event)
        if self.original_pixmap:
            self.scale_image()
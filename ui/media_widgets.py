"""
Media Widgets - Custom media player widgets for audio and video content
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
from pathlib import Path


class AudioPlayerWidget(QWidget):
    """Custom audio player widget"""
    
    def __init__(self):
        super().__init__()
        self.media_player = QMediaPlayer()
        self.media_loaded = False
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Create player interface"""
        layout = QVBoxLayout()
        
        # Info label
        self.info_label = QLabel("No audio loaded")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setEnabled(False)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout)
        self.setLayout(layout)
        
    def setup_connections(self):
        """Connect media player signals"""
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.error.connect(self.on_error)
        
        # Set initial volume
        self.media_player.setVolume(50)
        
    def load_media(self, file_path):
        """Load media file"""
        file_path = Path(file_path)
        if file_path.exists():
            media_content = QMediaContent(QUrl.fromLocalFile(str(file_path.absolute())))
            self.media_player.setMedia(media_content)
            self.info_label.setText(f"Audio: {file_path.name}")
            self.play_button.setEnabled(True)
            self.position_slider.setEnabled(True)
            self.media_loaded = True
        else:
            self.info_label.setText("Audio file not found")
            self.play_button.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.media_loaded = False
            
    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.media_loaded:
            return
            
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def set_position(self, position):
        """Set playback position"""
        self.media_player.setPosition(position)
        
    def set_volume(self, volume):
        """Set playback volume"""
        self.media_player.setVolume(volume)
        
    def on_state_changed(self, state):
        """Handle state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")
            
    def on_position_changed(self, position):
        """Handle position updates"""
        self.position_slider.setValue(position)
        self.update_time_label(position, self.media_player.duration())
        
    def on_duration_changed(self, duration):
        """Handle duration updates"""
        self.position_slider.setRange(0, duration)
        self.update_time_label(self.media_player.position(), duration)
        
    def on_error(self, error):
        """Handle playback errors"""
        self.info_label.setText(f"Error: {self.media_player.errorString()}")
        
    def update_time_label(self, position, duration):
        """Update time display"""
        def format_time(ms):
            seconds = ms // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
            
        current_time = format_time(position)
        total_time = format_time(duration)
        self.time_label.setText(f"{current_time} / {total_time}")


class VideoPlayerWidget(QWidget):
    """Custom video player widget"""
    
    def __init__(self):
        super().__init__()
        self.media_player = QMediaPlayer()
        self.media_loaded = False
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Create player interface"""
        layout = QVBoxLayout()
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(320, 240)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)
        
        # Info label
        self.info_label = QLabel("No video loaded")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        
        # Play/Pause button
        self.play_button = QPushButton("Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_playback)
        controls_layout.addWidget(self.stop_button)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setEnabled(False)
        self.position_slider.sliderMoved.connect(self.set_position)
        controls_layout.addWidget(self.position_slider)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        controls_layout.addWidget(self.time_label)
        
        layout.addLayout(controls_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout)
        self.setLayout(layout)
        
    def setup_connections(self):
        """Connect media player signals"""
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.error.connect(self.on_error)
        
        # Set initial volume
        self.media_player.setVolume(50)
        
    def load_media(self, file_path):
        """Load media file"""
        file_path = Path(file_path)
        if file_path.exists():
            media_content = QMediaContent(QUrl.fromLocalFile(str(file_path.absolute())))
            self.media_player.setMedia(media_content)
            self.info_label.setText(f"Video: {file_path.name}")
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.position_slider.setEnabled(True)
            self.media_loaded = True
        else:
            self.info_label.setText("Video file not found")
            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.media_loaded = False
            
    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.media_loaded:
            return
            
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def stop_playback(self):
        """Stop playback"""
        self.media_player.stop()
        
    def set_position(self, position):
        """Set playback position"""
        self.media_player.setPosition(position)
        
    def set_volume(self, volume):
        """Set playback volume"""
        self.media_player.setVolume(volume)
        
    def on_state_changed(self, state):
        """Handle state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")
            
    def on_position_changed(self, position):
        """Handle position updates"""
        self.position_slider.setValue(position)
        self.update_time_label(position, self.media_player.duration())
        
    def on_duration_changed(self, duration):
        """Handle duration updates"""
        self.position_slider.setRange(0, duration)
        self.update_time_label(self.media_player.position(), duration)
        
    def on_error(self, error):
        """Handle playback errors"""
        self.info_label.setText(f"Error: {self.media_player.errorString()}")
        
    def update_time_label(self, position, duration):
        """Update time display"""
        def format_time(ms):
            seconds = ms // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
            
        current_time = format_time(position)
        total_time = format_time(duration)
        self.time_label.setText(f"{current_time} / {total_time}")


class SimpleMediaPlayerWidget(QWidget):
    """Simplified media player for display mode"""
    
    def __init__(self, media_type="audio"):
        super().__init__()
        self.media_type = media_type
        self.media_player = QMediaPlayer()
        self.media_loaded = False
        self.setup_ui()
        
    def setup_ui(self):
        """Create simplified player interface"""
        layout = QVBoxLayout()
        
        if self.media_type == "video":
            # Video widget for video files
            self.video_widget = QVideoWidget()
            self.video_widget.setMinimumSize(200, 150)
            self.media_player.setVideoOutput(self.video_widget)
            layout.addWidget(self.video_widget)
            
        # Simple play button
        self.play_button = QPushButton("▶ Play")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_playback)
        layout.addWidget(self.play_button)
        
        self.setLayout(layout)
        
        # Connect media player
        self.media_player.stateChanged.connect(self.on_state_changed)
        
    def load_media(self, file_path):
        """Load media file"""
        file_path = Path(file_path)
        if file_path.exists():
            media_content = QMediaContent(QUrl.fromLocalFile(str(file_path.absolute())))
            self.media_player.setMedia(media_content)
            self.play_button.setEnabled(True)
            self.media_loaded = True
        else:
            self.play_button.setEnabled(False)
            self.media_loaded = False
            
    def toggle_playback(self):
        """Toggle play/pause"""
        if not self.media_loaded:
            return
            
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def on_state_changed(self, state):
        """Handle state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸ Pause")
        else:
            self.play_button.setText("▶ Play")
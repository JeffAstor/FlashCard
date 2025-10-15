"""
Icon Manager - Manages application icon sets and custom icons
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
from PyQt5.QtGui import QIcon, QPixmap
from utils.file_manager import FileManager


class IconManager:
    """Manages application icon sets and custom icons"""
    
    def __init__(self, icons_path):
        self.icons_path = Path(icons_path)
        self.available_icon_sets = []
        self.file_manager = FileManager()
        self.icon_sizes = [256, 128, 64, 32, 16]
        
        # Ensure icons directory exists
        self.icons_path.mkdir(parents=True, exist_ok=True)
        
        # Install default icons if missing
        self.install_default_icon_collection()
        
        # Scan for available icon sets
        self.refresh_available_icons()
        
    def refresh_available_icons(self):
        """Scan and validate available icon sets"""
        self.available_icon_sets = []
        
        try:
            for icon_dir in self.icons_path.iterdir():
                if icon_dir.is_dir():
                    if self.validate_icon_set(icon_dir):
                        self.available_icon_sets.append(icon_dir.name)
                        
            # Ensure default is always available
            if "default" not in self.available_icon_sets:
                self.install_default_icon_collection()
                self.available_icon_sets.append("default")
                
        except Exception as e:
            print(f"Error scanning icon sets: {e}")
            
    def get_available_icon_sets(self):
        """Return list of valid icon sets"""
        return self.available_icon_sets.copy()
        
    def validate_icon_set(self, icon_set_path):
        """Check if icon set is complete"""
        icon_set_path = Path(icon_set_path)
        
        if not icon_set_path.exists() or not icon_set_path.is_dir():
            return False
            
        # Check for all required sizes
        for size in self.icon_sizes:
            icon_file = icon_set_path / f"{size}.png"
            if not icon_file.exists():
                return False
                
        return True
        
    def get_icon(self, icon_set, size=256):
        """Return QIcon for specified set and size"""
        if icon_set not in self.available_icon_sets:
            icon_set = "default"
            
        if size not in self.icon_sizes:
            size = 256  # Default to largest size
            
        icon_path = self.icons_path / icon_set / f"{size}.png"
        
        if icon_path.exists():
            return QIcon(str(icon_path))
        else:
            # Fallback to default icon
            default_path = self.icons_path / "default" / f"{size}.png"
            if default_path.exists():
                return QIcon(str(default_path))
            else:
                return QIcon()  # Empty icon
                
    def get_icon_pixmap(self, icon_set, size=256):
        """Return QPixmap for specified set and size"""
        if icon_set not in self.available_icon_sets:
            icon_set = "default"
            
        if size not in self.icon_sizes:
            size = 256
            
        icon_path = self.icons_path / icon_set / f"{size}.png"
        
        if icon_path.exists():
            return QPixmap(str(icon_path))
        else:
            # Fallback to default icon
            default_path = self.icons_path / "default" / f"{size}.png"
            if default_path.exists():
                return QPixmap(str(default_path))
            else:
                return QPixmap()
                
    def install_custom_icon(self, image_path, icon_set_name):
        """Create custom icon set from image"""
        source_path = Path(image_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")
            
        # Validate image
        is_valid, error_msg = self.file_manager.validate_media_file(image_path, "image")
        if not is_valid:
            raise ValueError(error_msg)
            
        # Create icon set directory
        icon_set_path = self.icons_path / icon_set_name
        icon_set_path.mkdir(parents=True, exist_ok=True)
        
        # Generate all icon sizes
        self.resize_and_save_icon(source_path, icon_set_path)
        
        # Update available icon sets
        self.refresh_available_icons()
        
        return icon_set_name
        
    def resize_and_save_icon(self, source_path, icon_set_path):
        """Generate all icon sizes from source image"""
        try:
            with Image.open(source_path) as img:
                # Convert to RGBA for transparency support
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                # Generate all required sizes
                for size in self.icon_sizes:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    output_path = icon_set_path / f"{size}.png"
                    resized.save(output_path, 'PNG', optimize=True)
                    
        except Exception as e:
            raise ValueError(f"Error processing icon image: {str(e)}")
            
    def get_default_icon(self, size=256):
        """Return default application icon"""
        return self.get_icon("default", size)
        
    def install_default_icon_collection(self):
        """Install built-in educational icons"""
        default_path = self.icons_path / "default"
        default_path.mkdir(parents=True, exist_ok=True)
        
        # Create simple default icons if they don't exist
        for size in self.icon_sizes:
            icon_file = default_path / f"{size}.png"
            if not icon_file.exists():
                self._create_default_icon(icon_file, size)
                
    def _create_default_icon(self, output_path, size):
        """Create a simple default icon"""
        try:
            # Create a simple icon with educational theme
            img = Image.new('RGBA', (size, size), (70, 130, 180, 255))  # Steel blue background
            
            # Add a simple book-like shape
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # Calculate proportional sizes
            margin = size // 8
            book_width = size - (2 * margin)
            book_height = int(book_width * 0.8)
            
            # Draw book outline
            book_x = margin
            book_y = (size - book_height) // 2
            
            # Book background
            draw.rectangle(
                [book_x, book_y, book_x + book_width, book_y + book_height],
                fill=(255, 255, 255, 255),
                outline=(50, 50, 50, 255),
                width=max(1, size // 64)
            )
            
            # Book spine line
            spine_x = book_x + book_width // 4
            draw.line(
                [spine_x, book_y, spine_x, book_y + book_height],
                fill=(200, 200, 200, 255),
                width=max(1, size // 32)
            )
            
            # Save the icon
            img.save(output_path, 'PNG', optimize=True)
            
        except Exception as e:
            # If anything fails, create a simple solid color icon
            img = Image.new('RGBA', (size, size), (70, 130, 180, 255))
            img.save(output_path, 'PNG')
            
    def get_icon_categories(self):
        """Return available icon categories"""
        categories = {
            "Educational": ["default", "math", "science", "language", "history"],
            "Study Types": ["vocabulary", "concepts", "formulas", "facts"],
            "Difficulty": ["beginner", "intermediate", "advanced"],
            "General": ["study", "quiz", "test", "learning", "books"]
        }
        
        # Filter by actually available icon sets
        available_categories = {}
        for category, icon_sets in categories.items():
            available_sets = [icon_set for icon_set in icon_sets if icon_set in self.available_icon_sets]
            if available_sets:
                available_categories[category] = available_sets
                
        return available_categories
        
    def create_educational_icon_set(self, name, color_scheme):
        """Create an educational-themed icon set"""
        icon_set_path = self.icons_path / name
        icon_set_path.mkdir(parents=True, exist_ok=True)
        
        try:
            for size in self.icon_sizes:
                self._create_educational_icon(icon_set_path / f"{size}.png", size, color_scheme)
                
            self.refresh_available_icons()
            return name
            
        except Exception as e:
            # Clean up on failure
            if icon_set_path.exists():
                import shutil
                shutil.rmtree(icon_set_path)
            raise ValueError(f"Error creating icon set: {str(e)}")
            
    def _create_educational_icon(self, output_path, size, color_scheme):
        """Create an educational-themed icon"""
        # This is a simplified implementation
        # In a full implementation, you'd create different themed icons
        
        base_color = color_scheme.get("background", (70, 130, 180))
        accent_color = color_scheme.get("accent", (255, 255, 255))
        
        img = Image.new('RGBA', (size, size), (*base_color, 255))
        
        # Add simple geometric shape based on theme
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        margin = size // 6
        center = size // 2
        
        # Draw a simple circle or square
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=(*accent_color, 200),
            outline=(*accent_color, 255),
            width=max(1, size // 32)
        )
        
        img.save(output_path, 'PNG', optimize=True)
        
    def delete_icon_set(self, icon_set_name):
        """Delete a custom icon set"""
        if icon_set_name == "default":
            raise ValueError("Cannot delete default icon set")
            
        icon_set_path = self.icons_path / icon_set_name
        
        if icon_set_path.exists():
            import shutil
            shutil.rmtree(icon_set_path)
            self.refresh_available_icons()
        else:
            raise FileNotFoundError(f"Icon set '{icon_set_name}' not found")
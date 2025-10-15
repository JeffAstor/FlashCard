"""
File Manager - Handles file operations and media management
"""

import shutil
import mimetypes
from pathlib import Path
from PIL import Image


class FileManager:
    """Handles file operations and media management"""
    
    def __init__(self):
        self.supported_image_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
        self.supported_audio_formats = ['.wav', '.mp3', '.m4a', '.ogg']
        self.supported_video_formats = ['.mp4', '.avi', '.mov', '.mkv']
        
    def copy_file(self, source, destination):
        """Copy file with error handling"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            raise IOError(f"Failed to copy file: {str(e)}")
            
    def validate_media_file(self, file_path, media_type):
        """Validate media file format"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, "File does not exist"
            
        file_ext = file_path.suffix.lower()
        
        if media_type == "image":
            if file_ext not in self.supported_image_formats:
                return False, f"Unsupported image format: {file_ext}"
        elif media_type == "audio":
            if file_ext not in self.supported_audio_formats:
                return False, f"Unsupported audio format: {file_ext}"
        elif media_type == "video":
            if file_ext not in self.supported_video_formats:
                return False, f"Unsupported video format: {file_ext}"
        else:
            return False, f"Unknown media type: {media_type}"
            
        return True, ""
        
    def validate_image_dimensions(self, image_path, max_width=3840, max_height=2160):
        """Check image size limits (3840x2160)"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
            if width > max_width or height > max_height:
                return False, f"Image dimensions ({width}x{height}) exceed maximum ({max_width}x{max_height})"
                
            return True, ""
        except Exception as e:
            return False, f"Error reading image: {str(e)}"
            
    def get_file_info(self, file_path):
        """Return file metadata"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
            
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "extension": file_path.suffix,
            "mime_type": mime_type,
            "modified": stat.st_mtime
        }
        
    def get_image_info(self, image_path):
        """Return image dimensions and file size"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format
                
            file_info = self.get_file_info(image_path)
            
            return {
                "width": width,
                "height": height,
                "format": format_name,
                "size": file_info["size"] if file_info else 0
            }
        except Exception as e:
            raise ValueError(f"Error reading image info: {str(e)}")
            
    def resize_oversized_image(self, image_path, max_width=3840, max_height=2160, output_path=None):
        """Auto-resize if needed"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                if width <= max_width and height <= max_height:
                    return image_path  # No resize needed
                    
                # Calculate new dimensions maintaining aspect ratio
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # Resize image
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                if output_path is None:
                    output_path = image_path
                    
                resized_img.save(output_path, optimize=True, quality=95)
                
                return output_path
        except Exception as e:
            raise ValueError(f"Error resizing image: {str(e)}")
            
    def resize_image(self, image_path, output_path, size):
        """Resize images to specific size"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGBA if necessary for transparency support
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                    
                resized_img = img.resize(size, Image.Resampling.LANCZOS)
                resized_img.save(output_path, 'PNG', optimize=True)
                
        except Exception as e:
            raise ValueError(f"Error resizing image: {str(e)}")
            
    def generate_thumbnail(self, video_path, output_path, size=(320, 240)):
        """Create video thumbnails"""
        # This is a placeholder - would need video processing library
        # For now, create a simple placeholder image
        try:
            # Create a simple placeholder thumbnail
            img = Image.new('RGB', size, color='lightgray')
            img.save(output_path, 'PNG')
            return output_path
        except Exception as e:
            raise ValueError(f"Error generating thumbnail: {str(e)}")
            
    def get_media_duration(self, file_path):
        """Get audio/video duration"""
        # This is a placeholder - would need media info library
        # For now, return 0 as duration
        return 0
        
    def safe_filename(self, filename):
        """Sanitize filenames for filesystem"""
        import re
        
        # Remove or replace unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = "untitled"
            
        # Limit length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[:255-len(ext)] + ext
            
        return filename
        
    def cleanup_directory(self, directory_path):
        """Clean up empty directories"""
        try:
            directory = Path(directory_path)
            if directory.exists() and directory.is_dir():
                # Remove empty subdirectories
                for subdir in directory.iterdir():
                    if subdir.is_dir() and not any(subdir.iterdir()):
                        subdir.rmdir()
        except Exception:
            pass  # Ignore cleanup errors
            
    def move_file(self, source, destination):
        """Move file with error handling"""
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(source_path, dest_path)
            return True
        except Exception as e:
            raise IOError(f"Failed to move file: {str(e)}")
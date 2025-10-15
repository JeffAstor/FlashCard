"""
Vault Manager - Manages flash card vault operations and file system
"""

import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from models.flashcard import FlashCardSet, FlashCard
from utils.file_manager import FileManager

try:
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
    from PyQt5.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class SetConflictDialog(QDialog):
    """Dialog for handling set name conflicts during import"""
    
    IMPORT = 1
    IGNORE = 2
    IGNORE_ALL = 3
    
    def __init__(self, conflict_set_name, suggested_name="", parent=None):
        super().__init__(parent)
        self.result_action = None
        self.new_name = ""
        
        self.setWindowTitle("Set Name Conflict")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Conflict message
        conflict_label = QLabel(f"A set named '{conflict_set_name}' already exists.")
        conflict_label.setWordWrap(True)
        layout.addWidget(conflict_label)
        
        # New name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("New name:"))
        self.name_input = QLineEdit(suggested_name)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_clicked)
        button_layout.addWidget(self.import_btn)
        
        ignore_btn = QPushButton("Ignore")
        ignore_btn.clicked.connect(self.ignore_clicked)
        button_layout.addWidget(ignore_btn)
        
        ignore_all_btn = QPushButton("Ignore All")
        ignore_all_btn.clicked.connect(self.ignore_all_clicked)
        button_layout.addWidget(ignore_all_btn)
        
        layout.addLayout(button_layout)
        
        # Connect enter key to import
        self.name_input.returnPressed.connect(self.import_clicked)
        
    def import_clicked(self):
        self.new_name = self.name_input.text().strip()
        if not self.new_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a valid set name.")
            return
        self.result_action = self.IMPORT
        self.accept()
        
    def ignore_clicked(self):
        self.result_action = self.IGNORE
        self.accept()
        
    def ignore_all_clicked(self):
        self.result_action = self.IGNORE_ALL
        self.accept()


class VaultManager:
    """Manages flash card vault operations and file system"""
    
    def __init__(self, vault_path, icon_manager=None):
        self.vault_path = Path(vault_path)
        self.sets_path = self.vault_path / "sets"
        self.sets_cache = {}
        self.file_manager = FileManager()
        self.icon_manager = icon_manager
        
        # Ensure vault directory structure exists
        self.setup_vault_structure()
        
    def setup_vault_structure(self):
        """Create vault directory structure if it doesn't exist"""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.sets_path.mkdir(parents=True, exist_ok=True)
        
    def get_available_sets(self):
        """Return list of available set names"""
        try:
            sets = []
            for set_dir in self.sets_path.iterdir():
                if set_dir.is_dir():
                    set_json = set_dir / "set.json"
                    if set_json.exists():
                        sets.append(set_dir.name)
            return sorted(sets)
        except Exception as e:
            raise IOError(f"Error reading vault: {str(e)}")
            
    def get_set_metadata(self, set_name):
        """Load only set metadata"""
        set_path = self.sets_path / set_name
        set_file = set_path / "set.json"
        
        if not set_file.exists():
            raise FileNotFoundError(f"Set '{set_name}' not found")
            
        try:
            with open(set_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return metadata
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid set metadata for '{set_name}': {str(e)}")
            
    def load_set(self, set_name):
        """Load complete set from disk"""
        # Check cache first
        if set_name in self.sets_cache:
            return self.sets_cache[set_name]
            
        set_path = self.sets_path / set_name
        set_file = set_path / "set.json"
        cards_file = set_path / "cards.json"
        
        if not set_file.exists():
            raise FileNotFoundError(f"Set '{set_name}' not found")
            
        try:
            # Load set metadata
            with open(set_file, 'r', encoding='utf-8') as f:
                set_data = json.load(f)
                
            # Load cards data
            cards_data = None
            if cards_file.exists():
                with open(cards_file, 'r', encoding='utf-8') as f:
                    cards_data = json.load(f)
                    
            # Create FlashCardSet object
            flash_set = FlashCardSet.from_dict(set_data, cards_data)
            
            # Update last accessed
            flash_set.update_last_accessed()
            
            # Cache the set
            self.sets_cache[set_name] = flash_set
            
            return flash_set
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid set data for '{set_name}': {str(e)}")
        except Exception as e:
            raise IOError(f"Error loading set '{set_name}': {str(e)}")
            
    def save_set(self, flash_card_set):
        """Save complete set to disk"""
        set_name = flash_card_set.name
        set_path = self.sets_path / set_name
        
        # Create set directory structure
        set_path.mkdir(parents=True, exist_ok=True)
        (set_path / "images").mkdir(exist_ok=True)
        (set_path / "sounds").mkdir(exist_ok=True)
        
        try:
            # Save set metadata
            set_file = set_path / "set.json"
            with open(set_file, 'w', encoding='utf-8') as f:
                json.dump(flash_card_set.to_dict(), f, indent=2, ensure_ascii=False)
                
            # Save cards data
            cards_file = set_path / "cards.json"
            with open(cards_file, 'w', encoding='utf-8') as f:
                json.dump(flash_card_set.cards_to_dict(), f, indent=2, ensure_ascii=False)
                
            # Update cache
            self.sets_cache[set_name] = flash_card_set
            
        except Exception as e:
            raise IOError(f"Error saving set '{set_name}': {str(e)}")
            
    def create_set(self, name, description="", icon_set="default", tags=None, difficulty=1):
        """Create new set directory structure"""
        if self.validate_set_name(name)[0] is False:
            raise ValueError(f"Invalid set name: {name}")
            
        # Create new set
        flash_set = FlashCardSet(name, description)
        flash_set.icon_set = icon_set
        flash_set.tags = tags or []
        flash_set.difficulty_level = difficulty
        
        # Create initial empty card
        flash_set.create_empty_card()
        
        # Save to vault
        self.save_set(flash_set)
        
        return flash_set
        
    def delete_set(self, set_name):
        """Remove set from vault"""
        set_path = self.sets_path / set_name
        
        if not set_path.exists():
            raise FileNotFoundError(f"Set '{set_name}' not found")
            
        try:
            shutil.rmtree(set_path)
            
            # Remove from cache
            if set_name in self.sets_cache:
                del self.sets_cache[set_name]
                
        except Exception as e:
            raise IOError(f"Error deleting set '{set_name}': {str(e)}")
            
    def update_set_metadata(self, set_name, updated_data):
        """Update set metadata with new values"""
        set_path = self.sets_path / set_name
        set_file = set_path / "set.json"
        
        if not set_file.exists():
            raise FileNotFoundError(f"Set '{set_name}' not found")
            
        try:
            # Load current metadata
            with open(set_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            # Update with new values
            current_data.update({
                'name': updated_data['name'],
                'description': updated_data['description'],
                'icon_set': updated_data['icon_set'],
                'tags': updated_data['tags'],
                'difficulty_level': updated_data['difficulty']
            })
            
            # Update modification time
            current_data['last_modified'] = datetime.now().isoformat()
            
            # Save updated metadata
            with open(set_file, 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
                
            # Update cache if exists
            if set_name in self.sets_cache:
                flash_set = self.sets_cache[set_name]
                flash_set.name = updated_data['name']
                flash_set.description = updated_data['description']
                flash_set.icon_set = updated_data['icon_set']
                flash_set.tags = updated_data['tags']
                flash_set.difficulty_level = updated_data['difficulty']
                
        except Exception as e:
            raise IOError(f"Error updating set metadata for '{set_name}': {str(e)}")
            
    def rename_set(self, old_name, new_name):
        """Rename a set by moving its directory and updating metadata"""
        if old_name == new_name:
            return  # No change needed
            
        # Validate new name
        valid, error_msg = self.validate_set_name(new_name)
        if not valid:
            raise ValueError(f"Invalid new name: {error_msg}")
            
        old_path = self.sets_path / old_name
        new_path = self.sets_path / new_name
        
        if not old_path.exists():
            raise FileNotFoundError(f"Set '{old_name}' not found")
            
        if new_path.exists():
            raise ValueError(f"Set '{new_name}' already exists")
            
        try:
            # Move the directory
            shutil.move(str(old_path), str(new_path))
            
            # Update cache
            if old_name in self.sets_cache:
                self.sets_cache[new_name] = self.sets_cache.pop(old_name)
                self.sets_cache[new_name].name = new_name
                
        except Exception as e:
            raise IOError(f"Error renaming set from '{old_name}' to '{new_name}': {str(e)}")
            
    def export_set(self, set_name, export_path):
        """Export set as ZIP file"""
        set_path = self.sets_path / set_name
        
        if not set_path.exists():
            raise FileNotFoundError(f"Set '{set_name}' not found")
            
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Export the set files
                for file_path in set_path.rglob('*'):
                    if file_path.is_file():
                        # Create relative path within the set
                        arcname = file_path.relative_to(set_path)
                        zipf.write(file_path, arcname)
                
                # Export the icon set if icon manager is available
                if self.icon_manager:
                    # Load set metadata to get icon_set
                    set_json_path = set_path / "set.json"
                    if set_json_path.exists():
                        try:
                            with open(set_json_path, 'r', encoding='utf-8') as f:
                                set_data = json.load(f)
                            
                            icon_set_name = set_data.get('icon_set', 'default')
                            icons_path = self.icon_manager.icons_path / icon_set_name
                            
                            # Include icon set files if they exist
                            if icons_path.exists() and icons_path.is_dir():
                                for icon_file in icons_path.rglob('*'):
                                    if icon_file.is_file():
                                        # Create path for icons in the zip: icons/icon_set_name/file
                                        icon_arcname = Path('icons') / icon_set_name / icon_file.relative_to(icons_path)
                                        zipf.write(icon_file, icon_arcname)
                        except (json.JSONDecodeError, KeyError) as e:
                            # If we can't read metadata or get icon_set, continue without icons
                            pass
                        
        except Exception as e:
            raise IOError(f"Error exporting set '{set_name}': {str(e)}")
            
    def import_set(self, zip_path, new_name=None):
        """Import set from ZIP file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                # Extract ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zipf:
                    zipf.extractall(temp_path)
                    
                # Find set.json to get original name
                set_json_files = list(temp_path.rglob('set.json'))
                if not set_json_files:
                    raise ValueError("Invalid set archive: no set.json found")
                    
                set_json_path = set_json_files[0]
                
                # Load set metadata to get original name
                with open(set_json_path, 'r', encoding='utf-8') as f:
                    set_data = json.load(f)
                    
                original_name = set_data.get('name', 'Unknown')
                import_name = new_name if new_name else original_name
                
                # Check for name conflicts
                if import_name in self.get_available_sets():
                    if not new_name:  # Only auto-suggest if no name provided
                        counter = 2
                        while f"{original_name} {counter}" in self.get_available_sets():
                            counter += 1
                        suggested_name = f"{original_name} {counter}"
                        raise ValueError(f"Name conflict: Set '{import_name}' already exists. Suggested name: '{suggested_name}'")
                    else:
                        raise ValueError(f"Set '{import_name}' already exists")
                        
                # Update set name in metadata if changed
                if import_name != original_name:
                    set_data['name'] = import_name
                    with open(set_json_path, 'w', encoding='utf-8') as f:
                        json.dump(set_data, f, indent=2, ensure_ascii=False)
                        
                # Copy extracted files to vault
                set_source = set_json_path.parent
                set_dest = self.sets_path / import_name
                
                if set_dest.exists():
                    shutil.rmtree(set_dest)
                    
                shutil.copytree(set_source, set_dest)
                
                # Import icon sets if available and icon manager exists
                if self.icon_manager:
                    icons_source = temp_path / 'icons'
                    if icons_source.exists() and icons_source.is_dir():
                        # Copy each icon set found in the archive
                        for icon_set_dir in icons_source.iterdir():
                            if icon_set_dir.is_dir():
                                icon_set_name = icon_set_dir.name
                                icon_set_dest = self.icon_manager.icons_path / icon_set_name
                                
                                # Check if icon set already exists
                                if icon_set_dest.exists():
                                    # Only replace if it's not already a valid icon set
                                    if not self.icon_manager.validate_icon_set(icon_set_dest):
                                        shutil.rmtree(icon_set_dest)
                                        shutil.copytree(icon_set_dir, icon_set_dest)
                                else:
                                    # Copy new icon set
                                    shutil.copytree(icon_set_dir, icon_set_dest)
                        
                        # Refresh icon manager's available sets
                        self.icon_manager.refresh_available_icons()
                
                return import_name
                
            except zipfile.BadZipFile:
                raise ValueError("Invalid ZIP file")
            except Exception as e:
                raise IOError(f"Error importing set: {str(e)}")
                
    def export_entire_vault(self, export_path):
        """Export complete vault as ZIP"""
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Export only the sets folder from vault
                sets_path = self.vault_path / "sets"
                if sets_path.exists() and sets_path.is_dir():
                    for file_path in sets_path.rglob('*'):
                        if file_path.is_file():
                            # Create relative path within sets folder
                            arcname = Path('sets') / file_path.relative_to(sets_path)
                            zipf.write(file_path, arcname)
                
                # Export all icon sets if icon manager is available
                if self.icon_manager:
                    icons_path = self.icon_manager.icons_path
                    if icons_path.exists() and icons_path.is_dir():
                        for icon_file in icons_path.rglob('*'):
                            if icon_file.is_file():
                                # Create path for icons in the zip: icons/icon_set_name/file
                                icon_arcname = Path('icons') / icon_file.relative_to(icons_path)
                                zipf.write(icon_file, icon_arcname)
                        
        except Exception as e:
            raise IOError(f"Error exporting vault: {str(e)}")
            
    def import_vault(self, vault_zip_path, merge_mode="merge"):
        """Import vault with conflict resolution"""
        if merge_mode not in ["replace", "merge", "cancel"]:
            raise ValueError("Invalid merge mode. Must be 'replace', 'merge', or 'cancel'")
            
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "vault"
            
            try:
                # Extract vault ZIP
                with zipfile.ZipFile(vault_zip_path, 'r') as zipf:
                    zipf.extractall(temp_path.parent)
                    
                # Handle different extraction structures
                if temp_path.exists():
                    # Standard structure: vault/sets/, vault/icons/ or sets/, icons/
                    imported_sets_path = temp_path / "sets"
                    imported_icons_path = temp_path.parent / "icons"
                else:
                    # Alternative structure: sets/ and icons/ directly in archive
                    imported_sets_path = temp_path.parent / "sets"
                    imported_icons_path = temp_path.parent / "icons"
                    
                if merge_mode == "replace":
                    # Backup current vault
                    backup_path = self.vault_path.parent / f"vault_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    if self.vault_path.exists():
                        shutil.move(str(self.vault_path), str(backup_path))
                    
                    # Replace with imported sets
                    if imported_sets_path.exists():
                        self.sets_path.mkdir(parents=True, exist_ok=True)
                        for set_dir in imported_sets_path.iterdir():
                            if set_dir.is_dir():
                                dest_dir = self.sets_path / set_dir.name
                                if dest_dir.exists():
                                    shutil.rmtree(dest_dir)
                                shutil.copytree(set_dir, dest_dir)
                    
                    # Import icons if available and icon manager exists
                    if self.icon_manager and imported_icons_path.exists():
                        # Replace all icon sets
                        if self.icon_manager.icons_path.exists():
                            shutil.rmtree(self.icon_manager.icons_path)
                        shutil.copytree(imported_icons_path, self.icon_manager.icons_path)
                        # Refresh icon manager's available sets
                        self.icon_manager.refresh_available_icons()
                    
                elif merge_mode == "merge":
                    # Import icons first (always overwrite)
                    if self.icon_manager and imported_icons_path.exists():
                        for icon_set_dir in imported_icons_path.iterdir():
                            if icon_set_dir.is_dir():
                                icon_set_name = icon_set_dir.name
                                icon_set_dest = self.icon_manager.icons_path / icon_set_name
                                
                                # Overwrite existing icon sets
                                if icon_set_dest.exists():
                                    shutil.rmtree(icon_set_dest)
                                shutil.copytree(icon_set_dir, icon_set_dest)
                        
                        # Refresh icon manager's available sets
                        self.icon_manager.refresh_available_icons()
                    
                    # Process sets with conflict resolution
                    if imported_sets_path.exists():
                        existing_sets = set(self.get_available_sets())
                        import_results = {
                            'imported': [],
                            'ignored': [],
                            'renamed': []
                        }
                        
                        ignore_all = False
                        
                        for set_dir in imported_sets_path.iterdir():
                            if not set_dir.is_dir():
                                continue
                                
                            original_name = set_dir.name
                            import_name = original_name
                            
                            # Check for conflict
                            if original_name in existing_sets:
                                if ignore_all:
                                    import_results['ignored'].append(original_name)
                                    continue
                                
                                # Show conflict dialog if PyQt is available
                                if PYQT_AVAILABLE:
                                    # Generate suggested name
                                    counter = 2
                                    suggested_name = f"{original_name} {counter}"
                                    while suggested_name in existing_sets:
                                        counter += 1
                                        suggested_name = f"{original_name} {counter}"
                                    
                                    dialog = SetConflictDialog(original_name, suggested_name)
                                    dialog.exec_()
                                    
                                    if dialog.result_action == SetConflictDialog.IGNORE:
                                        import_results['ignored'].append(original_name)
                                        continue
                                    elif dialog.result_action == SetConflictDialog.IGNORE_ALL:
                                        ignore_all = True
                                        import_results['ignored'].append(original_name)
                                        continue
                                    elif dialog.result_action == SetConflictDialog.IMPORT:
                                        new_name = dialog.new_name
                                        
                                        # Validate new name
                                        valid, error_msg = self.validate_set_name(new_name)
                                        if not valid:
                                            from PyQt5.QtWidgets import QMessageBox
                                            QMessageBox.warning(None, "Invalid Name", error_msg)
                                            import_results['ignored'].append(original_name)
                                            continue
                                        
                                        import_name = new_name
                                        import_results['renamed'].append((original_name, new_name))
                                else:
                                    # Fallback without GUI - auto-rename
                                    counter = 2
                                    import_name = f"{original_name} {counter}"
                                    while import_name in existing_sets:
                                        counter += 1
                                        import_name = f"{original_name} {counter}"
                                    import_results['renamed'].append((original_name, import_name))
                            
                            # Import the set
                            try:
                                dest_dir = self.sets_path / import_name
                                if dest_dir.exists():
                                    shutil.rmtree(dest_dir)
                                shutil.copytree(set_dir, dest_dir)
                                
                                # Update set metadata with new name if renamed
                                if import_name != original_name:
                                    set_json_path = dest_dir / "set.json"
                                    if set_json_path.exists():
                                        try:
                                            with open(set_json_path, 'r', encoding='utf-8') as f:
                                                set_data = json.load(f)
                                            set_data['name'] = import_name
                                            set_data['last_modified'] = datetime.now().isoformat()
                                            with open(set_json_path, 'w', encoding='utf-8') as f:
                                                json.dump(set_data, f, indent=2, ensure_ascii=False)
                                        except (json.JSONDecodeError, KeyError):
                                            pass  # Continue even if metadata update fails
                                
                                existing_sets.add(import_name)
                                import_results['imported'].append(import_name)
                                
                            except Exception as e:
                                import_results['ignored'].append(original_name)
                                # Log error but continue with other sets
                                continue
                        
                        # Return import results for potential user feedback
                        return import_results
                                
                # Clear cache to force reload
                self.sets_cache.clear()
                
            except zipfile.BadZipFile:
                raise ValueError("Invalid vault ZIP file")
            except Exception as e:
                raise IOError(f"Error importing vault: {str(e)}")
        
        return None
                
    def validate_set_name(self, name):
        """Check name uniqueness and validity"""
        if not name or len(name.strip()) == 0:
            return False, "Set name cannot be empty"
            
        if len(name) > 128:
            return False, "Set name cannot exceed 128 characters"
            
        # Check for invalid filesystem characters
        invalid_chars = '<>:"/\\|?*'
        if any(char in name for char in invalid_chars):
            return False, f"Set name contains invalid characters: {invalid_chars}"
            
        # Check for uniqueness
        if name in self.get_available_sets():
            return False, "Set name already exists"
            
        return True, ""
        
    def get_vault_statistics(self):
        """Return vault-wide statistics"""
        try:
            sets = self.get_available_sets()
            total_sets = len(sets)
            total_cards = 0
            
            for set_name in sets:
                try:
                    metadata = self.get_set_metadata(set_name)
                    total_cards += metadata.get('card_count', 0)
                except Exception:
                    continue  # Skip corrupted sets
                    
            return {
                "total_sets": total_sets,
                "total_cards": total_cards,
                "vault_path": str(self.vault_path)
            }
        except Exception as e:
            return {
                "total_sets": 0,
                "total_cards": 0,
                "vault_path": str(self.vault_path),
                "error": str(e)
            }
            
    def validate_vault_integrity(self):
        """Check vault consistency"""
        issues = []
        
        try:
            sets = self.get_available_sets()
            
            for set_name in sets:
                set_path = self.sets_path / set_name
                
                # Check required files
                if not (set_path / "set.json").exists():
                    issues.append(f"Set '{set_name}': Missing set.json")
                    
                if not (set_path / "cards.json").exists():
                    issues.append(f"Set '{set_name}': Missing cards.json")
                    
                # Check JSON validity
                try:
                    self.get_set_metadata(set_name)
                except Exception as e:
                    issues.append(f"Set '{set_name}': Invalid metadata - {str(e)}")
                    
                # Check media directories
                images_dir = set_path / "images"
                sounds_dir = set_path / "sounds"
                
                if not images_dir.exists():
                    issues.append(f"Set '{set_name}': Missing images directory")
                if not sounds_dir.exists():
                    issues.append(f"Set '{set_name}': Missing sounds directory")
                    
        except Exception as e:
            issues.append(f"Vault integrity check failed: {str(e)}")
            
        return len(issues) == 0, issues
        
    def copy_media_file(self, source_path, set_name, media_type):
        """Copy media to set directory"""
        ## DEBUG START
        print(f"DEBUG: copy_media_file called with:")
        print(f"  source_path: {source_path}")
        print(f"  set_name: {set_name}")
        print(f"  media_type: {media_type}")
        print(f"  sets_path: {self.sets_path}")
        ## DEBUG END
        
        if media_type not in ["image", "audio", "video"]:
            raise ValueError(f"Invalid media type: {media_type}")
            
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
            
        # Determine destination directory
        set_path = self.sets_path / set_name
        if media_type == "image":
            dest_dir = set_path / "images"
        else:  # audio or video
            dest_dir = set_path / "sounds"
            
        ## DEBUG START
        print(f"DEBUG: Destination directory: {dest_dir}")
        ## DEBUG END
        
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        ## DEBUG START
        print(f"DEBUG: Directory created successfully: {dest_dir.exists()}")
        ## DEBUG END
        
        # Generate safe filename
        safe_name = self.file_manager.safe_filename(source.name)
        dest_path = dest_dir / safe_name
        
        ## DEBUG START
        print(f"DEBUG: Initial destination path: {dest_path}")
        ## DEBUG END
        
        # Handle name conflicts
        counter = 1
        while dest_path.exists():
            stem = Path(safe_name).stem
            suffix = Path(safe_name).suffix
            dest_path = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
            
        ## DEBUG START
        print(f"DEBUG: Final destination path: {dest_path}")
        ## DEBUG END
        
        # Copy file
        self.file_manager.copy_file(source, dest_path)
        
        ## DEBUG START
        print(f"DEBUG: File copy completed. File exists: {dest_path.exists()}")
        print(f"DEBUG: Returning filename: {dest_path.name}")
        ## DEBUG END
        
        return dest_path.name  # Return relative filename
        
    def cleanup_unused_media(self, set_name):
        """Remove unreferenced media files"""
        try:
            flash_set = self.load_set(set_name)
            set_path = self.sets_path / set_name
            
            # Collect all referenced media files
            referenced_files = set()
            
            for card in flash_set.cards:
                for side in ["information", "answer"]:
                    for block in card.get_side_blocks(side):
                        if hasattr(block, 'image_path') and block.image_path:
                            referenced_files.add(block.image_path)
                        elif hasattr(block, 'audio_path') and block.audio_path:
                            referenced_files.add(block.audio_path)
                        elif hasattr(block, 'video_path') and block.video_path:
                            referenced_files.add(block.video_path)
                            
            # Check media directories for unreferenced files
            removed_files = []
            
            for media_dir in ["images", "sounds"]:
                media_path = set_path / media_dir
                if media_path.exists():
                    for file_path in media_path.iterdir():
                        if file_path.is_file() and file_path.name not in referenced_files:
                            file_path.unlink()
                            removed_files.append(str(file_path))
                            
            return removed_files
            
        except Exception as e:
            raise IOError(f"Error cleaning up media for '{set_name}': {str(e)}")
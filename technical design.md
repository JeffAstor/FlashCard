# Technical Design Document
## FlashCard Application with PyQt5

### Application Architecture Overview

The application follows a Model-View-Controller (MVC) architecture with three distinct operational modes:
- **Vault Mode**: Main interface for set management
- **Edit Mode**: Card creation and editing interface  
- **View Mode**: Study/learning interface

### Core Application Classes

#### 1. Main Application Controller
```python
class FlashCardApplication(QApplication):
```
**Purpose**: Main application controller managing mode transitions and global state
**Methods**:
- `__init__()`: Initialize application, load config, create directories
- `switch_to_vault_mode()`: Transition to vault interface
- `switch_to_edit_mode(set_name)`: Transition to edit interface
- `switch_to_view_mode(set_name)`: Transition to study interface
- `load_config()`: Load application configuration
- `save_config()`: Save application configuration
- `setup_directories()`: Create required directory structure
- `get_vault_path()`: Return path to vault directory
- `show_error_dialog(message)`: Display error to user
- `log_error(error, context)`: Log error to error system

#### 2. Main Window Container
```python
class MainWindow(QMainWindow):
```
**Purpose**: Primary window container that hosts different mode interfaces
**Methods**:
- `__init__(app_controller)`: Initialize main window
- `set_mode_widget(widget)`: Replace current interface with new mode widget
- `setup_menu_bar()`: Create application menu bar
- `setup_status_bar()`: Create status bar with loading indicators
- `show_loading(message)`: Display loading indicator
- `hide_loading()`: Hide loading indicator
- `update_status(message)`: Update status text
- `closeEvent(event)`: Handle application shutdown

### Data Model Classes

#### 3. Flash Card Data Model
```python
class FlashCard:
```
**Purpose**: Represents a single flash card with two sides
**Attributes**:
- `card_id`: Unique identifier
- `information_side`: List of content blocks
- `answer_side`: List of content blocks
- `status`: Card status (Known/Review/Unknown)
- `created_date`: Card creation timestamp
- `last_studied`: Last study timestamp
**Methods**:
- `__init__(card_id)`: Initialize empty card
- `add_block_to_side(side, block)`: Add content block to specified side
- `remove_block_from_side(side, block_index)`: Remove block from side
- `move_block(side, from_index, to_index)`: Reorder blocks within side
- `get_side_blocks(side)`: Return blocks for specified side
- `set_status(status)`: Update card study status
- `to_dict()`: Serialize card to dictionary
- `from_dict(data)`: Deserialize card from dictionary

#### 4. Content Block Base Class
```python
class ContentBlock:
```
**Purpose**: Base class for all content block types
**Attributes**:
- `block_id`: Unique block identifier
- `block_type`: Type of content block
- `created_date`: Block creation timestamp
**Methods**:
- `__init__(block_type)`: Initialize base block
- `to_dict()`: Serialize block to dictionary
- `from_dict(data)`: Create block from dictionary
- `validate()`: Validate block content
- `get_display_widget()`: Return widget for display (abstract)
- `get_edit_widget()`: Return widget for editing (abstract)

#### 5. Text Content Block
```python
class TextBlock(ContentBlock):
```
**Purpose**: Text content with rich formatting
**Attributes**:
- `text_content`: Rich text content (HTML format)
- `font_size`: Text size setting
- `alignment`: Text alignment (left/center/right)
- `max_chars`: Maximum character limit (1024)
**Methods**:
- `__init__()`: Initialize text block
- `set_text(content)`: Update text content with validation
- `set_formatting(font_size, alignment)`: Update text formatting
- `get_plain_text()`: Return plain text without formatting
- `get_display_widget()`: Return QLabel for display
- `get_edit_widget()`: Return QTextEdit for editing

#### 6. Image Content Block
```python
class ImageBlock(ContentBlock):
```
**Purpose**: Image content block with size validation
**Attributes**:
- `image_path`: Relative path to image file
- `original_filename`: Original image filename
- `width`: Display width
- `height`: Display height
- `max_width`: Maximum allowed width (3840)
- `max_height`: Maximum allowed height (2160)
**Methods**:
- `__init__()`: Initialize image block
- `set_image(file_path)`: Set image file with dimension validation
- `validate_image_size()`: Check image dimensions against limits
- `resize_if_needed()`: Auto-resize oversized images
- `get_full_path(vault_path)`: Return full path to image
- `get_display_widget()`: Return QLabel with scaled image
- `get_edit_widget()`: Return image selection interface

#### 7. Audio Content Block
```python
class AudioBlock(ContentBlock):
```
**Purpose**: Audio file content block
**Attributes**:
- `audio_path`: Relative path to audio file
- `original_filename`: Original audio filename
- `duration`: Audio duration in seconds
**Methods**:
- `__init__()`: Initialize audio block
- `set_audio(file_path)`: Set audio file with validation
- `get_full_path(vault_path)`: Return full path to audio
- `get_display_widget()`: Return audio player widget
- `get_edit_widget()`: Return audio selection interface

#### 8. Video Content Block
```python
class VideoBlock(ContentBlock):
```
**Purpose**: Video file content block (max 5 minutes)
**Attributes**:
- `video_path`: Relative path to video file
- `original_filename`: Original video filename
- `duration`: Video duration in seconds
- `thumbnail_path`: Path to generated thumbnail
**Methods**:
- `__init__()`: Initialize video block
- `set_video(file_path)`: Set video file with validation
- `generate_thumbnail()`: Create video thumbnail
- `get_full_path(vault_path)`: Return full path to video
- `get_display_widget()`: Return video player widget
- `get_edit_widget()`: Return video selection interface

#### 9. Flash Card Set Model
```python
class FlashCardSet:
```
**Purpose**: Container for a collection of flash cards with metadata
**Attributes**:
- `name`: Set name (unique identifier)
- `description`: Set description
- `icon_set`: Icon set name
- `tags`: List of user-defined tags
- `difficulty_level`: Difficulty rating
- `created_date`: Set creation date
- `last_accessed`: Last access timestamp
- `cards`: List of FlashCard objects
- `card_count`: Number of cards in set
**Methods**:
- `__init__(name, description)`: Initialize new set
- `add_card(card)`: Add card to set
- `remove_card(card_id)`: Remove card from set
- `get_card(card_id)`: Retrieve specific card
- `get_card_by_index(index)`: Get card by position
- `move_card(from_index, to_index)`: Reorder cards
- `get_cards_by_status(status)`: Filter cards by study status
- `update_metadata(description, tags, difficulty)`: Update set metadata
- `to_dict()`: Serialize set to dictionary
- `from_dict(data)`: Deserialize set from dictionary

### Vault Management Classes

#### 10. Vault Manager
```python
class VaultManager:
```
**Purpose**: Manages flash card vault operations and file system
**Attributes**:
- `vault_path`: Path to vault directory
- `sets_cache`: Cache of loaded sets
**Methods**:
- `__init__(vault_path)`: Initialize vault manager
- `get_available_sets()`: Return list of available set names
- `load_set(set_name)`: Load complete set from disk
- `save_set(flash_card_set)`: Save complete set to disk
- `create_set(name, description, icon_set)`: Create new set directory structure
- `delete_set(set_name)`: Remove set from vault
- `export_set(set_name, export_path)`: Export set as ZIP file
- `import_set(zip_path, new_name=None)`: Import set from ZIP file
- `export_entire_vault(export_path)`: Export complete vault as ZIP
- `import_vault(vault_zip_path, merge_mode)`: Import vault with conflict resolution
- `validate_set_name(name)`: Check name uniqueness and validity
- `get_set_metadata(set_name)`: Load only set metadata
- `get_vault_statistics()`: Return vault-wide statistics
- `validate_vault_integrity()`: Check vault consistency
- `copy_media_file(source_path, set_name, media_type)`: Copy media to set directory
- `cleanup_unused_media(set_name)`: Remove unreferenced media files

#### 11. Icon Manager
```python
class IconManager:
```
**Purpose**: Manages application icon sets and custom icons
**Attributes**:
- `icons_path`: Path to icons directory
- `available_icon_sets`: List of valid icon sets
- `default_icons`: Built-in educational icon collection
**Methods**:
- `__init__(icons_path)`: Initialize icon manager
- `get_available_icon_sets()`: Return list of valid icon sets
- `get_icon(icon_set, size)`: Return QIcon for specified set and size
- `validate_icon_set(icon_set_path)`: Check if icon set is complete
- `install_custom_icon(image_path, icon_set_name)`: Create custom icon set
- `resize_and_save_icon(source_path, icon_set_path)`: Generate all icon sizes
- `get_default_icon(size)`: Return default application icon
- `install_default_icon_collection()`: Install built-in educational icons
- `get_icon_categories()`: Return available icon categories

### User Interface Classes - Vault Mode

#### 12. Vault Mode Interface
```python
class VaultModeWidget(QWidget):
```
**Purpose**: Main vault interface for set management
**Attributes**:
- `app_controller`: Reference to main application controller
- `vault_manager`: Vault management instance
- `set_list_widget`: Widget displaying available sets
- `selected_set`: Currently selected set name
- `menu_bar`: Vault-specific menu bar widget
**Methods**:
- `__init__(app_controller, vault_manager)`: Initialize vault interface
- `setup_ui()`: Create interface layout and widgets
- `setup_vault_menu_bar()`: Create vault-specific menu buttons
- `setup_set_list()`: Create set display area
- `refresh_set_list()`: Reload and display available sets
- `on_set_selected(set_name)`: Handle set selection
- `on_new_set_clicked()`: Handle new set creation
- `on_load_set_clicked()`: Handle load set for study
- `on_edit_set_clicked()`: Handle edit set
- `on_export_set_clicked()`: Handle set export
- `on_export_vault_clicked()`: Handle entire vault export
- `on_import_vault_clicked()`: Handle vault import with merge options
- `show_set_creation_dialog()`: Display new set creation dialog
- `show_import_dialog()`: Display set import dialog
- `show_vault_import_dialog()`: Display vault import dialog with merge options
- `update_set_display()`: Refresh set list display

#### 13. Set List Display Widget
```python
class SetListWidget(QWidget):
```
**Purpose**: Custom widget for displaying flash card sets
**Attributes**:
- `sets_data`: List of set metadata
- `display_mode`: Grid or list view mode
- `selected_set`: Currently selected set
**Methods**:
- `__init__()`: Initialize set list widget
- `set_sets_data(sets_data)`: Update displayed sets
- `set_display_mode(mode)`: Switch between grid/list view
- `select_set(set_name)`: Programmatically select set
- `get_selected_set()`: Return currently selected set
- `paintEvent(event)`: Custom painting for set display
- `mousePressEvent(event)`: Handle set selection clicks
- `keyPressEvent(event)`: Handle keyboard navigation

#### 14. Set Creation Dialog
```python
class SetCreationDialog(QDialog):
```
**Purpose**: Dialog for creating new flash card sets
**Attributes**:
- `name_input`: Set name text field
- `description_input`: Set description text area
- `icon_selector`: Icon selection widget
- `tags_input`: Tags input field
- `difficulty_selector`: Difficulty level selector
**Methods**:
- `__init__(icon_manager, vault_manager)`: Initialize creation dialog
- `setup_ui()`: Create dialog layout and widgets
- `setup_icon_selector()`: Create icon selection interface
- `validate_input()`: Validate user input
- `get_set_data()`: Return entered set data
- `on_name_changed()`: Handle name field changes
- `on_icon_selected(icon_set)`: Handle icon selection
- `accept()`: Validate and accept dialog

### User Interface Classes - Edit Mode

#### 15. Edit Mode Interface
```python
class EditModeWidget(QWidget):
```
**Purpose**: Interface for editing flash card sets and individual cards
**Attributes**:
- `app_controller`: Reference to main application controller
- `vault_manager`: Vault management instance
- `current_set`: Currently loaded FlashCardSet
- `current_card_index`: Index of currently displayed card
- `current_side`: Currently displayed side (info/answer)
- `menu_bar`: Edit-specific menu bar widget
**Methods**:
- `__init__(app_controller, vault_manager)`: Initialize edit interface
- `setup_ui()`: Create interface layout and widgets
- `load_set(set_name)`: Load set for editing
- `setup_edit_menu_bar()`: Create edit-specific menu bar with navigation and controls
- `setup_side_selection()`: Create side selection tabs/buttons
- `setup_block_editor()`: Create block editing interface
- `display_current_card()`: Show current card content
- `on_previous_card_clicked()`: Navigate to previous card
- `on_next_card_clicked()`: Navigate to next card
- `on_new_card_clicked()`: Create new blank card
- `on_card_selector_changed(index)`: Handle dropdown card selection
- `on_flip_side_clicked()`: Switch between information and answer sides
- `on_save_changes_clicked()`: Save changes to vault
- `on_return_to_vault_clicked()`: Return to vault mode
- `auto_save()`: Automatically save changes

#### 16. Block Editor Widget
```python
class BlockEditorWidget(QWidget):
```
**Purpose**: Interface for managing content blocks on card sides
**Attributes**:
- `current_blocks`: List of blocks for current side
- `block_creation_dropdown`: Block type selector
- `block_list_widget`: Scrollable list of blocks
- `max_blocks`: Maximum blocks per side (10)
**Methods**:
- `__init__()`: Initialize block editor
- `setup_ui()`: Create editor layout
- `set_blocks(blocks)`: Display blocks for editing
- `setup_block_creation()`: Create block creation controls
- `setup_block_list()`: Create scrollable block list
- `on_create_block_clicked(block_type)`: Handle new block creation
- `on_block_edited(block_index, content)`: Handle block content changes
- `on_block_moved(from_index, to_index)`: Handle block reordering
- `on_block_deleted(block_index)`: Handle block deletion
- `validate_block_count()`: Check block limit
- `get_blocks()`: Return current block list

#### 17. Block Edit Item Widget
```python
class BlockEditItemWidget(QWidget):
```
**Purpose**: Individual block editing widget with controls
**Attributes**:
- `block`: Associated ContentBlock object
- `content_widget`: Block-specific edit widget
- `move_up_button`: Up arrow button
- `move_down_button`: Down arrow button
- `delete_button`: Delete button
**Methods**:
- `__init__(block, block_index)`: Initialize block item widget
- `setup_ui()`: Create item layout with controls
- `setup_content_widget()`: Create block-specific editor
- `on_move_up_clicked()`: Signal block move up
- `on_move_down_clicked()`: Signal block move down
- `on_delete_clicked()`: Signal block deletion
- `on_content_changed()`: Signal content modification
- `update_move_buttons(can_move_up, can_move_down)`: Update button states

### User Interface Classes - View Mode

#### 18. View Mode Interface
```python
class ViewModeWidget(QWidget):
```
**Purpose**: Study interface for flash card learning
**Attributes**:
- `app_controller`: Reference to main application controller
- `vault_manager`: Vault management instance
- `current_set`: Currently loaded FlashCardSet
- `current_card_index`: Index of currently displayed card
- `current_side`: Currently displayed side
- `study_mode`: Study mode (sequential/random/review)
- `session_stats`: Study session statistics
- `menu_bar`: View-specific menu bar widget
**Methods**:
- `__init__(app_controller, vault_manager)`: Initialize view interface
- `setup_ui()`: Create study interface layout
- `load_set(set_name)`: Load set for studying
- `setup_view_menu_bar()`: Create view-specific menu bar with navigation and study controls
- `setup_card_display()`: Create card display area
- `setup_progress_tracking()`: Create progress indicators
- `display_current_card()`: Show current card content
- `on_previous_clicked()`: Navigate to previous card
- `on_next_clicked()`: Navigate to next card
- `on_random_clicked()`: Jump to random card
- `on_flip_card_clicked()`: Switch between card sides
- `on_mark_known_clicked()`: Mark card as Known
- `on_mark_review_clicked()`: Mark card as Need Review
- `on_mark_unknown_clicked()`: Mark card as Unknown
- `on_study_mode_changed(mode)`: Switch study mode
- `on_session_stats_clicked()`: Display session statistics
- `on_return_to_vault_clicked()`: Return to vault mode
- `update_progress()`: Update progress indicators

#### 19. Card Display Widget
```python
class CardDisplayWidget(QWidget):
```
**Purpose**: Widget for displaying card content during study
**Attributes**:
- `current_blocks`: List of content blocks to display
- `display_widgets`: List of block display widgets
- `flip_animation`: Animation for card flipping
**Methods**:
- `__init__()`: Initialize card display widget
- `set_blocks(blocks)`: Set blocks for display
- `setup_block_display()`: Create block display widgets
- `animate_flip()`: Animate card flip transition
- `mousePressEvent(event)`: Handle click to flip
- `paintEvent(event)`: Custom painting for card appearance

#### 20. Study Session Manager
```python
class StudySessionManager:
```
**Purpose**: Manages study session state and basic statistics
**Attributes**:
- `session_start_time`: Session start timestamp
- `cards_studied`: Number of cards reviewed
- `cards_known`: Count of cards marked as known
- `cards_review`: Count of cards marked for review
- `cards_unknown`: Count of cards marked as unknown
- `study_mode`: Current study mode
- `total_session_time`: Total time spent studying
**Methods**:
- `__init__(card_set, study_mode)`: Initialize session
- `start_session()`: Begin study session
- `end_session()`: Complete study session
- `record_card_study(card_id, status)`: Record card interaction
- `get_session_duration()`: Return session time
- `get_progress_percentage()`: Return completion percentage
- `get_basic_statistics()`: Return simple session stats
- `get_cards_by_status_count()`: Return status breakdown counts
- `save_session_data()`: Persist session results

### Utility and Helper Classes

#### 21. File Manager
```python
class FileManager:
```
**Purpose**: Handles file operations and media management
**Methods**:
- `copy_file(source, destination)`: Copy file with error handling
- `validate_media_file(file_path, media_type)`: Validate media file format
- `validate_image_dimensions(image_path)`: Check image size limits (3840x2160)
- `get_file_info(file_path)`: Return file metadata
- `get_image_info(image_path)`: Return image dimensions and file size
- `resize_oversized_image(image_path, max_width, max_height)`: Auto-resize if needed
- `generate_thumbnail(video_path, output_path)`: Create video thumbnails
- `resize_image(image_path, output_path, size)`: Resize images
- `get_media_duration(file_path)`: Get audio/video duration
- `safe_filename(filename)`: Sanitize filenames for filesystem

#### 22. Error Logger
```python
class ErrorLogger:
```
**Purpose**: Centralized error logging and management
**Attributes**:
- `log_file_path`: Path to error log file
- `error_history`: In-memory error history
**Methods**:
- `__init__(log_file_path)`: Initialize error logger
- `log_error(error, context, severity)`: Log error with context
- `get_error_history()`: Return recent errors
- `clear_log()`: Clear error log
- `show_error_dialog(parent, error_list)`: Display error dialog

#### 23. Configuration Manager
```python
class ConfigManager:
```
**Purpose**: Application configuration management
**Attributes**:
- `config_file_path`: Path to configuration file
- `config_data`: Current configuration dictionary
**Methods**:
- `__init__(config_file_path)`: Initialize config manager
- `load_config()`: Load configuration from file
- `save_config()`: Save configuration to file
- `get_setting(key, default)`: Get configuration value
- `set_setting(key, value)`: Update configuration value
- `reset_to_defaults()`: Reset configuration to defaults

### Media Handler Classes

#### 24. Media Player Widget
```python
class MediaPlayerWidget(QWidget):
```
**Purpose**: Custom media player for audio/video content
**Attributes**:
- `media_player`: QMediaPlayer instance
- `media_content`: QMediaContent instance
- `play_button`: Play/pause button
- `position_slider`: Position slider
- `volume_slider`: Volume control
**Methods**:
- `__init__()`: Initialize media player widget
- `setup_ui()`: Create player interface
- `load_media(file_path)`: Load media file
- `play()`: Start playback
- `pause()`: Pause playback
- `stop()`: Stop playback
- `set_position(position)`: Set playback position
- `set_volume(volume)`: Set playback volume
- `on_position_changed(position)`: Handle position updates
- `on_duration_changed(duration)`: Handle duration updates

#### 26. Mode-Specific Menu Bar Classes

##### Vault Menu Bar Widget
```python
class VaultMenuBar(QWidget):
```
**Purpose**: Menu bar for vault mode operations
**Attributes**:
- `parent_widget`: Reference to vault mode widget
**Methods**:
- `__init__(parent_widget)`: Initialize vault menu bar
- `setup_ui()`: Create menu bar layout and buttons
- `update_button_states(has_selection)`: Enable/disable buttons based on selection

##### Edit Menu Bar Widget
```python
class EditMenuBar(QWidget):
```
**Purpose**: Menu bar for edit mode operations
**Attributes**:
- `parent_widget`: Reference to edit mode widget
- `card_selector`: Dropdown for card navigation
**Methods**:
- `__init__(parent_widget)`: Initialize edit menu bar
- `setup_ui()`: Create menu bar layout and buttons
- `update_navigation_buttons(card_index, total_cards)`: Update button states
- `update_card_selector(cards)`: Populate card selector dropdown
- `update_side_indicator(current_side)`: Show current side

##### View Menu Bar Widget
```python
class ViewMenuBar(QWidget):
```
**Purpose**: Menu bar for view mode operations
**Attributes**:
- `parent_widget`: Reference to view mode widget
- `study_mode_selector`: Dropdown for study mode selection
- `stats_display`: Session statistics display
**Methods**:
- `__init__(parent_widget)`: Initialize view menu bar
- `setup_ui()`: Create menu bar layout and buttons
- `update_navigation_buttons(card_index, total_cards)`: Update button states
- `update_status_buttons(current_card_status)`: Highlight current card status
- `update_study_mode_selector(current_mode)`: Update mode selector
- `update_stats_display(session_stats)`: Refresh statistics display

### Integration and Communication

#### 27. Signal Manager
```python
class SignalManager(QObject):
```
**Purpose**: Centralized signal management for component communication
**Signals**:
- `mode_change_requested(mode, data)`
- `set_modified(set_name)`
- `card_status_changed(card_id, status)`
- `error_occurred(error_message, context)`
- `operation_completed(operation_name, success)`
**Methods**:
- `__init__()`: Initialize signal manager
- `connect_signals()`: Connect all application signals
- `emit_mode_change(mode, data)`: Request mode change
- `emit_set_modified(set_name)`: Signal set modification
- `emit_card_status_change(card_id, status)`: Signal card status update

### Application Flow and State Management

#### Key Application Flows:

1. **Application Startup**:
   - Initialize FlashCardApplication
   - Load configuration
   - Create directory structure
   - Initialize vault manager
   - Display vault mode interface

2. **New Set Creation**:
   - Display set creation dialog
   - Validate input
   - Create set directory structure
   - Create initial blank card
   - Switch to edit mode

3. **Set Editing**:
   - Load set from vault
   - Switch to edit mode interface
   - Enable card navigation and block editing
   - Auto-save changes
   - Return to vault mode on exit

4. **Study Session**:
   - Load set from vault
   - Switch to view mode interface
   - Initialize session manager
   - Enable card navigation and status marking
   - Track progress and statistics
   - Save session results

5. **Import/Export**:
   - Export: ZIP set directory with all media
   - Import: Extract ZIP, validate, handle name conflicts

### Data Persistence

#### File Structure and Formats:

1. **Set Metadata (set.json)**:
```json
{
    "name": "string",
    "description": "string", 
    "icon_set": "string",
    "tags": ["string"],
    "difficulty_level": "integer",
    "created_date": "ISO timestamp",
    "last_accessed": "ISO timestamp",
    "card_count": "integer"
}
```

2. **Card Data (cards.json)**:
```json
{
    "cards": [
        {
            "card_id": "string",
            "information_side": [
                {
                    "block_type": "text|image|audio|video",
                    "block_id": "string",
                    "content": "varies by type",
                    "created_date": "ISO timestamp"
                }
            ],
            "answer_side": [...],
            "status": "Known|Review|Unknown",
            "created_date": "ISO timestamp",
            "last_studied": "ISO timestamp"
        }
    ]
}
```

### Default Icon Collection

The application includes a comprehensive default icon set covering common educational and study categories. This collection will be embedded with the application and automatically installed on first run.

**Default Icon Categories:**
- **Academic Subjects**: Math, Science, Language Arts, History, Geography, Art, Music
- **Study Types**: Vocabulary, Concepts, Formulas, Facts, Review, Practice
- **Difficulty Levels**: Beginner, Intermediate, Advanced
- **General Categories**: Study, Quiz, Test, Learning, Education, Books
- **Content Types**: Text, Images, Audio, Video, Mixed Media

**Icon Specifications:**
- All icons provided in 5 standard sizes: 256x256, 128x128, 64x64, 32x32, 16x16 pixels
- PNG format with transparency support
- Consistent visual style across the collection
- High contrast and clear visibility at all sizes
- Colorful but professional appearance suitable for educational use

**Icon Installation:**
- Default icons are installed automatically during application first run
- Located in `./icons/default/` and individual category folders
- Users can add additional custom icon sets following the same structure
- Icon Manager validates and manages both default and custom icon collections

1. **Default Icon Set**: Application includes a comprehensive default icon collection with common educational and category icons (math, science, language, history, etc.)

2. **Image Size Limits**: Maximum image dimensions of 3840 x 2160 pixels with automatic scaling and validation

3. **Progress Tracking**: Basic session statistics and card status tracking without complex algorithms

4. **Vault Management**: Full vault export/import functionality for backing up and sharing entire collections

5. **Accessibility**: Standard PyQt5 accessibility with no additional specialized features

### Additional Technical Requirements:

#### Default Icon Collection:
The application will include a default icon set covering common educational categories:
- Academic subjects (math, science, language, history, geography)
- General categories (study, practice, review, quiz)
- Difficulty levels (beginner, intermediate, advanced)
- Content types (vocabulary, concepts, formulas, facts)

#### Enhanced Vault Manager Methods:
```python
class VaultManager:
    # Additional methods for vault-wide operations
    def export_entire_vault(self, export_path): # Export complete vault as ZIP
    def import_vault(self, vault_zip_path, merge_mode): # Import vault with conflict resolution
    def get_vault_statistics(): # Return vault-wide statistics
    def validate_vault_integrity(): # Check vault consistency
```

#### Image Validation Updates:
```python
class FileManager:
    def validate_image_dimensions(self, image_path): # Check 3840x2160 limit
    def get_image_info(self, image_path): # Return dimensions and file size
    def resize_oversized_image(self, image_path, max_width, max_height): # Auto-resize if needed
```

This technical design provides a comprehensive foundation for implementing the flashcard application with clear separation of concerns, proper data management, and extensible architecture.

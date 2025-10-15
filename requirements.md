# Requirements

I require a python script for a flash card application.  The app will use PyQt5 for the user interface.

I need the application to support the loading, saving and editing of flash card sets.

The flash cards will have a name and an icon (PNG file).

## Application Modes

The flash card application operates in three distinct modes, each with its own dedicated interface and functionality. The application switches between these modes based on user actions, with each mode completely replacing the previous interface.

### Mode Overview

#### 1. Vault Mode (Primary Interface)
- **Purpose**: Main hub for flash card set management and organization
- **When Active**: Application startup, returning from other modes
- **Primary Functions**: Browse sets, create new sets, import/export, select sets for study or editing
- **Navigation**: Entry point to other modes via menu buttons

#### 2. Edit Mode (Content Creation)
- **Purpose**: Creating and modifying flash card sets and individual cards
- **When Active**: When user selects "Edit selected" or creates a new set
- **Primary Functions**: Add/remove cards, manage content blocks, edit card content, organize card order
- **Navigation**: Accessed from Vault mode, returns to Vault mode when complete

#### 3. View Mode (Study Interface)
- **Purpose**: Studying flash cards with progress tracking and learning features
- **When Active**: When user selects "Load selected" to study a set
- **Primary Functions**: Card navigation, flip interactions, progress tracking, study session management
- **Navigation**: Accessed from Vault mode, returns to Vault mode when session ends

### Mode Transitions

**From Vault Mode:**
- → Edit Mode: Click "Edit selected" or "New card set" (after creation dialog)
- → View Mode: Click "Load selected"

**From Edit Mode:**
- → Vault Mode: Click "Exit" or "Return to Vault" button

**From View Mode:**
- → Vault Mode: Click "Return to Vault" or complete study session

### Interface Replacement Strategy
- Each mode completely replaces the current interface (no overlays or tabs)
- Clean transitions between modes provide focused, distraction-free experiences
- Consistent navigation patterns across all modes
- Status bar and error handling remain consistent across all modes

### Mode-Specific Features and Menu Bars

Each mode has its own dedicated menu bar with mode-appropriate functionality:

**Vault Mode Only:**
- Set library browsing and organization
- Import/export functionality
- Set creation dialogs
- Vault-wide search and filtering

**Vault Mode Menu Bar:**
- **New card set**: Creates a new flash card set with creation dialog
- **Load selected**: Opens selected set in view mode for studying
- **Export selected**: Exports selected set as ZIP file for sharing
- **Edit selected**: Opens selected set in edit mode for modification
- **Export vault**: Exports entire vault as ZIP file for backup and sharing
- **Import vault**: Imports vault ZIP file with merge options for restoration or sharing

**Edit Mode Only:**
- Content block management
- Rich text editing
- Media file integration
- Card reordering and organization

**Edit Mode Menu Bar:**
- **Previous Card**: Navigate to previous card in set
- **Next Card**: Navigate to next card in set
- **New Card**: Create new blank card and switch to it for editing
- **Card Selector**: Dropdown menu for jumping to specific cards by index
- **Flip/Switch Side**: Toggle between information and answer sides
- **Save Changes**: Save current modifications to vault
- **Return to Vault**: Exit edit mode and return to vault interface

**View Mode Only:**
- Study session management
- Progress tracking and analytics
- Card status marking (Known/Review/Unknown)
- Study mode selection (Sequential/Random/Review)

**View Mode Menu Bar:**
- **Previous**: Navigate to previous card in study sequence
- **Next**: Navigate to next card in study sequence
- **Random**: Jump to random card in set
- **Flip Card**: Toggle between information and answer sides
- **Mark Known**: Mark current card as "Known" (K shortcut)
- **Mark Review**: Mark current card as "Need Review" (R shortcut)
- **Mark Unknown**: Mark current card as "Unknown" (U shortcut)
- **Study Mode**: Dropdown to switch between Sequential/Random/Review modes
- **Session Stats**: Display current session statistics
- **Return to Vault**: End study session and return to vault interface

## Flash cards
Flash cards have two sides.  The information side and the answer side.

### Content Block System
Each side of a flash card uses a flexible multi-block content system. Users can add multiple content blocks of different types to create rich, multimedia flash cards.

#### Supported Block Types:
- **Text blocks**: Rich text with formatting (bold, italic, colors), configurable text size per block, and alignment options (center, left, right)
- **Image blocks**: PNG/JPG images that scale to match the stack width while maintaining aspect ratio (maximum 3840 x 2160 pixels)
- **Sound blocks**: WAV or MP3 files with a play button interface
- **Video blocks**: MP4 files (maximum 5 minutes) displayed as thumbnails with play buttons, scaled to stack width

#### Block Management:
- Maximum of 10 blocks per card side
- Blocks are displayed in vertical stack order
- Each block includes up/down arrow buttons for reordering and a delete button
- Block list interface supports scrolling when needed
- Content scales to match stack window width while preserving aspect ratios

#### Block Creation:
Users select block type from a dropdown menu and click a create button to add new blocks.

### Side 1: The information
The information side uses the content block system described above.

### Side 2: The answer
The answer side uses the same content block system as the information side.

### Editing flash cards
The application has three main interfaces: the vault interface (main), the edit interface, and the view interface for studying cards.

#### Edit Mode Interface
Edit mode completely replaces the main interface and provides comprehensive card editing capabilities.

**Layout and Navigation:**
- Displays one card side at a time (information or answer side)
- Side selection via tabs or flip button accessible through menu bar
- Navigation controls in menu bar: Previous, Next, and New Card buttons
- Quick access dropdown selector in menu bar for jumping to specific cards
- Save Changes and Return to Vault buttons in menu bar

**Block Creation and Management:**
- Block creation dropdown and "Create" button positioned above the block list
- Supports adding text, image, sound, and video blocks up to the 10-block limit
- Scrollable block list interface when needed

**Block Editing:**
- Direct click-to-edit functionality for all blocks
- **Text blocks**: Inline rich text editor that visually expands with content
  - Supports multiple lines with maximum 1024 characters
  - Rich formatting options (bold, italic, colors)
  - Configurable text size and alignment per block
- **Media blocks**: File browser dialogs for selection
  - Media preview during file selection process
  - Automatic file organization into appropriate vault subdirectories

**Block Controls:**
- Each block displays up/down arrows for reordering
- Delete button for block removal
- Visual feedback for block order changes

**New Card Creation:**
- New cards start with completely empty sides (no default blocks)
- "New Card" button creates card immediately and switches to it for editing

### Flash card local vault.
The flash card vault is a sub directory in the app folder which contains all of the users local flash cards.

Folder Structure:
./vault/
./vault/sets/
./vault/sets/<set name>/set.json
./vault/sets/<set name>/cards.json
./vault/sets/<set name>/images/
./vault/sets/<set name>/sounds/


### Loading Flash card sets
Flash card sets are loaded from the flash card vault.

### Saving flash card sets
Flash card sets are saved to the flash card vault.

### Exporting and importing
The flash card sets can be exported by zipping the local vault set into single zip file with a filename that matches the set name; this file can then be imported by another user

When importing, the name of the set is first checked, if there are no conflicts the imported flash card set is extracted into the local vault.

**Import Name Conflict Resolution:**
- If imported set name conflicts with existing set, user is prompted to enter a different name
- System suggests default alternative: original name + number (e.g., "Math Cards 2")
- User can accept suggestion or enter custom name
- Same validation rules apply as new set creation

### Vault Export and Import
The application supports exporting and importing the entire vault for backup and sharing purposes.

**Vault Export:**
- Exports complete vault directory structure as a single ZIP file
- Includes all sets, media files, and vault metadata
- Default filename: "FlashCard_Vault_[timestamp].zip"
- User can specify custom export location

**Vault Import:**
- Imports complete vault from ZIP file
- Provides merge options when importing into existing vault:
  - **Replace**: Completely replace existing vault (with confirmation)
  - **Merge**: Add imported sets to existing vault with conflict resolution
  - **Cancel**: Abort import operation

**Vault Import Conflict Resolution:**
- If imported sets have name conflicts with existing sets:
  - Display list of conflicts to user
  - Offer options: Skip conflicting sets, Rename conflicting sets, or Replace existing sets
  - Apply chosen resolution method to all conflicts or handle individually
- Preserve existing sets that don't conflict
- Update vault metadata after successful import

## The application
The application has three main interfaces: vault mode (main startup interface), edit mode, and view mode for studying.

### Vault Mode Interface
The vault mode is the primary interface displayed when the application starts. It serves as the central hub for managing flash card sets.

**Main Display Area:**
- Master list displaying all available flash card sets from the local vault
- Each set displayed with:
  - Set icon (256x256 for large view, smaller sizes for compact views)
  - Set name
  - Set description
  - Creation date and metadata (tags, difficulty level)
  - Card count indicator

**Vault Mode Menu Bar:**
As detailed in the Mode-Specific Features section above, containing: New card set, Load selected, Export selected, Edit selected, Export vault, and Import vault buttons.

**Set Selection:**
- Single-click selection highlighting
- Only one set can be selected at a time
- Visual indication of currently selected set
- Keyboard navigation support (arrow keys, Enter to load/edit)

**Vault Organization:**
- Sets can be sorted by name, creation date, or last accessed
- Search functionality to filter sets by name or tags
- Grid or list view options for set display
- Set count and total cards statistics

**Status and Feedback:**
- Loading indicators at bottom during operations
- Status text for user feedback ("Set loaded successfully", etc.)
- Error log button for accessing detailed error information
- Application version and vault location information

The user will be presented with the contents of the flash card vault. Each flash card set will be displayed with its icon, name and description in a master list. Above the flash card vault master list is the menu bar containing the following buttons:
- New card set.
- Load selected.
- Export selected.
- Edit selected.
- Export vault.
- Import vault.

### New card set
Creating a new flash card set opens a creation dialog with the following requirements:

**Required Information:**
- **Name**: Maximum 128 characters, must be unique (corresponds to vault folder name)
- **Description**: Text description of the set's content/purpose
- **Icon**: Icon selection from available icon sets or custom PNG file upload
  - Dropdown/grid showing available icon sets from `./icons/` folder
  - Option to browse for custom PNG file
  - If no icon selected, "default" icon set is used
  - Custom icons automatically resized and stored in multiple formats: 256x256, 128x128, 64x64, 32x32, 16x16 pixels
  - Source icons should be square for best results

**Additional Metadata:**
- **Tags**: User-defined tags for organization
- **Difficulty Level**: Selectable difficulty rating
- **Creation Date**: Automatically set to current date

**Validation Rules:**
- Set names must be unique across the vault
- Name length limited to 128 characters
- Names must be valid folder names (no special filesystem characters)
- Duplicate name detection with error messaging

**Creation Process:**
1. User clicks "New card set" button
2. Creation dialog opens with form fields
3. User fills required information (name, description) and optional fields
4. Upon creation, new set is saved to vault with proper folder structure
5. Set starts with one blank card (empty sides)
6. Application automatically switches to edit mode for the new set

**Icon Management:**
- Users can add or change icons later through edit mode
- Icon file browser restricted to PNG format
- Automatic multi-resolution icon generation for optimal display
### Load set
If the user clicks the load set button, the currently selected flash card set is loaded.  If the user has not selected a set or there are no sets available the app will inform the user.

If there is a flash card set selected then the application will switch to flash card mode. 

#### View Interface (Study Mode)
The view interface is dedicated to studying flash cards and replaces the main interface during study sessions.

**Navigation Controls:**
- Menu bar contains: Previous, Next, Random, Flip Card, and Return to Vault buttons
- Card status buttons in menu bar: Mark Known, Mark Review, Mark Unknown
- Study mode selector in menu bar for switching between Sequential/Random/Review
- Session statistics display accessible from menu bar
- Keyboard shortcuts: Left/Right arrow keys for navigation, Spacebar for flip

**Card Interaction:**
- Click anywhere on card or press spacebar to flip between sides
- Visual indication of which side is currently displayed
- Smooth flip animation between information and answer sides

**Study Modes:**
- Sequential: Cards in original order
- Random/Shuffled: Randomized card order
- Review Mode: Only cards marked as "Need Review"
- Mode selection available at session start

**Progress Tracking and Card Status:**
- Mark cards as "Known", "Need Review", or "Unknown"
- Keyboard shortcuts: K (known), R (review), U (unknown)
- Visual status indicators on cards (green checkmark, red dot, etc.)
- Auto-save card statuses to set data

**Session Management:**
- Session statistics display: cards studied, time spent, cards remaining
- Progress bar showing session completion
- Session timer
- Overall set progress percentage
- "Study Complete" notification when all cards reviewed
- Options to restart session or return to vault

**Analytics Dashboard:**
- Simple session statistics
- Cards by status breakdown
- Time spent in current session
- Overall set mastery progress 

### Edit selected
The "Edit selected" functionality allows users to modify existing flash card sets from the vault interface.

**Selection Requirements:**
- Only single set selection is supported (no multi-select)
- If no set is selected when "Edit selected" is clicked, display dialog: "Please select or create a set"
- Selected set is highlighted in the vault interface

**Edit Mode Transition:**
- Application switches from vault view to edit interface (complete page/view replacement)
- Edit interface loads with the selected set's data
- User can navigate through all cards in the set using the edit interface controls

**Loading and Feedback:**
- Loading indicator displayed at bottom of application during set loading
- Status text at bottom shows operation feedback ("Set loaded successfully", "Loading set...", etc.)
- Error log button provides access to detailed error information dialog
- If set loading fails, error message displayed with option to view error log
## Error handling and display
The application implements a comprehensive feedback system to keep users informed of operations and errors.

**Status Bar System:**
- Bottom of application displays loading indicators during operations
- Static status text shows operation feedback:
  - Success messages: "Set loaded successfully", "Card saved", "Set exported successfully"
  - Loading states: "Loading set...", "Saving changes...", "Exporting set..."
  - Error notifications: "Failed to load set", "Export failed"

**Error Log System:**
- Error log button accessible from status bar area
- Clicking opens dialog with chronological list of all application errors
- Each error entry includes timestamp, operation, and detailed error message
- Log persists across application sessions
- Clear log option available in error dialog

**Error Scenarios:**
- Corrupted set files (invalid JSON, missing files)
- Missing media files referenced in cards
- File system permission issues
- Import/export failures
- Media file format validation errors
- Network issues (if applicable for future features)

**User Feedback:**
- Clear, non-technical error messages for users
- Detailed technical information available in error log
- Suggested actions when possible ("Check file permissions", "Verify file format")
## Directory structure

### Application Root Structure:
```
./flashcards/                          # Application root directory
├── flashcards.exe                     # Main executable (or .py file)
├── config/
│   └── app_config.json               # Application configuration
├── vault/                            # User's flash card sets
│   └── sets/
│       └── <set name>/
│           ├── set.json             # Set metadata
│           ├── cards.json           # Card data
│           ├── images/              # Set images
│           └── sounds/              # Set audio/video files
├── icons/                           # Available set icons
│   ├── default/                     # Default application icon set
│   │   ├── 256.png                 # 256x256 pixel icon
│   │   ├── 128.png                 # 128x128 pixel icon
│   │   ├── 64.png                  # 64x64 pixel icon
│   │   ├── 32.png                  # 32x32 pixel icon
│   │   └── 16.png                  # 16x16 pixel icon
│   └── <icon_set_name>/            # Additional icon collections
│       ├── 256.png
│       ├── 128.png
│       ├── 64.png
│       ├── 32.png
│       └── 16.png
├── cache/                           # Application cache
│   └── thumbnails/                  # Media file thumbnails
├── logs/                            # Error and application logs
│   └── error.log                    # Error log file
├── temp/                            # Temporary files
│   └── exports/                     # Temporary export files
└── documentation/                   # Help and documentation files
    └── (documentation files)
```

### Configuration File (app_config.json):
```json
{
    "window": {
        "width": 1024,
        "height": 768,
        "maximized": false
    },
    "vault": {
        "last_opened": "",
        "path": "./vault"
    },
    "preferences": {
        "theme": "default",
        "auto_save": true
    }
}
```

### Icon System:
- Application scans `./icons/` folder at startup
- Each subfolder is validated for complete icon set (all 5 PNG sizes)
- Valid icon sets are available for user selection in set creation
- `default` folder contains application's default set icon
- Users can add custom icon sets by creating properly structured folders

### Automatic Directory Creation:
- If any required directories are missing, they are created at startup
- Default config file is generated if not present
- Default icon set is installed if missing

## Libraries used

### Core GUI Framework:
- **PyQt5**: Main user interface framework
  - `PyQt5.QtWidgets`: UI components (windows, buttons, dialogs, layouts)
  - `PyQt5.QtCore`: Core functionality (signals, slots, timers, threading)
  - `PyQt5.QtGui`: Graphics and styling (icons, fonts, colors, images)
  - `PyQt5.QtMultimedia`: Audio and video playback capabilities
  - `PyQt5.QtMultimediaWidgets`: Video display widgets

### Rich Text Editing:
- **PyQt5.QtWidgets.QTextEdit**: Rich text editor for text blocks
- **PyQt5.QtGui.QTextDocument**: Text formatting and document handling
- **PyQt5.QtGui.QTextCursor**: Text manipulation and cursor control

### Image Processing:
- **Pillow (PIL)**: Image resizing, format conversion, and thumbnail generation
  - Used for automatic icon resizing to multiple formats
  - Media thumbnail generation for cache

### File and Data Handling:
- **json** (built-in): Configuration files, set metadata, and card data storage
- **zipfile** (built-in): Export/import functionality for flash card sets
- **os** (built-in): File system operations and directory management
- **pathlib** (built-in): Modern path handling and validation
- **shutil** (built-in): File copying and directory operations

### Media File Support:
- **mimetypes** (built-in): File type detection and validation
- **tempfile** (built-in): Temporary file management for exports
- **hashlib** (built-in): File integrity checking and cache management

### Date and Time:
- **datetime** (built-in): Creation dates, session timing, and log timestamps

### Additional Utilities:
- **re** (built-in): Regular expressions for filename validation
- **logging** (built-in): Error logging system
- **sys** (built-in): System information and application management

### Installation Requirements:
```
PyQt5>=5.15.0
Pillow>=8.0.0
```

### Python Version:
- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+

### Optional Dependencies:
- **pygame**: Alternative audio playback if PyQt5 multimedia has issues
- **send2trash**: Safe file deletion to system trash instead of permanent deletion
# Changelog

## [v1.5.0] - 2025-07-15 🎉

**The Steam Integration Update! This version introduces full management of your Steam library directly within the application.**

### ✨ Main Features: Steam Library Management

* **Automatic Game Detection:**
    * The app now scans all your Steam libraries to find both native **Steam games** and **Non-Steam shortcuts**.
* **On-the-Fly Proton Version Switching:**
    * Change the compatibility tool for any game directly from a dropdown menu.
    * Supports official Proton, Proton-GE, and other custom versions.
* **ProtonDB Ratings:**
    * Fetches and displays the latest ProtonDB compatibility rating (Platinum, Gold, Borked, etc.) for each game.
* **Safe Configuration Saving:**
    * The app safely modifies Steam's configuration files, creating a backup first and prompting you to close Steam to ensure data integrity.

## [v1.4.0] - 2025-07-12 🎉

**This version brings a significant UI overhaul and key internal improvements for a smoother, more robust experience!**

### ✨ Features and Improvements:

* **Complete UI Overhaul (Breeze Style):**
    * Implemented a style system inspired by Plasma 6.0's "Breeze," with centralized colors and typography for a modern and consistent look.
    * Defined and applied separate color palettes for light and dark themes, improving readability and overall aesthetics.
    * Improved styles for buttons, tables, GroupBoxes, lists, trees, text fields (QLineEdit), and comboboxes (QComboBox), including `:hover` and `:pressed` effects for better interactivity.
    * Font sizes adjusted in various widgets like QListWidget and QTreeWidget to enhance information density and reading.

* **Unified and Improved Log Management:**
    * Centralized installation log management into a single `.log` file within the config directory.
    * All log messages now include timestamps and the name of the program or action, facilitating debugging and tracking.

* **Revamped and Safer Backup Logic:**
    * **CHANGE:** The path to the last full backup is now stored for *each* Wine/Proton configuration, allowing for more precise incremental (Rsync) backups for specific environments.
    * The full backup process now creates a folder with a `timestamp` to prevent accidental overwrites.
    * Incremental backups (Rsync) now require a previous full backup for the current configuration, with clear warnings if one doesn't exist.
    * More informative backup dialogs with clear options for "Rsync (Incremental)" or "Full Backup (New)".
    * Improved error handling during the backup process and cleanup of temporary files.

* **Improvements in Program and Component Installation:**
    * **CHANGE:** The installation list now maintains item states ("Finished", "Error", "Skipped", "Cancelled"), and items with errors/cancellations remain checked to facilitate retries.
    * **CHANGE:** Introduced an `item_error` signal in `InstallerThread` to handle individual item errors without halting the entire installation sequence.
    * The installation progress dialog is now "NonModal," allowing the user to interact with the main window (e.g., view the item table) while an installation is in progress, though control buttons are correctly disabled.
    * Re-checking a program in the table after an installation resets its status to "Pending."
    * Clearer warning messages when trying to add programs/components that are already on the list or registered as installed in the prefix.
    * The prefix initialization process (`wineboot`) is now handled more robustly and with progress messages.
    * Successful installation records in `wineprotonmanager.ini` now include the item type and original path/name for greater detail.

* **Folder Path Persistence:**
    * **CHANGE:** The application now remembers the last browsed folder for different file types (Wine/Proton prefixes, Wine/Proton installations, programs, Winetricks), improving usability when opening file dialogs.

* **Robustness and Error Handling:**
    * General improvements in exception handling and path validation for critical operations (downloads, decompressions, Wine/Proton commands).
    * Increased Python's recursion limit to prevent `RecursionError` in environments with many configurations or long lists.
    * More efficient handling of download and installation thread interruptions.

### ⚠️ Important Considerations:

* **Restarting the Application:** Changes to the theme and other general settings now require a full application restart to be applied globally. The configuration dialog will indicate this and facilitate the restart.
* **Winetricks Permissions:** Winetricks path detection and validation have been improved. If you encounter issues, ensure the `winetricks` file has execution permissions.
* **Winetricks Script Compatibility (.wtr):** The addition of custom `.wtr` scripts for installing Winetricks components allows for greater flexibility.

## [v1.3.0] - 2025-07-09 🎉

### Repository Downloads for Wine and Proton
- New "Version Downloads" tab in the configuration dialog
    - Allows adding/removing/enabling/disabling GitHub repositories
- Search and list available versions:
    - Proton: from (GitHub API)
    - Wine: from (GitHub API)
- Automatic download and decompression into:
    - `~/.config/WineProtonManager/Wine`
    - `~/.config/WineProtonManager/Proton`
- Operations in separate threads:
    - `DownloadThread` for downloads
    - `DecompressionThread` for decompression
    - With an interactive progress dialog
- Disk space check before downloading

### Force Installation (--force)
- New configuration option (global and per-session)
- Allows forcing the installation of Winetricks components with `--force`
- Useful for reinstalling/repairing existing components

## Improvements

### Design and Style (inspired by Steam Deck)
- Complete UI redesign with a Steam Deck aesthetic
- Centralization of color variables
- Unified styles (`STYLE_STEAM_DECK`)
- Custom color palettes for:
    - `QApplication`, `QWidget`, `QPushButton`, `QGroupBox`
    - `QLabel`, `QComboBox`, `QLineEdit`, `QListWidget`
    - `QTableWidget`, `QTreeWidget`
- Adjustments to:
    - Font sizes
    - Borders and padding
    - Visual states (hover, pressed, disabled)

### Program Installation Method (Winetricks, EXE, and WTR)
- Unified installation process (`InstallerThread`):
    - Supports `.exe` and `.msi`
    - Winetricks components by name
    - Custom Winetricks scripts (`.wtr`)
- Execution in a separate Konsole window (`nohup konsole -e ...`)
- Detailed logging system per program (`ConfigManager.write_to_log`)
- Installation logging in prefixes (`wineprotonmanager.log`)
- Main table shows statuses:
    - Pending, Installing..., Finished
    - Error, Cancelled, Skipped
    - With color indicators
- Additional features:
    - Selection/deselection of items
    - Reordering with "Move Up"/"Move Down"
    - Auto-unchecking of successful installations

### Component Descriptions in Winetricks
- New "Description" column in the selection dialog
- Detailed descriptions for:
    - Visual Basic libraries
    - Visual C++ runtimes
    - .NET Framework
    - DirectX and multimedia
    - DXVK/VKD3D
    - Codecs
    - System components

## Internal Changes

### Configuration Management (ConfigManager)
- Complete refactoring to centralize configurations
- Initialization with default values (e.g., "Wine-System")
- Better handling of Wine/Proton environment variables
- New `get_installed_winetricks` function for installation history

### Execution Threads
- Consistent use of `QThread` for long operations
- Improvements in the signals and slots system
- More efficient communication between threads and the GUI

### Modal Dialogs
- Automatic application of the current theme (`apply_theme_to_dialog`)

### Error Handling
- Increased robustness in:
    - File operations
    - Network operations
    - External processes
- More informative error messages
- Temporary logs for installations

## [v1.2.0] - 2025-07-06 🎉

#### Console Management (Konsole)
- **New**: Automatic closing of Konsole after each installation finishes
- **Change**: Replaced `--noclose` with `--hold` for better behavior
- **Added**: Explicit `exit` command to ensure terminal closure
- **Optimization**: Reduced wait time between installations

#### Improved Logging System
- **New**: Full capture of console output in log files
- **Improvement**: Standardized format with start/end markers
- **Added**: Logging of the exact command executed
- **Fixed**: Corrected encoding (UTF-8) for special characters

#### Installation Flow
- **Optimization**: Use of `subprocess.Popen` + `wait()` for better control
- **Improvement**: Consistent handling for .exe and Winetricks components
- **Fixed**: Proper deletion of temporary files post-installation

#### User Experience
- **New**: More descriptive progress messages
- **Improvement**: More informative error codes
- **Optimization**: Pre-check for dependencies (konsole)

### Bug Fixes
- **Fixed**: Console not closing automatically
- **Fixed**: Loss of logs in rapid installations
- **Fixed**: Handling of paths with special spaces
- **Fixed**: Cleanup of residual processes

## [v1.1.0] - 2025-07-05 🎉
### Fixed
- Fixed errors in prefix management
- Improvements in version detection
- Fixed installation repair (.exe and .msi)

## [v1.0.0] - 2025-07-05 🎉
### Added
- Initial implementation of the environment manager
- Support for Wine and Proton
- Component installation system via Winetricks
- Interface with light/dark themes

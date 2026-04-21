# Custom Sight

A custom crosshair overlay application for **STALCRAFT / STALCRAFT: X**.  
Draws a fully configurable crosshair on top of any game window without injecting into the game process.

---

## Features

- Transparent overlay crosshair (works over any window)
- Customizable shape, size, color, opacity, gap, thickness
- Preset system — save and switch between multiple crosshair profiles
- Auto-stretch game window to remove black borders
- Custom resolution switching with a hotkey
- Right-mouse-button listener (hides crosshair while ADS)
- System tray icon with quick actions
- Global hotkey `Ctrl+Shift+H` to toggle crosshair visibility

---

## Requirements

- Windows 10 / 11
- Python 3.10+

---

## Installation (from source)

```bash
git clone https://github.com/Saikaro/Custom-sight.git
cd Custom-sight
pip install -r requirements.txt
python run.py
```

---

## Building an executable

Three build scripts are provided in the root of the repository:

| Script | Description |
|---|---|
| `build.bat` | Builds a **folder** distribution (`dist\CustomSight\CustomSight.exe`) and places a shortcut on the Desktop |
| `build_onedir.bat` | Same as above, alternative variant |
| `build_portable.bat` | Builds a **single portable `.exe`** (`dist\CustomSight-portable.exe`) — can be moved anywhere and run without installation |

Simply double-click the desired `.bat` file. It will automatically install all dependencies and run PyInstaller.

---

## Project Structure

```
Custom-sight/
├── run.py                  # Entry point
├── requirements.txt        # Runtime dependencies
├── requirements-build.txt  # Build dependencies (PyInstaller)
├── CustomSight.spec        # PyInstaller spec file
├── build.bat               # Build script (folder)
├── build_onedir.bat        # Build script (folder, alt)
├── build_portable.bat      # Build script (single exe)
└── custom_sight/           # Main package
    ├── __init__.py
    ├── main.py             # Application entry & hotkeys
    ├── main_window.py      # Main settings window
    ├── overlay.py          # Crosshair overlay widget
    ├── settings_window.py  # Settings panel
    ├── widgets.py          # Reusable UI widgets
    ├── config.py           # Config & preset management
    ├── constants.py        # App constants & color palette
    ├── stylesheet.py       # QSS stylesheet
    ├── system.py           # WinAPI helpers
    ├── rmb_listener.py     # Right-click ADS listener
    └── target.ico          # Application icon
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `PyQt5` | GUI framework |
| `pywin32` | Windows API access |
| `keyboard` | Global hotkey registration |
| `pynput` | Mouse button listener |

---

## License

This project is provided as-is for personal use.

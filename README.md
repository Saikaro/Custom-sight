# Custom Sight

Оверлей-прицел для **STALCRAFT / STALCRAFT: X**.  
Рисует полностью настраиваемый прицел поверх игрового окна без инъекций в игровой процесс.

---

## Возможности

- Прозрачный прицел-оверлей (работает поверх любого окна)
- Настройка формы, размера, цвета, прозрачности, зазора и толщины
- Система пресетов — сохраняй и переключайся между профилями прицела
- Авто-растяжение окна игры для удаления чёрных полос
- Переключение разрешения экрана по горячей клавише
- Слушатель правой кнопки мыши (скрывает прицел при прицеливании)
- Иконка в системном трее с быстрыми действиями
- Глобальная горячая клавиша `Ctrl+Shift+H` для показа/скрытия прицела

---

## Требования

- Windows 10 / 11
- Python 3.10+

---

## Установка (из исходников)

```bash
git clone https://github.com/Saikaro/Custom-sight.git
cd Custom-sight
pip install -r requirements.txt
python run.py
```

---

## Сборка исполняемого файла

В корне репозитория находятся три скрипта сборки:

| Скрипт | Описание |
|---|---|
| `build.bat` | Сборка в **папку** (`dist\CustomSight\CustomSight.exe`) + ярлык на рабочем столе |
| `build_onedir.bat` | То же самое, альтернативный вариант |
| `build_portable.bat` | Сборка в **один portable `.exe`** (`dist\CustomSight-portable.exe`) — можно перенести куда угодно |

Просто дважды кликни на нужный `.bat` файл. Все зависимости установятся автоматически.

---

## Структура проекта

```
Custom-sight/
├── run.py                  # Точка входа
├── requirements.txt        # Зависимости приложения
├── requirements-build.txt  # Зависимости для сборки (PyInstaller)
├── CustomSight.spec        # Spec-файл PyInstaller
├── build.bat               # Скрипт сборки (папка)
├── build_onedir.bat        # Скрипт сборки (папка, альт.)
├── build_portable.bat      # Скрипт сборки (один exe)
└── custom_sight/           # Основной пакет
    ├── __init__.py
    ├── main.py             # Запуск приложения и горячие клавиши
    ├── main_window.py      # Главное окно настроек
    ├── overlay.py          # Виджет оверлея прицела
    ├── settings_window.py  # Панель настроек
    ├── widgets.py          # Переиспользуемые UI-виджеты
    ├── config.py           # Управление конфигом и пресетами
    ├── constants.py        # Константы приложения и цветовая палитра
    ├── stylesheet.py       # QSS-стили
    ├── system.py           # Вспомогательные функции WinAPI
    ├── rmb_listener.py     # Слушатель правой кнопки мыши
    └── target.ico          # Иконка приложения
```

---

## Зависимости

| Пакет | Назначение |
|---|---|
| `PyQt5` | GUI-фреймворк |
| `pywin32` | Доступ к Windows API |
| `keyboard` | Регистрация глобальных горячих клавиш |
| `pynput` | Слушатель кнопок мыши |

---

---

# Custom Sight — English

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

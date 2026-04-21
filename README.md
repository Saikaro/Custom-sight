# Custom Sight

Оверлей-прицел для **STALCRAFT / STALCRAFT: X**.  
Рисует полностью настраиваемый прицел поверх игрового окна без инъекций в игровой процесс.

---

## Возможности

- Прозрачный прицел-оверлей (работает поверх любого окна)
- Настройка формы, размера, цвета, прозрачности, зазора и толщины
- Система пресетов — сохраняй и переключайся между профилями прицела
- Возможность менять разрешение (Меняет разрешение в свойствах Windows. После закрытия окна с игрой разрешение сбрасывается автоматически до изначального.)
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

## Скачать

Готовые сборки доступны в разделе [Releases](https://github.com/Saikaro/Custom-sight/releases):

| Файл | Описание |
|---|---|
| `CustomSight-portable.exe` | Один файл — скачай и запусти |
| `CustomSight-vX.X.zip` | Распакуй и запусти `CustomSight.exe`. Работает быстрее. |

---

## Структура проекта

```
Custom-sight/
├── run.py                  # Точка входа
├── requirements.txt        # Зависимости приложения
├── requirements-build.txt  # Зависимости для сборки (PyInstaller)
├── CustomSight.spec        # Spec-файл PyInstaller
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
- Ability to change resolution (Changes resolution in Windows display settings. After closing the game window, resolution resets automatically to the original.)
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

## Download

Pre-built releases are available in the [Releases](https://github.com/Saikaro/Custom-sight/releases) section:

| File | Description |
|---|---|
| `CustomSight-portable.exe` | Single file — download and run |
| `CustomSight-vX.X.zip` | Extract and run `CustomSight.exe`. Starts faster. |

---

## Project Structure

```
Custom-sight/
├── run.py                  # Entry point
├── requirements.txt        # Runtime dependencies
├── requirements-build.txt  # Build dependencies (PyInstaller)
├── CustomSight.spec        # PyInstaller spec file
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

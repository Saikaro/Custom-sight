@echo off
chcp 65001 >nul
echo ============================================
echo  CustomSight — portable (один .exe файл)
echo ============================================
echo.

:: ── Проверить Python ─────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python не найден. Установи Python 3.10+ и добавь его в PATH.
    pause
    exit /b 1
)

:: ── Установить все зависимости автоматически ─────────────────────────────────
echo [*] Обновление pip...
python -m pip install --upgrade pip --quiet

echo [*] Установка зависимостей приложения...
pip install -r requirements.txt --quiet

echo [*] Установка PyInstaller...
pip install -r requirements-build.txt --quiet
echo.

:: ── Очистить предыдущий билд ─────────────────────────────────────────────────
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist

:: ── Сборка onefile ───────────────────────────────────────────────────────────
echo [*] Сборка portable exe...
echo.

pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name CustomSight-portable ^
  --icon "custom_sight\target.ico" ^
  --add-data "custom_sight\target.ico;custom_sight" ^
  --collect-all pynput ^
  --collect-all keyboard ^
  --hidden-import win32timezone ^
  --hidden-import win32gui ^
  --hidden-import win32api ^
  --hidden-import win32con ^
  run.py

if errorlevel 1 (
    echo.
    echo [!] Сборка завершилась с ошибкой. Проверь лог выше.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Готово!
echo  Файл: dist\CustomSight-portable.exe
echo  Можно перенести куда угодно и запустить.
echo ============================================
pause

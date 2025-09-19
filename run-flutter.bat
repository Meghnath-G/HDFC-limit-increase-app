@echo off
echo 🔍 Searching for Flutter project...

:: Find Flutter project directory
for /r %%i in (pubspec.yaml) do (
    findstr /c:"flutter:" "%%i" >nul 2>&1
    if not errorlevel 1 (
        set "FLUTTER_DIR=%%~pi"
        goto :found
    )
)

echo ❌ No Flutter project found!
pause
exit /b 1

:found
echo 📱 Found Flutter project in: %FLUTTER_DIR%
cd /d "%FLUTTER_DIR%"

echo 🧹 Cleaning Flutter project...
flutter clean

echo 📦 Installing dependencies...
flutter pub get

echo 🔧 Running Flutter doctor...
flutter doctor

echo 📱 Checking devices...
flutter devices

echo 🚀 Starting Flutter app...
flutter run

pause
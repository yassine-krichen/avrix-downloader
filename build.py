"""
Build script to create a standalone executable for Avrix YouTube Downloader.
This script uses PyInstaller to bundle the application with all dependencies.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if required tools are installed."""
    print("Checking requirements...\n")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller not found")
        print("  Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    print()

def clean_build_folders():
    """Remove old build artifacts."""
    print("Cleaning old build files...\n")
    
    folders_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["Avrix.spec"]
    
    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✓ Removed {folder}/")
    
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ Removed {file}")
    
    print()

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...\n")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=Avrix",
        "--windowed",  # No console window
        "--onefile",   # Single executable file
        "--icon=assets/avrix_icon.ico" if os.path.exists("assets/avrix_icon.ico") else "",
        "--add-data=assets;assets",  # Include assets folder
        "--add-data=config;config",  # Include config folder
        "--hidden-import=yt_dlp",
        "--hidden-import=PySide6",
        "--hidden-import=certifi",
        "--collect-all=yt_dlp",
        "--collect-all=certifi",
        "--noconfirm",  # Overwrite without asking
        "main.py"
    ]
    
    # Remove empty strings from command
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        subprocess.check_call(cmd)
        print("\n✓ Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

def create_installer_structure():
    """Create folder structure for distribution."""
    print("\nCreating distribution package...\n")
    
    # Create distribution folder
    dist_folder = Path("dist/Avrix_Installer")
    dist_folder.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    exe_source = Path("dist/Avrix.exe")
    if exe_source.exists():
        shutil.copy(exe_source, dist_folder / "Avrix.exe")
        print("✓ Copied Avrix.exe")
    
    # Create README for users
    readme_content = """# Avrix - YouTube Downloader

## Installation

1. Copy the entire "Avrix_Installer" folder to your desired location
2. Double-click "Avrix.exe" to run the application

## First Run

On first run, Avrix will:
- Create necessary configuration files
- Check for ffmpeg (required for video processing)
- If ffmpeg is not found, you'll need to install it separately

## Installing ffmpeg (if needed)

**Option 1: Automatic (Recommended)**
- Avrix will prompt you to download ffmpeg
- Follow the on-screen instructions

**Option 2: Manual**
1. Download ffmpeg from: https://ffmpeg.org/download.html
2. Extract the files
3. Add ffmpeg to your system PATH, or
4. Place ffmpeg.exe in the same folder as Avrix.exe

## Usage

1. Launch Avrix.exe
2. Paste a YouTube URL
3. Select format (MP4 video or MP3 audio)
4. Choose quality and options
5. Click "Download"

## Features

- Download videos in various qualities (up to 4K)
- Extract audio as MP3
- Batch download with queue system
- Concurrent downloads (up to 10 simultaneous)
- Dark/Light theme support
- Subtitle and thumbnail downloads

## System Requirements

- Windows 10 or later
- Internet connection
- ~100MB free disk space

## Support

For issues or questions, please check the documentation.

---
Avrix YouTube Downloader
Version 1.0
"""
    
    with open(dist_folder / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✓ Created README.txt")
    
    print(f"\n✓ Distribution package ready at: {dist_folder.absolute()}")
    print(f"  Executable size: {exe_source.stat().st_size / (1024*1024):.1f} MB")

def create_installer_script():
    """Create a simple installer batch script."""
    print("\nCreating installer script...\n")
    
    installer_script = """@echo off
echo ================================================
echo Avrix YouTube Downloader - Installation
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo Note: Not running as administrator
    echo Some features may require admin rights
)

echo.
echo Installing Avrix...
echo.

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\\Avrix
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
echo Copying files...
copy /Y "Avrix.exe" "%INSTALL_DIR%\\Avrix.exe" >nul
if %errorLevel% == 0 (
    echo [OK] Executable copied
) else (
    echo [ERROR] Failed to copy executable
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT="%USERPROFILE%\\Desktop\\Avrix.lnk"
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='%INSTALL_DIR%\\Avrix.exe'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Save()"
if %errorLevel% == 0 (
    echo [OK] Desktop shortcut created
) else (
    echo [WARNING] Failed to create desktop shortcut
)

REM Create start menu shortcut
echo Creating start menu entry...
set START_MENU="%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Avrix.lnk"
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%START_MENU%'); $s.TargetPath='%INSTALL_DIR%\\Avrix.exe'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Save()"
if %errorLevel% == 0 (
    echo [OK] Start menu entry created
) else (
    echo [WARNING] Failed to create start menu entry
)

echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo Avrix has been installed to: %INSTALL_DIR%
echo.
echo You can now:
echo  - Launch Avrix from your Desktop
echo  - Find it in the Start Menu
echo  - Run it directly from: %INSTALL_DIR%\\Avrix.exe
echo.
echo Press any key to launch Avrix now...
pause >nul

start "" "%INSTALL_DIR%\\Avrix.exe"
exit
"""
    
    dist_folder = Path("dist/Avrix_Installer")
    with open(dist_folder / "Install_Avrix.bat", "w", encoding="utf-8") as f:
        f.write(installer_script)
    print("✓ Created Install_Avrix.bat")

def create_uninstaller_script():
    """Create an uninstaller script."""
    uninstaller_script = """@echo off
echo ================================================
echo Avrix YouTube Downloader - Uninstaller
echo ================================================
echo.
echo This will remove Avrix from your computer.
echo.
set /p CONFIRM="Are you sure you want to uninstall? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Uninstallation cancelled.
    pause
    exit
)

echo.
echo Uninstalling Avrix...
echo.

set INSTALL_DIR=%LOCALAPPDATA%\\Avrix

REM Remove desktop shortcut
if exist "%USERPROFILE%\\Desktop\\Avrix.lnk" (
    del "%USERPROFILE%\\Desktop\\Avrix.lnk"
    echo [OK] Removed desktop shortcut
)

REM Remove start menu entry
if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Avrix.lnk" (
    del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Avrix.lnk"
    echo [OK] Removed start menu entry
)

REM Remove installation directory
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo [OK] Removed installation files
)

echo.
echo ================================================
echo Uninstallation Complete
echo ================================================
echo.
echo Avrix has been removed from your computer.
echo.
pause
"""
    
    dist_folder = Path("dist/Avrix_Installer")
    with open(dist_folder / "Uninstall_Avrix.bat", "w", encoding="utf-8") as f:
        f.write(uninstaller_script)
    print("✓ Created Uninstall_Avrix.bat")

def main():
    """Main build process."""
    print("=" * 60)
    print("Avrix YouTube Downloader - Build Script")
    print("=" * 60)
    print()
    
    # Step 1: Check requirements
    check_requirements()
    
    # Step 2: Clean old builds
    clean_build_folders()
    
    # Step 3: Build executable
    if not build_executable():
        print("\n✗ Build failed. Please check the errors above.")
        return
    
    # Step 4: Create distribution package
    create_installer_structure()
    
    # Step 5: Create installer scripts
    create_installer_script()
    create_uninstaller_script()
    
    print("\n" + "=" * 60)
    print("BUILD COMPLETE!")
    print("=" * 60)
    print(f"\nYour distributable package is ready in:")
    print(f"  dist/Avrix_Installer/")
    print(f"\nTo distribute:")
    print(f"  1. Share the entire 'Avrix_Installer' folder")
    print(f"  2. Users run 'Install_Avrix.bat' to install")
    print(f"  3. Or users can run 'Avrix.exe' directly (portable mode)")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

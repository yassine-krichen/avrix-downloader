# Building Avrix as a Standalone Application

This guide explains how to build Avrix into a standalone Windows executable that users can install and run without needing Python or other dependencies.

## Quick Start

1. **Run the build script:**
   ```bash
   python build_exe.py
   ```

2. **Wait for the build to complete** (may take 5-10 minutes)

3. **Find your distributable in:**
   ```
   dist/Avrix_Installer/
   ```

## What Gets Created

After running `build_exe.py`, you'll have:

```
dist/Avrix_Installer/
├── Avrix.exe              # Main application (50-100 MB)
├── Install_Avrix.bat      # Installer script
├── Uninstall_Avrix.bat    # Uninstaller script
└── README.txt             # User instructions
```

## Distribution Options

### Option 1: Full Installer (Recommended)
Share the entire `Avrix_Installer` folder with users:
- Users run `Install_Avrix.bat`
- Creates desktop and start menu shortcuts
- Installs to `%LOCALAPPDATA%\Avrix`

### Option 2: Portable Mode
Share just `Avrix.exe`:
- Users can run it from any location
- No installation required
- Perfect for USB drives or temporary use

### Option 3: Create ZIP Archive
```bash
# Navigate to dist folder
cd dist
# Create a distributable ZIP
powershell Compress-Archive -Path Avrix_Installer -DestinationPath Avrix_Setup.zip
```

## Build Process Details

The `build_exe.py` script does the following:

1. **Checks Requirements**
   - Installs PyInstaller if not present
   - Verifies all dependencies

2. **Cleans Old Builds**
   - Removes previous build artifacts
   - Ensures fresh build

3. **Builds Executable**
   - Bundles Python interpreter
   - Includes all dependencies (PySide6, yt-dlp, etc.)
   - Embeds icon and assets
   - Creates single `.exe` file

4. **Creates Distribution Package**
   - Copies executable
   - Creates installer scripts
   - Generates documentation

## Requirements for Building

### System Requirements
- Windows 10 or later
- Python 3.8+
- ~2GB free disk space (for build process)

### Python Packages
All required packages will be auto-installed:
- PyInstaller (for building)
- All packages from `requirements.txt`

## Handling ffmpeg

ffmpeg is **NOT** bundled with the executable to keep file size reasonable.

### User Options:

**Option A: Automatic Download** (Recommended)
- Include `setup_ffmpeg.py` in the distribution
- Users run it once to auto-download ffmpeg

**Option B: Manual Installation**
- Users download from https://ffmpeg.org/download.html
- Place `ffmpeg.exe` next to `Avrix.exe`

**Option C: System Installation**
- Users install ffmpeg system-wide
- Add to PATH environment variable

### Pre-bundle ffmpeg (Optional)

If you want to include ffmpeg in your distribution:

1. Download ffmpeg: https://github.com/BtbN/FFmpeg-Builds/releases
2. Extract `ffmpeg.exe`
3. Place it in the project root before building
4. Modify `build_exe.py` to include it:
   ```python
   --add-binary=ffmpeg.exe;.
   ```

## Advanced Build Options

### Customize PyInstaller Options

Edit `build_exe.py` and modify the `cmd` list:

```python
cmd = [
    "pyinstaller",
    "--name=Avrix",
    "--windowed",                    # No console
    # "--console",                   # Show console (for debugging)
    "--onefile",                     # Single file
    # "--onedir",                    # Directory with dependencies
    "--icon=assets/avrix_icon.ico",
    "--add-data=assets;assets",
    "--add-data=config;config",
    # Add more options here
]
```

### Debug Build

For troubleshooting, create a console version:
```python
# In build_exe.py, change:
"--windowed",  # No console window
# To:
"--console",   # Show console window
```

### Reduce File Size

1. Use `--onedir` instead of `--onefile`
2. Use UPX compression (requires separate download)
3. Exclude unnecessary modules:
   ```python
   "--exclude-module=matplotlib",
   "--exclude-module=numpy",
   ```

## Testing the Build

1. **Test the executable:**
   ```bash
   dist\Avrix_Installer\Avrix.exe
   ```

2. **Test the installer:**
   ```bash
   cd dist\Avrix_Installer
   Install_Avrix.bat
   ```

3. **Test on a clean Windows machine:**
   - Copy the folder to a PC without Python
   - Run the installer
   - Verify all features work

## Troubleshooting

### Build Fails

**"Module not found" error:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**"PyInstaller not found":**
```bash
pip install pyinstaller
```

**Icon not found:**
- Ensure `assets/avrix_icon.ico` exists
- Or remove the `--icon` parameter

### Executable Won't Run

**"Failed to execute script":**
- Build with `--console` to see error messages
- Check if antivirus is blocking it

**"Missing DLL":**
- Install Visual C++ Redistributable:
  https://aka.ms/vs/17/release/vc_redist.x64.exe

### Large File Size

Typical sizes:
- Basic build: 50-70 MB
- With all dependencies: 80-120 MB

To reduce:
- Use `--onedir` mode
- Exclude unused modules
- Use UPX compression

## Creating an Installer (Advanced)

For a professional installer, consider:

### Inno Setup (Free)
1. Download: https://jrsoftware.org/isinfo.php
2. Create setup script
3. Generates `.exe` installer

### NSIS (Free)
1. Download: https://nsis.sourceforge.io/
2. Create `.nsi` script
3. Compile to installer

### Example Inno Setup Script
```iss
[Setup]
AppName=Avrix
AppVersion=1.0
DefaultDirName={pf}\Avrix
DefaultGroupName=Avrix
OutputDir=installer
OutputBaseFilename=Avrix_Setup

[Files]
Source: "dist\Avrix_Installer\Avrix.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Avrix"; Filename: "{app}\Avrix.exe"
Name: "{commondesktop}\Avrix"; Filename: "{app}\Avrix.exe"
```

## Distribution Checklist

Before sharing your build:

- [ ] Test on clean Windows machine
- [ ] Verify all features work
- [ ] Check file size is reasonable
- [ ] Include clear installation instructions
- [ ] Test installer script
- [ ] Test uninstaller script
- [ ] Scan with antivirus (to check for false positives)
- [ ] Include license information
- [ ] Add version number to executable
- [ ] Create release notes

## Updating Your Application

To release updates:

1. Update version number in your code
2. Rebuild with `python build_exe.py`
3. Distribute new package
4. Users can install over old version

## Legal Considerations

- Ensure you have rights to bundle all dependencies
- Include appropriate licenses
- yt-dlp is Unlicense (public domain)
- PySide6 is LGPL
- ffmpeg is LGPL/GPL (depending on build)

---

## Need Help?

Common issues and solutions:
- Check PyInstaller documentation: https://pyinstaller.org/
- Review error messages in console mode
- Test on multiple Windows versions
- Check antivirus isn't blocking the executable

Happy building! 🚀

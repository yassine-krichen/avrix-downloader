# Application Icon Setup

## Current Status

The application is configured to use the Avrix logo as its window icon. The icon is set in `ui/main_window.py` and will display in the window title bar and taskbar.

## Using PNG Icons (Current Setup)

The application currently uses PNG files as icons:
- `avrix_logo_dark.png` - Primary icon
- `avrix_logo_light.png` - Fallback icon

This works well for most cases and displays correctly in the window.

## Creating ICO Files (Optional - Better Windows Integration)

For improved Windows taskbar integration, you can convert the PNG to ICO format:

### Option 1: Using Online Converters

1. Go to an online converter:
   - https://convertio.co/png-ico/
   - https://cloudconvert.com/png-to-ico
   - https://icoconvert.com/

2. Upload `assets/avrix_logo_dark.png`

3. Select multiple sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256

4. Download and save as `assets/avrix_icon.ico`

### Option 2: Using Python (Requires Pillow)

1. Install Pillow:
   ```bash
   pip install Pillow
   ```

2. Run the icon creator:
   ```bash
   python create_icon.py
   ```

3. This will create `assets/avrix_icon.ico` with multiple sizes

### Option 3: Using GIMP (Free Software)

1. Open `avrix_logo_dark.png` in GIMP
2. File → Export As
3. Change extension to `.ico`
4. Select multiple sizes in the dialog
5. Export

## Using ICO Files in the Application

Once you have an `.ico` file, update `ui/main_window.py`:

```python
# Change this line in setup_ui():
icon_paths = [
    "assets/avrix_icon.ico",           # Add this first
    "assets/avrix_logo_dark.png",
    "assets/avrix_logo_light.png",
]
```

## Building an EXE with Icon

When creating a standalone executable with PyInstaller:

```bash
pyinstaller --onefile --windowed --icon=assets/avrix_icon.ico main.py
```

This will embed the icon in the EXE file for proper Windows integration.

## Notes

- PNG icons work fine for the window title bar
- ICO files provide better multi-resolution support for Windows
- ICO files are required for proper EXE icon embedding
- The current setup (PNG) is sufficient for development and most use cases

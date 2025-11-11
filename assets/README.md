# Icon Assets

This folder contains application icons and branding assets.

## Required Files:

### 1. **icon.png** (Main Application Icon)
- Size: 256x256 pixels (or higher)
- Format: PNG with transparency
- Usage: Window icon, taskbar icon
- Suggested design: YouTube play button with download arrow

### 2. **icon.ico** (Windows Icon)
- Size: Multiple sizes (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
- Format: ICO file
- Usage: Windows executable icon
- Note: Can be generated from icon.png using online tools

### 3. **logo.png** (Optional - App Logo)
- Size: 512x512 pixels
- Format: PNG with transparency
- Usage: About dialog, splash screen
- Suggested design: Full branding logo with text

## Design Guidelines:

**Color Scheme:**
- Primary: #1976d2 (Blue)
- Accent: #64b5f6 (Light Blue)
- Success: #388e3c (Green)
- Error: #d32f2f (Red)

**Style:**
- Modern, flat design
- Clean and professional
- Recognizable at small sizes
- Works well in both light and dark modes

## Icon Sources:

You can create icons using:
- Figma, Adobe Illustrator, Sketch
- Online icon generators (e.g., icon-icons.com, flaticon.com)
- AI tools (DALL-E, Midjourney)

## Converting PNG to ICO:

Use online tools:
- https://convertico.com/
- https://cloudconvert.com/png-to-ico
- https://www.icoconverter.com/

Or use ImageMagick:
```bash
magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```

## To Use Icons:

1. Place `icon.png` in this assets folder
2. Uncomment the icon loading code in `ui/main_window.py`:
   ```python
   self.setWindowIcon(QIcon("assets/icon.png"))
   ```
3. For Windows executable, use `icon.ico` in PyInstaller spec file

## Current Status:

❌ icon.png - **PENDING** (Please provide)
❌ icon.ico - **PENDING** (Please provide)
❌ logo.png - **OPTIONAL** (Please provide if desired)

Once you provide the icon files, the app will automatically use them!

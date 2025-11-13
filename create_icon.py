"""
Utility script to create a Windows .ico file from PNG images.
Run this to create an icon file for better Windows taskbar integration.
"""

from PIL import Image
import os

def create_icon_from_png(png_path, ico_path, sizes=None):
    """
    Convert PNG to ICO with multiple sizes.
    
    Args:
        png_path: Path to source PNG file
        ico_path: Path to output ICO file
        sizes: List of sizes to include (default: [16, 32, 48, 64, 128, 256])
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    try:
        # Open the source image
        img = Image.open(png_path)
        
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create list of resized images
        icon_sizes = []
        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            icon_sizes.append(resized)
        
        # Save as ICO with all sizes
        icon_sizes[0].save(
            ico_path,
            format='ICO',
            sizes=[(size, size) for size in sizes],
            append_images=icon_sizes[1:]
        )
        
        print(f"✓ Created {ico_path} with sizes: {sizes}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating icon: {e}")
        return False


def main():
    """Create icon files from available PNG assets."""
    print("Creating Windows icon files from PNG assets...\n")
    
    # Define conversions
    conversions = [
        ("assets/avrix_logo_dark.png", "assets/avrix_icon.ico"),
        ("assets/avrix_logo_light.png", "assets/avrix_icon_light.ico"),
    ]
    
    success_count = 0
    for png_path, ico_path in conversions:
        if os.path.exists(png_path):
            print(f"Converting {png_path}...")
            if create_icon_from_png(png_path, ico_path):
                success_count += 1
        else:
            print(f"✗ Source file not found: {png_path}")
    
    print(f"\n{success_count}/{len(conversions)} icon files created successfully!")
    
    if success_count > 0:
        print("\nTo use the icon in your application:")
        print("1. The icon is already set in main_window.py")
        print("2. For better taskbar integration, update setup_ui() to use the .ico file")
        print("3. When creating an .exe with PyInstaller, add: --icon=assets/avrix_icon.ico")


if __name__ == "__main__":
    # Check if Pillow is installed
    try:
        import PIL
        main()
    except ImportError:
        print("Error: Pillow library is required.")
        print("Install it with: pip install Pillow")
        print("\nAlternatively, you can use online converters:")
        print("- https://convertio.co/png-ico/")
        print("- https://cloudconvert.com/png-to-ico")
        print("\nConvert assets/avrix_logo_dark.png to assets/avrix_icon.ico")

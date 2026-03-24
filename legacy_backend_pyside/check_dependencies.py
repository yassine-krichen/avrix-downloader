"""
Simple test script to verify the installation and check dependencies.
"""

import sys
import subprocess

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print("✓ FFmpeg is installed")
            version_line = result.stdout.split('\n')[0]
            print(f"  {version_line}")
            return True
        else:
            print("✗ FFmpeg check failed")
            return False
    except FileNotFoundError:
        print("✗ FFmpeg is NOT installed")
        print("  Please install FFmpeg from https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"✗ Error checking FFmpeg: {e}")
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    packages_ok = True
    
    try:
        import yt_dlp
        print(f"✓ yt-dlp is installed (version {yt_dlp.version.__version__})")
    except ImportError:
        print("✗ yt-dlp is NOT installed")
        packages_ok = False
    
    try:
        import PySide6
        print(f"✓ PySide6 is installed (version {PySide6.__version__})")
    except ImportError:
        print("✗ PySide6 is NOT installed")
        packages_ok = False
    
    return packages_ok

def main():
    """Run all checks."""
    print("YouTube Downloader - Dependency Check")
    print("=" * 50)
    print()
    
    print("Python Packages:")
    packages_ok = check_python_packages()
    print()
    
    print("External Dependencies:")
    ffmpeg_ok = check_ffmpeg()
    print()
    
    print("=" * 50)
    if packages_ok and ffmpeg_ok:
        print("✓ All dependencies are installed!")
        print("✓ You can run the application with: python main.py")
    elif packages_ok and not ffmpeg_ok:
        print("⚠ Python packages are OK, but FFmpeg is missing")
        print("  The app will work, but MP3 conversion may fail")
        print("  Install FFmpeg for full functionality")
    else:
        print("✗ Some dependencies are missing")
        print("  Run: pip install -r requirements.txt")

if __name__ == "__main__":
    main()

"""
Script to help users download and set up ffmpeg automatically.
This can be bundled with the application or run separately.
"""

import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

FFMPEG_DOWNLOAD_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def check_ffmpeg_installed():
    """Check if ffmpeg is already available."""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def download_ffmpeg(destination_folder):
    """Download and extract ffmpeg."""
    print("Downloading ffmpeg... This may take a few minutes.")
    print(f"Source: {FFMPEG_DOWNLOAD_URL}")
    print()
    
    # Create temp directory
    temp_dir = Path(destination_folder) / "temp_ffmpeg"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = temp_dir / "ffmpeg.zip"
    
    try:
        # Download with progress
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            sys.stdout.write(f"\rDownloading: {percent}%")
            sys.stdout.flush()
        
        urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, zip_path, reporthook)
        print("\n✓ Download complete")
        
        # Extract
        print("Extracting ffmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print("✓ Extraction complete")
        
        # Find and copy ffmpeg.exe
        ffmpeg_exe = None
        for root, dirs, files in os.walk(temp_dir):
            if "ffmpeg.exe" in files:
                ffmpeg_exe = Path(root) / "ffmpeg.exe"
                break
        
        if ffmpeg_exe:
            dest_path = Path(destination_folder) / "ffmpeg.exe"
            shutil.copy(ffmpeg_exe, dest_path)
            print(f"✓ ffmpeg installed to: {dest_path}")
            
            # Cleanup
            shutil.rmtree(temp_dir)
            print("✓ Cleaned up temporary files")
            
            return True
        else:
            print("✗ Could not find ffmpeg.exe in downloaded archive")
            return False
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return False

def main():
    """Main setup process."""
    print("=" * 60)
    print("Avrix - ffmpeg Setup Utility")
    print("=" * 60)
    print()
    
    # Check if already installed
    if check_ffmpeg_installed():
        print("✓ ffmpeg is already installed and accessible!")
        print()
        input("Press Enter to exit...")
        return
    
    print("ffmpeg is required for video processing.")
    print("This utility will download and install it for you.")
    print()
    
    # Determine installation location
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        install_dir = Path(sys.executable).parent
    else:
        # Running as script
        install_dir = Path.cwd()
    
    print(f"Installation directory: {install_dir}")
    print()
    
    response = input("Download and install ffmpeg? (Y/N): ")
    if response.lower() != 'y':
        print("Installation cancelled.")
        input("Press Enter to exit...")
        return
    
    print()
    if download_ffmpeg(install_dir):
        print()
        print("=" * 60)
        print("Installation Complete!")
        print("=" * 60)
        print()
        print("ffmpeg has been installed successfully.")
        print("You can now use Avrix to download videos!")
    else:
        print()
        print("=" * 60)
        print("Installation Failed")
        print("=" * 60)
        print()
        print("Please download ffmpeg manually from:")
        print("https://ffmpeg.org/download.html")
        print()
        print("Then place ffmpeg.exe in the same folder as Avrix.exe")
    
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()

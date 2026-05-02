#!/usr/bin/env python3
"""
LEVI Setup Verification Script
Checks all dependencies and system requirements
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_python():
    """Check Python version"""
    print_header("Python Version")
    print(f"✓ Python {sys.version}")
    if sys.version_info < (3, 10):
        print("⚠️  WARNING: Python 3.10+ recommended")
        return False
    return True

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        print(f"✓ {package_name} installed")
        return True
    except ImportError:
        print(f"✗ {package_name} NOT installed - run: pip install {package_name}")
        return False

def check_packages():
    """Check all required packages"""
    print_header("Required Packages")
    
    packages = [
        ("faster-whisper", "faster_whisper"),
        ("numpy", "numpy"),
        ("sounddevice", "sounddevice"),
        ("soundfile", "soundfile"),
        ("edge-tts", "edge_tts"),
    ]
    
    all_installed = True
    for package, import_name in packages:
        if not check_package(package, import_name):
            all_installed = False
    
    return all_installed

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print_header("FFmpeg Installation")
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ FFmpeg installed")
            # Extract version
            version_line = result.stdout.split('\n')[0]
            print(f"  {version_line}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("✗ FFmpeg NOT found")
    print("  Install with: winget install FFmpeg")
    return False

def check_microphone():
    """Check if microphone is available"""
    print_header("Microphone Status")
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"Found {len(devices)} audio device(s):\n")
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  [{i}] {device['name']}")
                print(f"      Channels: {device['max_input_channels']}")
        
        return True
    except Exception as e:
        print(f"✗ Error querying devices: {e}")
        return False

def check_file_structure():
    """Check if project structure is correct"""
    print_header("Project Structure")
    
    required_dirs = [
        "audio",
        "brain",
        "actions",
        "core",
        "utils",
        "ui",
    ]
    
    required_files = [
        "main.py",
        "requirements.txt",
        "audio/speech.py",
        "audio/tts.py",
        "core/loop.py",
        "utils/logger.py",
        "utils/config.py",
    ]
    
    project_root = Path(__file__).parent
    all_present = True
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/")
        else:
            print(f"✗ {dir_name}/ NOT FOUND")
            all_present = False
    
    print()
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.exists():
            print(f"✓ {file_name}")
        else:
            print(f"✗ {file_name} NOT FOUND")
            all_present = False
    
    return all_present

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("  LEVI Assistant - System Check")
    print("="*60)
    
    checks = [
        ("Python Version", check_python()),
        ("Project Structure", check_file_structure()),
        ("Required Packages", check_packages()),
        ("FFmpeg", check_ffmpeg()),
        ("Microphone", check_microphone()),
    ]
    
    print_header("Summary")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to run: python main.py")
        return 0
    else:
        print("\n⚠️  Some checks failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

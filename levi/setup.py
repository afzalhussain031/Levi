#!/usr/bin/env python3
"""
LEVI Setup Script
Automated installation and configuration
"""

import subprocess
import sys
import os
from pathlib import Path

def print_step(step_num, text):
    """Print a numbered step"""
    print(f"\n{'='*60}")
    print(f"  [{step_num}] {text}")
    print(f"{'='*60}")

def print_success(text):
    """Print success message"""
    print(f"  ✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"  ✗ {text}")

def run_command(command, description):
    """Run a shell command"""
    print(f"\n  Running: {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print_success(description)
            return True
        else:
            print_error(f"{description}")
            print(f"    Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_error(f"{description} (timeout)")
        return False
    except Exception as e:
        print_error(f"{description}: {e}")
        return False

def check_python():
    """Check Python version"""
    print_step(1, "Checking Python")
    
    version = sys.version_info
    print(f"\n  Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 10):
        print_error("Python 3.10+ required")
        return False
    
    print_success("Python version OK")
    return True

def check_ffmpeg():
    """Check FFmpeg installation"""
    print_step(2, "Checking FFmpeg")
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"\n  {version_line}")
            print_success("FFmpeg installed")
            return True
    except:
        pass
    
    print_error("FFmpeg not found")
    print("\n  Install with: winget install FFmpeg")
    print("  Then restart this script")
    return False

def create_venv():
    """Create virtual environment"""
    print_step(3, "Creating Virtual Environment")
    
    venv_path = Path(__file__).parent / "venv"
    
    if venv_path.exists():
        print_success("Virtual environment already exists")
        return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creating venv..."
    )

def get_activate_command():
    """Get the activate command for the current OS"""
    if sys.platform == "win32":
        return "venv\\Scripts\\activate.bat && "
    else:
        return "source venv/bin/activate && "

def install_dependencies():
    """Install Python dependencies"""
    print_step(4, "Installing Dependencies")
    
    print("\n  This may take a few minutes...")
    
    activate_cmd = get_activate_command()
    return run_command(
        f"{activate_cmd}pip install -r requirements.txt --upgrade",
        "Installing packages (pip install -r requirements.txt)..."
    )

def verify_imports():
    """Verify all imports work"""
    print_step(5, "Verifying Imports")
    
    packages = [
        ("faster_whisper", "faster-whisper"),
        ("sounddevice", "sounddevice"),
        ("soundfile", "soundfile"),
        ("edge_tts", "edge-tts"),
        ("numpy", "numpy"),
    ]
    
    all_ok = True
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            print_success(f"{package_name}")
        except ImportError:
            print_error(f"{package_name} not found")
            all_ok = False
    
    return all_ok

def create_directories():
    """Create required directories"""
    print_step(6, "Creating Directories")
    
    dirs = [
        "logs",
        "data",
        "data/conversations",
        "models",
    ]
    
    for dir_name in dirs:
        dir_path = Path(__file__).parent / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print_success(f"Created {dir_name}/")
    
    return True

def main():
    """Main setup process"""
    print("\n" + "="*60)
    print("  LEVI Assistant - Automated Setup")
    print("="*60)
    
    steps = [
        ("Python Version", check_python),
        ("FFmpeg", check_ffmpeg),
        ("Virtual Environment", create_venv),
        ("Dependencies", install_dependencies),
        ("Verification", verify_imports),
        ("Directories", create_directories),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print("\n" + "="*60)
            print("  ⚠️  Setup incomplete - see errors above")
            print("="*60)
            return 1
    
    # Success
    print("\n" + "="*60)
    print("  ✓ Setup Complete!")
    print("="*60)
    
    print("\n  Next steps:")
    print("    1. Activate virtual environment:")
    
    if sys.platform == "win32":
        print("       .\\venv\\Scripts\\Activate.ps1")
    else:
        print("       source venv/bin/activate")
    
    print("\n    2. Run LEVI:")
    print("       python main.py")
    
    print("\n  Documentation:")
    print("    - README.md - Full overview")
    print("    - QUICK_START.md - 5-minute guide")
    print("    - ARCHITECTURE.md - System design")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

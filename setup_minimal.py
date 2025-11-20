"""
Minimal Setup Script - No C++ Build Tools Required
Installs only core dependencies (no aiohttp/fastapi).
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(message):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {message}")
    print("="*70 + "\n")

def print_step(step, message):
    """Print step information."""
    print(f"[{step}] {message}")

def run_command(cmd, description):
    """Run command and handle errors."""
    print(f"   Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"   ✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} - Failed")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is sufficient."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def main():
    print_header("Intune App Packager - Minimal Setup (No C++ Required)")
    
    # Check Python version
    print_step("1/5", "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Get project directory
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    print_step("2/5", "Upgrading pip")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrade pip"):
        sys.exit(1)
    
    print_step("3/5", "Installing minimal dependencies")
    print("   ℹ️  Using requirements-minimal.txt (no aiohttp/fastapi)")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements-minimal.txt"], "Install dependencies"):
        sys.exit(1)
    
    print_step("4/5", "Installing package in editable mode")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps"], "Install package"):
        sys.exit(1)
    
    print_step("5/5", "Creating directories")
    dirs_to_create = [
        "output",
        "packages",
        "logs",
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {dir_path}")
    
    print_header("Installation Complete!")
    
    print("✅ Minimal version installed successfully!\n")
    
    print("📦 What was installed:")
    print("   - Core Python package (intune_packager)")
    print("   - Basic dependencies (PyYAML, Jinja2, Click, MSAL)")
    print("   - PowerShell template system")
    print("   - GUI (tkinter - built into Python)\n")
    
    print("⚠️  Not installed (require C++ Build Tools):")
    print("   - aiohttp (Graph API async client)")
    print("   - fastapi/uvicorn (REST API server)")
    print("   - These are for future features\n")
    
    print("🚀 You can now:\n")
    print("   1. Test GUI:")
    print("      python -m intune_packager.installer_gui\n")
    
    print("   2. Test script generation:")
    print('      python -c "from intune_packager import ScriptGenerator; print(\'✅ Works!\')"')
    print("")
    
    print("   3. Build standalone installer:")
    print("      python build_installer_minimal.py\n")
    
    print("="*70)

if __name__ == "__main__":
    main()

"""
Build standalone installer with embedded Python
This creates a single executable that includes Python and all dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_step(message):
    print(f"\n{'='*70}")
    print(f"  {message}")
    print(f"{'='*70}\n")

def run_command(cmd, description):
    """Run command and show output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ {description} failed!")
        print(result.stderr)
        return False
    print(f"✅ {description} completed")
    return True

def main():
    print_step("Building Standalone Installer")
    
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    # Check if PyInstaller is installed
    print("Checking for PyInstaller...")
    result = subprocess.run([sys.executable, "-m", "pip", "show", "pyinstaller"], 
                          capture_output=True)
    
    if result.returncode != 0:
        print("PyInstaller not found. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                          "Install PyInstaller"):
            sys.exit(1)
    
    # Install current package first
    print("\nInstalling package dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], 
                      "Install package"):
        sys.exit(1)
    
    # Create the main entry point for the installer
    print("\nCreating installer entry point...")
    
    installer_script = """
import sys
import os
from pathlib import Path

# Add the bundled package to path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = Path(sys._MEIPASS)
else:
    # Running as script
    bundle_dir = Path(__file__).parent

# Import and run setup
from intune_packager.installer_gui import main as run_installer

if __name__ == '__main__':
    run_installer()
"""
    
    entry_point = project_dir / "installer_main.py"
    with open(entry_point, 'w') as f:
        f.write(installer_script)
    
    # Create PyInstaller spec
    print("\nCreating PyInstaller specification...")
    
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['installer_main.py'],
    pathex=['{project_dir}'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('examples', 'examples'),
        ('USER_GUIDE.md', '.'),
        ('ARCHITECTURE.md', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'intune_packager',
        'intune_packager.models',
        'intune_packager.services',
        'intune_packager.script_generator',
        'jinja2',
        'yaml',
        'msal',
        'aiohttp',
        'click',
        'colorama',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='IntuneAppPackager-Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    spec_file = project_dir / "installer.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    # Build with PyInstaller
    print("\nBuilding executable with PyInstaller...")
    print("This may take a few minutes...")
    
    if not run_command([sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)], 
                      "Build executable"):
        sys.exit(1)
    
    # Check output
    if platform.system() == "Windows":
        exe_name = "IntuneAppPackager-Installer.exe"
    else:
        exe_name = "IntuneAppPackager-Installer"
    
    exe_path = project_dir / "dist" / exe_name
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print_step("Build Successful!")
        print(f"✅ Executable created: {exe_path}")
        print(f"📦 Size: {size_mb:.1f} MB")
        print(f"\n🚀 You can now distribute: {exe_name}")
        print(f"   Users don't need Python installed!")
        print(f"\n   To run: ./{exe_name}")
    else:
        print("❌ Build failed - executable not found")
        sys.exit(1)
    
    # Clean up
    entry_point.unlink()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

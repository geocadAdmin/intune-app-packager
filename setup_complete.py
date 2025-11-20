"""
Complete Setup Script for Intune App Packager
Single command installation with all dependencies.
"""

import os
import sys
import subprocess
import platform
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
    print_header("Intune App Packager - Complete Setup")
    
    # Check Python version
    print_step("1/6", "Checking Python version")
    if not check_python_version():
        sys.exit(1)
    
    # Get project directory
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    print_step("2/6", "Installing Python dependencies")
    if not run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], "Upgrade pip"):
        sys.exit(1)
    
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."], "Install package"):
        sys.exit(1)
    
    print_step("3/6", "Verifying installation")
    if not run_command([sys.executable, "-m", "pip", "list"], "List installed packages"):
        sys.exit(1)
    
    print_step("4/6", "Creating required directories")
    dirs_to_create = [
        "output",
        "packages",
        "logs",
        os.path.expanduser("~/.intune_packager")
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {dir_path}")
    
    print_step("5/6", "Testing script generator")
    test_script = """
from intune_packager.models import ApplicationProfile, Installer, DetectionRule
from intune_packager.script_generator import ScriptGenerator

# Create simple test profile
profile = ApplicationProfile(
    name="TestApp",
    version="1.0.0",
    publisher="TestPublisher"
)

profile.installers = [
    Installer(
        name="Test Installer",
        file="test.exe",
        silent_args="/S"
    )
]

profile.detection_rules = [
    DetectionRule(
        type="file",
        path="C:\\\\Program Files\\\\TestApp\\\\test.exe",
        check_version=True,
        min_version="1.0.0"
    )
]

# Generate scripts
generator = ScriptGenerator()
scripts = generator.generate_all_scripts(profile)

print("✅ Script generation test passed")
print(f"   - Generated {len(scripts)} scripts")
"""
    
    test_file = project_dir / "test_installation.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    if run_command([sys.executable, str(test_file)], "Test script generation"):
        test_file.unlink()  # Clean up test file
    else:
        print("   ⚠️  Script generation test failed (check dependencies)")
    
    print_step("6/6", "Setup complete!")
    
    print_header("Installation Summary")
    
    print("✅ Intune App Packager installed successfully!\n")
    
    print("📦 What was installed:")
    print("   - Python package (intune_packager)")
    print("   - All dependencies (Jinja2, MSAL, aiohttp, PyYAML, etc.)")
    print("   - PowerShell templates")
    print("   - Example configurations\n")
    
    print("📁 Project structure:")
    print(f"   - Project dir: {project_dir}")
    print(f"   - Templates:   {project_dir}/templates")
    print(f"   - Examples:    {project_dir}/examples")
    print(f"   - Output:      {project_dir}/output\n")
    
    print("🚀 Next steps:\n")
    print("   1. Test script generation:")
    print("      python3 -c 'from intune_packager import ScriptGenerator; print(\"✅ Works!\")'\n")
    
    print("   2. Generate scripts from example:")
    print("      python3 examples/generate_example.py\n")
    
    print("   3. Read documentation:")
    print("      - USER_GUIDE.md - Complete user guide")
    print("      - ARCHITECTURE.md - Technical details")
    print("      - examples/ewmapa_config.yml - Real-world example\n")
    
    print("   4. For Windows deployment:")
    print("      - Download IntuneWinAppUtil.exe")
    print("      - Set up Azure AD authentication")
    print("      - See USER_GUIDE.md for details\n")
    
    print("⚠️  Note: GUI (Electron) is not yet implemented.")
    print("   Currently available: CLI + Python API + Script Generation\n")
    
    print("📚 Documentation:")
    print(f"   - {project_dir}/USER_GUIDE.md")
    print(f"   - {project_dir}/ARCHITECTURE.md")
    print(f"   - {project_dir}/PROJECT_STATUS.md\n")
    
    print("="*70)
    print("Installation complete! 🎉")
    print("="*70)

if __name__ == "__main__":
    main()

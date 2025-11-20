#!/usr/bin/env python3
"""
Example: Generate PowerShell scripts from EWMapa configuration
"""

import yaml
from pathlib import Path
from intune_packager.models import ApplicationProfile
from intune_packager.script_generator import ScriptGenerator

def main():
    print("="*70)
    print("  Intune App Packager - Example Script Generation")
    print("="*70)
    print()
    
    # Load example configuration
    config_path = Path(__file__).parent / "ewmapa_config.yml"
    print(f"📄 Loading configuration: {config_path}")
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Create ApplicationProfile from config
    print("🔧 Creating application profile...")
    profile = ApplicationProfile.from_dict(config_data)
    
    print(f"   ✅ Application: {profile.name} v{profile.version}")
    print(f"   ✅ Publisher: {profile.publisher}")
    print(f"   ✅ Installers: {len(profile.installers)}")
    print(f"   ✅ Detection rules: {len(profile.detection_rules)}")
    print()
    
    # Generate PowerShell scripts
    print("📜 Generating PowerShell scripts...")
    generator = ScriptGenerator()
    scripts = generator.generate_all_scripts(profile)
    
    # Save to output directory
    output_dir = Path(__file__).parent.parent / "output" / "ewmapa_scripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for script_name, script_content in scripts.items():
        output_path = output_dir / script_name
        with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(script_content)
        
        lines = len(script_content.split('\n'))
        size = len(script_content)
        print(f"   ✅ {script_name}: {lines} lines, {size} bytes")
    
    print()
    print(f"📁 Scripts saved to: {output_dir}")
    print()
    
    # Show preview of install script
    print("📋 Preview of install.ps1 (first 30 lines):")
    print("-"*70)
    install_script_lines = scripts['install.ps1'].split('\n')
    for i, line in enumerate(install_script_lines[:30], 1):
        print(f"{i:3d} | {line}")
    
    if len(install_script_lines) > 30:
        print(f"... ({len(install_script_lines) - 30} more lines)")
    
    print("-"*70)
    print()
    
    # Show what these scripts do
    print("✨ What these scripts do:")
    print()
    print("📜 install.ps1:")
    print("   - Installs Firebird Database first (dependency)")
    print("   - Then installs EWMapa Application")
    print("   - Creates desktop and start menu shortcuts")
    print("   - Comprehensive logging to C:\\ProgramData\\IntuneAppPackager\\Logs")
    print("   - Returns Intune-compliant exit codes")
    print()
    
    print("📜 uninstall.ps1:")
    print("   - Tries standard uninstall via registry")
    print("   - Falls back to force removal if needed")
    print("   - Kills running processes (EWMapa.exe, fbserver.exe)")
    print("   - Removes files, registry keys, shortcuts")
    print("   - Verifies complete removal")
    print()
    
    print("📜 detection.ps1:")
    print("   - Checks if EWMapa.exe exists with correct version")
    print("   - Validates registry keys for both EWMapa and Firebird")
    print("   - Custom check for Firebird service and database")
    print("   - Returns 0 (detected) or 1 (not detected)")
    print()
    
    print("🚀 Next steps:")
    print("   1. Review the generated scripts in:", output_dir)
    print("   2. Test on Windows (requires IntuneWinAppUtil.exe)")
    print("   3. Deploy to Intune (requires Azure AD setup)")
    print()
    
    print("="*70)
    print("  Example completed successfully! 🎉")
    print("="*70)

if __name__ == "__main__":
    main()

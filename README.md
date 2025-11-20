# Intune App Packager

**Complete Intune application packaging and deployment solution with zero manual Intune portal work required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Overview

Intune App Packager automates the entire lifecycle of Windows application deployment to Microsoft Intune:
- 📦 **Package** - Convert EXE installers to .intunewin with auto-generated PowerShell scripts
- 🚀 **Deploy** - Upload and assign to Azure AD groups via Microsoft Graph API  
- 👥 **Assign** - Select groups visually, configure Company Portal, set dependencies
- 📊 **Monitor** - Real-time deployment status and device-level tracking
- ✅ **Test** - Windows Sandbox testing before production deployment

**Key Innovation**: Handles complex multi-installer scenarios (e.g., Firebird + EWMapa) where multiple EXEs must be installed in sequence.

## ✨ Key Features

### Packaging & Scripts
- 🛠️ **Multi-Installer Support** - Sequential installation with dependency management (Firebird → EWMapa)
- 📜 **Smart PowerShell Generation** - Auto-generated install/uninstall/detection scripts with comprehensive logging
- 🔍 **Enhanced Detection** - Multi-layer detection: file + registry + version + custom PowerShell
- ♻️ **Multi-Strategy Uninstall** - Attempts standard uninstall, falls back to force removal
- 🔗 **Shortcut Management** - Auto-creates desktop/start menu shortcuts if missing

### Intune Integration (Zero Portal Work)
- 🔐 **Complete API Integration** - Microsoft Graph API for all Intune operations
- 👥 **Group Assignment** - Visual Azure AD group selector
- 🏪 **Company Portal** - Full control over app display (description, icon, screenshots)
- 🔗 **Dependencies** - Set which apps must be installed first
- 🔄 **Supersedence** - Automatically replace old versions
- 📊 **Real-time Monitoring** - Track deployment status per device/user

### Development Experience  
- 🖥️ **Dual Interface** - Both GUI (Electron + React) and CLI
- 📦 **YAML Configuration** - Version-controlled application profiles
- 🧪 **Windows Sandbox Testing** - Validate packages before production
- 📑 **Template System** - Customizable PowerShell script templates
- 🤖 **CI/CD Ready** - Service principal authentication for automation

## Prerequisites

- Python 3.8 or higher
- Microsoft Win32 Content Prep Tool (IntuneWinAppUtil.exe)
- Windows OS or Wine (for running Win32 Content Prep Tool on non-Windows systems)

## Installation

### From Source

```bash
git clone https://github.com/yourusername/intune-app-packager.git
cd intune-app-packager
pip install -e .
```

### Using pip

```bash
pip install intune-app-packager
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/intune-app-packager.git
cd intune-app-packager
pip install -e .
```

### Authenticate with Azure AD

```bash
intune-packager auth login --interactive
```

### Create Your First Package

```bash
# Create application config
intune-packager init-app --name "EWMapa" --wizard

# Generate PowerShell scripts
intune-packager generate-scripts --config ewmapa.yml --preview

# Test in Windows Sandbox
intune-packager test-sandbox --config ewmapa.yml

# Deploy to Intune and assign to groups
intune-packager deploy \
  --config ewmapa.yml \
  --groups "IT-Department,GIS-Team" \
  --mode available \
  --monitor
```

### Example: Multi-Installer (Firebird + EWMapa)

See complete example in `examples/ewmapa_config.yml`:

```yaml
application:
  name: "EWMapa"
  version: "2.1.0"
  
installers:
  - name: "Firebird Database"
    file: "Firebird-3.0.10-Setup.exe"
    silent_args: "/VERYSILENT /NORESTART"
    
  - name: "EWMapa Application"
    file: "EWMapa-2.1.0-Setup.exe"
    silent_args: "/S"
    depends_on: ["Firebird Database"]

intune:
  assignments:
    - intent: "available"
      target_groups: ["IT-Department", "GIS-Team"]
```

## Configuration

### YAML Configuration Example

```yaml
intune_win_tool: "C:\\Tools\\IntuneWinAppUtil.exe"
output_directory: "C:\\IntunePackages"

applications:
  - name: "Adobe Reader"
    source_file: "C:\\Installers\\AdobeReader.exe"
    setup_file: "AdobeReader.exe"
    install_command: "AdobeReader.exe /silent"
    uninstall_command: "msiexec /x {GUID} /quiet"
    
  - name: "7-Zip"
    source_file: "C:\\Installers\\7z-setup.exe"
    setup_file: "7z-setup.exe"
    install_command: "7z-setup.exe /S"
    uninstall_command: "C:\\Program Files\\7-Zip\\Uninstall.exe /S"
```

### JSON Configuration Example

```json
{
  "intune_win_tool": "C:\\Tools\\IntuneWinAppUtil.exe",
  "output_directory": "C:\\IntunePackages",
  "applications": [
    {
      "name": "VLC Media Player",
      "source_file": "C:\\Installers\\vlc-installer.exe",
      "setup_file": "vlc-installer.exe",
      "install_command": "vlc-installer.exe /S",
      "uninstall_command": "C:\\Program Files\\VideoLAN\\VLC\\uninstall.exe /S"
    }
  ]
}
```

## CLI Commands

### convert

Convert a single application to .intunewin format.

```bash
intune-packager convert [OPTIONS]

Options:
  --input PATH          Path to the EXE file to convert [required]
  --output PATH         Output directory for .intunewin file [required]
  --setup-file TEXT     Name of the setup file (default: detected automatically)
  --catalog PATH        Path to catalog folder containing source files
  --quiet              Suppress output
  --help               Show help message
```

### batch

Process multiple applications using a configuration file.

```bash
intune-packager batch [OPTIONS]

Options:
  --config PATH        Path to configuration file (YAML or JSON) [required]
  --dry-run           Show what would be done without executing
  --verbose           Enable verbose output
  --help              Show help message
```

### analyze

Analyze an EXE file and extract metadata.

```bash
intune-packager analyze [OPTIONS]

Options:
  --input PATH        Path to the EXE file to analyze [required]
  --output PATH       Save analysis report to file
  --format TEXT       Output format: json, yaml, or text (default: text)
  --help              Show help message
```

## Project Structure

```
intune-app-packager/
├── src/
│   └── intune_packager/
│       ├── __init__.py
│       ├── cli.py                 # Command-line interface
│       ├── converter.py           # IntuneWin wrapper module
│       ├── analyzer.py            # Application analyzer
│       ├── orchestrator.py        # Main orchestration logic
│       └── config.py              # Configuration management
├── tests/
│   ├── __init__.py
│   └── test_*.py                  # Unit tests
├── docs/
│   └── *.md                       # Additional documentation
├── examples/
│   ├── config.yml                 # Example YAML configuration
│   └── config.json                # Example JSON configuration
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── README.md                      # This file
└── .gitignore                     # Git ignore rules
```

## How It Works

1. **Analysis Phase**: The tool analyzes the input EXE file to extract metadata such as version, publisher, product name, and file properties.

2. **Preparation Phase**: Creates a temporary working directory and prepares the source files for conversion.

3. **Conversion Phase**: Invokes the Microsoft Win32 Content Prep Tool (IntuneWinAppUtil.exe) to package the application into .intunewin format.

4. **Cleanup Phase**: Moves the generated .intunewin file to the specified output directory and cleans up temporary files.

## Microsoft Win32 Content Prep Tool

This tool requires the Microsoft Win32 Content Prep Tool (IntuneWinAppUtil.exe). Download it from:
https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool

Place the IntuneWinAppUtil.exe in a known location and configure the path in your configuration file or pass it via command-line arguments.

## Troubleshooting

### Common Issues

**Issue**: "IntuneWinAppUtil.exe not found"
- **Solution**: Ensure the Win32 Content Prep Tool is downloaded and the path is correctly configured.

**Issue**: "Failed to extract metadata from EXE"
- **Solution**: The EXE may not have standard PE headers. Try using the `--setup-file` option to manually specify details.

**Issue**: "Permission denied"
- **Solution**: Ensure you have read/write permissions for the input files and output directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Microsoft for the Win32 Content Prep Tool
- The Python community for excellent libraries

## Support

For issues, questions, or contributions, please visit:
https://github.com/yourusername/intune-app-packager/issues

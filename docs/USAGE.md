# Usage Guide

## Getting Started

### Installation

1. Install the package:
```bash
pip install -e .
```

2. Download the Microsoft Win32 Content Prep Tool from:
   https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool

3. Verify your setup:
```bash
intune-packager validate --tool-path /path/to/IntuneWinAppUtil.exe
```

## Basic Usage

### Converting a Single Application

The simplest way to convert an application:

```bash
intune-packager convert --input /path/to/app.exe --output /path/to/output
```

This will:
1. Analyze the EXE file to extract metadata
2. Create a temporary working directory
3. Convert the application to .intunewin format
4. Place the output file in the specified directory

### With Custom Tool Path

If IntuneWinAppUtil.exe is not in your PATH:

```bash
intune-packager convert \
  --input /path/to/app.exe \
  --output /path/to/output \
  --tool-path C:\\Tools\\IntuneWinAppUtil.exe
```

### Skip Analysis

To skip the analysis phase (faster but less information):

```bash
intune-packager convert --input app.exe --output ./output --no-analyze
```

## Analyzing Applications

Get detailed information about an EXE file:

```bash
intune-packager analyze --input app.exe
```

Save analysis to a file:

```bash
intune-packager analyze --input app.exe --output report.json --format json
```

Available formats:
- `text` - Human-readable text report (default)
- `json` - JSON format
- `yaml` - YAML format

## Batch Processing

### Creating a Configuration File

Generate a template configuration:

```bash
intune-packager init-config --output config.yml
```

Or for JSON format:

```bash
intune-packager init-config --output config.json --format json
```

### Running Batch Conversion

Process all applications in the configuration file:

```bash
intune-packager batch --config config.yml
```

### Dry Run

Preview what will be processed without actually converting:

```bash
intune-packager batch --config config.yml --dry-run
```

## Configuration File Format

### YAML Example

```yaml
intune_win_tool: "C:\\Tools\\IntuneWinAppUtil.exe"
output_directory: "C:\\IntunePackages"
stop_on_error: false

applications:
  - name: "Application Name"
    source_file: "C:\\Installers\\app.exe"
    setup_file: "app.exe"
    install_command: "app.exe /silent"
    uninstall_command: "C:\\Program Files\\App\\uninstall.exe /S"
    analyze: true
```

### Configuration Options

#### Global Settings

- `intune_win_tool` - Path to IntuneWinAppUtil.exe
- `output_directory` - Default output directory for all applications
- `stop_on_error` - Stop processing if any application fails (default: false)

#### Per-Application Settings

Required (choose one):
- `source_file` - Path to a single EXE file
- `source_folder` + `setup_file` - Path to folder containing installer files

Optional:
- `name` - Application name (for logging/reporting)
- `output_folder` - Override the default output directory
- `catalog_folder` - Path to catalog folder for signed applications
- `install_command` - Installation command (for documentation)
- `uninstall_command` - Uninstallation command (for documentation)
- `analyze` - Whether to analyze the application (default: true)
- `quiet` - Suppress conversion output (default: false)

## Advanced Usage

### Working with Signed Applications

If your application has a catalog file:

```bash
intune-packager convert \
  --input app.exe \
  --output ./output \
  --catalog /path/to/catalog
```

### Custom Setup File Name

If the setup file has a different name than the source file:

```bash
intune-packager convert \
  --input /path/to/installer/app-v1.0.exe \
  --output ./output \
  --setup-file app-v1.0.exe
```

## Common Scenarios

### Scenario 1: Converting NSIS Installer

```bash
intune-packager convert \
  --input "7z-setup.exe" \
  --output "./intune-packages"
```

### Scenario 2: Converting MSI Wrapper

```bash
intune-packager convert \
  --input "GoogleChrome.msi" \
  --output "./intune-packages"
```

### Scenario 3: Application with Multiple Files

Create a configuration file:

```yaml
applications:
  - name: "Complex App"
    source_folder: "C:\\Installers\\ComplexApp"
    setup_file: "setup.exe"
    output_folder: "C:\\IntunePackages\\ComplexApp"
```

Then run:

```bash
intune-packager batch --config config.yml
```

### Scenario 4: Batch Processing Multiple Apps

1. Create `applications.yml`:

```yaml
intune_win_tool: "C:\\Tools\\IntuneWinAppUtil.exe"
output_directory: "C:\\IntunePackages"

applications:
  - name: "7-Zip"
    source_file: "C:\\Installers\\7z-setup.exe"
    install_command: "7z-setup.exe /S"
    
  - name: "Notepad++"
    source_file: "C:\\Installers\\npp-installer.exe"
    install_command: "npp-installer.exe /S"
    
  - name: "VLC"
    source_file: "C:\\Installers\\vlc-installer.exe"
    install_command: "vlc-installer.exe /S"
```

2. Run batch conversion:

```bash
intune-packager batch --config applications.yml
```

## Troubleshooting

### IntuneWinAppUtil.exe Not Found

Error: `IntuneWinAppUtil.exe not found`

Solutions:
1. Download the tool from Microsoft's GitHub repository
2. Specify the path explicitly:
   ```bash
   intune-packager convert --tool-path /path/to/IntuneWinAppUtil.exe ...
   ```
3. Add the tool to your system PATH

### pefile Library Not Available

Warning: `pefile library not available`

This is optional but recommended for detailed PE analysis:

```bash
pip install pefile
```

### Permission Denied

Ensure you have:
- Read permissions for source files
- Write permissions for output directory
- Execute permissions for IntuneWinAppUtil.exe

### Invalid EXE File

If the tool reports an invalid EXE file:
1. Verify the file is not corrupted
2. Check if it's actually a PE executable
3. Try analyzing it first: `intune-packager analyze --input file.exe`

## Tips and Best Practices

1. **Always test conversions**: Start with one application before batch processing
2. **Use version control**: Keep your configuration files in version control
3. **Document install commands**: Include install/uninstall commands in your config
4. **Organize output**: Use separate output folders for different applications
5. **Validate first**: Run `intune-packager validate` before starting
6. **Use dry-run**: Test batch configurations with `--dry-run` first
7. **Keep logs**: Enable verbose mode (`-v`) for troubleshooting

## Environment Variables

You can set these environment variables:

- `INTUNE_WIN_TOOL_PATH` - Default path to IntuneWinAppUtil.exe
- `INTUNE_OUTPUT_DIR` - Default output directory

Example:

```bash
export INTUNE_WIN_TOOL_PATH="/opt/tools/IntuneWinAppUtil.exe"
export INTUNE_OUTPUT_DIR="/var/intune-packages"
```

## Getting Help

For more help on any command:

```bash
intune-packager --help
intune-packager convert --help
intune-packager batch --help
intune-packager analyze --help
```

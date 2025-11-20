# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Intune App Packager is a comprehensive Windows application packaging and deployment solution for Microsoft Intune. It generates PowerShell installation scripts, wraps applications with Microsoft's IntuneWinAppUtil.exe, and provides full Microsoft Graph API integration for automated Intune deployment with zero manual portal work.

## Development Setup

### Quick Setup (Recommended)

```bash
# Complete setup with all dependencies and directory structure
python3 setup_complete.py
```

This automated script:
- Verifies Python 3.8+ is installed
- Installs the package in development mode
- Creates required directories
- Tests script generation functionality

### Manual Installation

```bash
# Install in development mode
pip install -e .

# Verify installation
intune-packager --version
```

### Prerequisites

- Python 3.8+ (use `python3` on this system, not `python`)
- Microsoft Win32 Content Prep Tool (IntuneWinAppUtil.exe) - required for .intunewin packaging
- Azure AD app registration - required for Microsoft Graph API integration
- Optional: Windows Sandbox (Windows 10/11 Pro+) for testing

### Building Standalone Installer

To create a distributable executable that bundles Python and all dependencies:

```bash
# Build standalone installer (creates ~50-80MB executable)
python3 build_installer.py

# Output: dist/IntuneAppPackager-Installer
# Users don't need Python installed to run this
```

## Common Commands

### Testing the GUI

```bash
# Test tkinter GUI (after installation)
python3 -m intune_packager.installer_gui

# Test GUI from source
python3 src/intune_packager/installer_gui.py
```

### Testing Script Generation

```bash
# Quick test that script generation works
python3 -c 'from intune_packager import ScriptGenerator; print("✅ Works!")'

# Generate scripts from example config
python3 examples/generate_example.py  # if this file exists
```

### Unit Testing

This project currently has minimal test infrastructure. When adding tests:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest tests/

# Run specific test file
pytest tests/test_analyzer.py

# Run with coverage
pytest --cov=src/intune_packager tests/
```

### Running the CLI

```bash
# Convert single application
intune-packager convert --input app.exe --output ./output

# Analyze application
intune-packager analyze --input app.exe

# Batch process
intune-packager batch --config examples/config.yml --dry-run

# Generate template config
intune-packager init-config --output config.yml

# Validate setup
intune-packager validate
```

### Code Quality

```bash
# Format code (if adding formatting tools)
black src/ tests/

# Type checking (if adding mypy)
mypy src/

# Linting (if adding flake8/ruff)
flake8 src/
ruff check src/
```

## Architecture

### Core Components

The application follows a layered architecture with clear separation of concerns:

1. **CLI Layer** (`cli.py`)
   - Entry point for all user interactions
   - Handles argument parsing via Click
   - Provides colorized output with colorama
   - Commands: convert, batch, analyze, validate, init-config
   - All CLI commands route through the orchestrator

2. **GUI Layer** (`installer_gui.py`) **✅ NEW**
   - Tkinter-based GUI for non-technical users
   - Loads YAML configuration files (especially `examples/ewmapa_config.yml`)
   - Generates PowerShell scripts via ScriptGenerator
   - Can be bundled as standalone executable with PyInstaller
   - Entry point: `python3 -m intune_packager.installer_gui`

3. **Orchestration Layer** (`orchestrator.py`)
   - Coordinates the complete packaging workflow
   - Manages the analysis → conversion pipeline
   - Handles batch processing of multiple applications
   - Contains the core business logic for workflow coordination
   - Methods: `package_application()`, `package_from_folder()`, `batch_package()`

4. **Script Generator** (`script_generator.py`) **✅ NEW - CRITICAL**
   - Generates PowerShell install/uninstall/detection scripts from Jinja2 templates
   - Uses ApplicationProfile data model as input
   - Templates in `templates/install/`, `templates/uninstall/`, `templates/detection/`
   - Key method: `generate_all_scripts()` returns dict of script name → content
   - Ensures Windows line endings (CRLF) for PowerShell compatibility

5. **Microsoft Graph API Client** (`services/intune_api.py`) **✅ NEW - CRITICAL**
   - Complete Intune automation via Microsoft Graph API
   - Async/await pattern using aiohttp for performance
   - Authentication: both interactive (MSAL PublicClientApplication) and service principal (ConfidentialClientApplication)
   - Key operations:
     - `list_groups()` - List Azure AD groups for assignment
     - `create_win32_app()` - Create Win32 app in Intune
     - `upload_intunewin_content()` - Upload .intunewin to Azure Storage
     - `assign_app_to_groups()` - Assign app to Azure AD groups
     - `set_app_dependencies()` / `set_app_supersedence()` - Manage app relationships
     - `get_app_install_status()` - Monitor deployment progress

6. **Data Models** (`models/app_profile.py`) **✅ NEW - CRITICAL**
   - Complete dataclass-based models for application configuration
   - Core classes:
     - `ApplicationProfile` - Top-level app configuration
     - `Installer` - Installer configuration with dependencies
     - `DetectionRule` - Multi-type detection (file/registry/process/script)
     - `UninstallStrategy` - Multi-strategy uninstall (standard/force/multi)
     - `Shortcut` - Shortcut definitions
     - `Assignment` - Intune assignment configuration
     - `CompanyPortalMetadata` - Company Portal display metadata
     - `IntuneSettings` / `IntuneRequirements` - Intune-specific settings
   - All models have `to_dict()` methods for template rendering
   - Fully serializable to/from YAML

7. **Converter Layer** (`converter.py`)
   - Wraps IntuneWinAppUtil.exe subprocess calls
   - Manages temporary working directories
   - Handles both single-file and folder-based conversions
   - Automatically finds the tool in common locations or PATH
   - Key method: `convert()` is the core wrapper around IntuneWinAppUtil

8. **Analyzer Layer** (`analyzer.py`)
   - Extracts metadata from PE executables using pefile library
   - Detects installer types (NSIS, Inno Setup, InstallShield, etc.)
   - Generates reports in text/JSON/YAML formats
   - Gracefully degrades if pefile is unavailable
   - Key methods: `analyze()`, `detect_installer_type()`

9. **Configuration Layer** (`config.py`)
   - Loads and validates YAML/JSON configuration files
   - Parses batch processing configurations
   - Generates template configurations
   - Applies defaults and validates required fields

### Key Design Patterns

- **Template-Based Script Generation**: PowerShell scripts generated from Jinja2 templates using ApplicationProfile models
- **Async API Pattern**: Microsoft Graph API calls use async/await for performance (aiohttp)
- **Dependency Injection**: IntuneWinAppUtil.exe path is injected into converter
- **Graceful Degradation**: pefile and PyYAML are optional dependencies with fallbacks
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Pipeline Pattern**: Orchestrator chains analysis → script generation → packaging → deployment
- **Result Objects**: All operations return dictionaries with status, errors, and results
- **Dataclass Models**: All configuration uses dataclasses with `to_dict()` for serialization

### Data Flow

**Current Workflow (PowerShell Script Generation):**
1. User loads YAML config (e.g., `ewmapa_config.yml`) → Parsed to `ApplicationProfile`
2. `ScriptGenerator` loads Jinja2 templates from `templates/`
3. Templates rendered with ApplicationProfile data → PowerShell scripts
4. Scripts saved to output directory with CRLF line endings
5. User manually uses scripts + IntuneWinAppUtil.exe to create .intunewin
6. User manually uploads to Intune portal OR uses Graph API (via `intune_api.py`)

**Legacy Workflow (Direct Conversion - Still Supported):**
1. User invokes CLI command → `cli.py`
2. CLI creates `PackageOrchestrator` instance
3. Orchestrator creates `ApplicationAnalyzer` and `IntuneWinConverter` instances
4. For conversion:
   - Analyzer extracts metadata (optional)
   - Converter creates temp folder, copies files, invokes IntuneWinAppUtil.exe
   - Results bubble back up through orchestrator to CLI
5. CLI displays formatted results to user

**Future Workflow (Full Automation - Planned):**
1. Load ApplicationProfile from YAML
2. Generate PowerShell scripts (ScriptGenerator)
3. Build .intunewin package (PackageBuilder - needs implementation)
4. Authenticate with Azure AD (IntuneAPIClient)
5. Upload to Intune (Graph API)
6. Assign to groups (Graph API)
7. Set dependencies/supersedence (Graph API)
8. Monitor deployment (Graph API)

### Error Handling

- FileNotFoundError: Raised when source files or IntuneWinAppUtil.exe are missing
- ValueError: Raised for invalid configurations or parameters
- RuntimeError: Raised when conversions or API calls fail
- All exceptions are caught at CLI layer and displayed with colored error messages
- Batch processing continues on error unless `stop_on_error` is set
- Graph API errors wrapped in RuntimeError with HTTP status and response

## Important Patterns

### Working with Script Templates

PowerShell script generation is the **core feature** of this tool:
- Templates located in `templates/install/`, `templates/uninstall/`, `templates/detection/`
- Use Jinja2 syntax for variable substitution and control flow
- Templates receive context from `ApplicationProfile.to_dict()` and related model methods
- **Critical**: Always ensure CRLF line endings for PowerShell scripts (see `save_scripts()` in `script_generator.py`)
- Templates support:
  - Multi-installer scenarios (sequential installation with dependencies)
  - Multi-strategy uninstall (standard → force fallback)
  - Comprehensive detection (file + registry + version + process + custom)
  - Automatic shortcut creation if missing
  - Intune-compliant exit codes and comprehensive logging

When adding or modifying templates:
- Test with real ApplicationProfile objects using `generate_all_scripts()`
- Verify PowerShell syntax by running generated scripts in PowerShell
- Ensure logging paths use `C:\ProgramData\IntuneAppPackager\Logs\`
- Use proper Intune exit codes (0=success, 1707=already installed, 3010=reboot required)

### Working with ApplicationProfile Models

The dataclass-based models in `models/app_profile.py` are central to configuration:
- **All models have `to_dict()` methods** for template rendering and YAML serialization
- Models support complex scenarios:
  - Multiple installers with dependencies (`Installer.depends_on`)
  - Multiple detection rules with different types (file, registry, process, script)
  - Multi-strategy uninstall (standard method + force removal)
  - Multiple shortcuts across Desktop/StartMenu
  - Multiple Intune assignments with different intents (available/required/uninstall)
- When adding new fields, update:
  1. Dataclass definition
  2. `to_dict()` method
  3. Related Jinja2 templates
  4. Example YAML configs in `examples/`

### Working with Microsoft Graph API

The `IntuneAPIClient` in `services/intune_api.py` provides full Intune automation:
- **Authentication**:
  - Interactive: `authenticate_interactive()` for GUI users (browser flow)
  - Service Principal: `authenticate_service_principal(client_secret)` for CI/CD
  - Tokens cached in `~/.intune_packager/token_cache.json`
- **Async Pattern**: All API methods use `async`/`await` - must be called from async context
- **Error Handling**: API errors raise `RuntimeError` with HTTP status and response body
- **Endpoints**: Uses both v1.0 (`GRAPH_API_ENDPOINT`) and beta (`GRAPH_API_BETA`) as needed
- Required Azure AD permissions:
  - `DeviceManagementApps.ReadWrite.All`
  - `Group.Read.All`
  - `DeviceManagementManagedDevices.Read.All`

When extending Graph API functionality:
- Add new methods following existing patterns in `IntuneAPIClient`
- Use `_make_request()` helper for authenticated requests
- Set `use_beta=True` if endpoint requires beta API
- Add proper type hints and docstrings
- Log all operations with `logger.info()`

### Working with IntuneWinAppUtil.exe

IntuneWinAppUtil.exe is an external dependency. The tool:
- Must be downloaded separately from Microsoft's GitHub
- Requires specific command-line arguments: `-c` (source folder), `-s` (setup file), `-o` (output folder)
- Runs as a subprocess via `subprocess.run()`
- Outputs a `.intunewin` file named after the setup file (without extension)

When modifying converter code:
- Always validate tool existence before invoking
- Use `capture_output=True` to capture stdout/stderr
- Check for `.intunewin` file creation to verify success
- Handle Windows path separators appropriately

### Configuration File Structure

Configuration files support two modes:
1. **File mode**: `source_file` for single EXE
2. **Folder mode**: `source_folder` + `setup_file` for multi-file installers

Both YAML and JSON are supported. When adding new config options:
- Add to template in `config.py::create_template_config()`
- Update validation in `config.py::validate_config()`
- Update parsing in `config.py::parse_config_for_batch()`
- Update examples in `examples/` directory

### PE Analysis with pefile

The pefile library is optional but provides rich metadata:
- Product name, version, company, description
- Import DLL dependencies
- Machine type (x86, x64, ARM)
- Subsystem (GUI vs Console)

When enhancing analysis:
- Always check `self.pefile_available` before using pefile
- Wrap pefile operations in try/except to handle malformed PEs
- Close PE objects with `pe.close()` to avoid resource leaks
- Use `.decode('utf-8', errors='ignore')` when reading PE strings

### Adding New CLI Commands

To add a new command:
1. Define command function decorated with `@cli.command()` in `cli.py`
2. Add Click options for parameters
3. Use `print_info()`, `print_success()`, `print_error()` for colored output
4. Route logic through orchestrator when possible
5. Handle exceptions and exit with appropriate codes
6. Update `--help` documentation

## File Organization

```
src/intune_packager/
├── __init__.py          # Package exports
├── cli.py               # Click-based CLI (entry point)
├── orchestrator.py      # Workflow coordination
├── converter.py         # IntuneWinAppUtil wrapper
├── analyzer.py          # PE file analysis
└── config.py            # Config loading/validation

tests/                   # Unit tests (minimal currently)
examples/                # Example configuration files
docs/USAGE.md           # Detailed user documentation
```

## Development Notes

### Platform Considerations

- This tool is designed primarily for Windows (IntuneWinAppUtil.exe is Windows-only)
- Can run on non-Windows with Wine, but not commonly used that way
- Path handling uses `os.path` and `Path` objects for cross-platform compatibility
- The current development system is macOS but target platform is Windows

### Logging

- Uses Python's `logging` module throughout
- Logger instances: `logger = logging.getLogger(__name__)`
- Default level: INFO (can be changed to DEBUG with `--verbose` flag)
- Log critical operations: file operations, subprocess calls, analysis results

### Dependencies

Core dependencies (from requirements.txt):
- `click` - CLI framework
- `pyyaml` - YAML config parsing
- `pefile` - PE file analysis
- `colorama` - Cross-platform colored output
- `tqdm` - Progress bars (for potential future use)

Keep dependencies minimal. When adding new ones:
- Make them optional if possible with fallback behavior
- Update requirements.txt
- Update setup.py `install_requires`

### Windows-Specific Code

IntuneWinAppUtil.exe requires:
- Windows-style paths (backslashes in config examples)
- Proper quoting of paths with spaces
- Running as subprocess with appropriate shell settings

When testing on macOS/Linux, use mock subprocess calls or Wine.

## Testing Strategy

When writing tests:
1. Mock IntuneWinAppUtil.exe subprocess calls (it won't exist in CI)
2. Use `tempfile.TemporaryDirectory()` for file operations
3. Test each module independently (unit tests)
4. Create fixture EXE files or mock pefile.PE objects
5. Test error conditions (missing files, invalid configs, subprocess failures)
6. Test both CLI commands and underlying modules directly

## Troubleshooting Development Issues

### "IntuneWinAppUtil.exe not found"

This is expected during development without the actual tool. Options:
1. Download the tool from Microsoft's GitHub for real testing
2. Mock the subprocess calls in tests
3. Use `validate` command to check if tool is accessible

### "pefile library not available"

Install with: `pip install pefile`

The tool will work without it but with reduced analysis capabilities.

### Import Errors

Ensure you've installed in development mode: `pip install -e .`

This creates editable install linking to your source directory.

## Entry Point

The main CLI entry point is defined in setup.py:
```python
entry_points={
    "console_scripts": [
        "intune-packager=intune_packager.cli:main",
    ],
}
```

After installation, `intune-packager` command becomes available system-wide.

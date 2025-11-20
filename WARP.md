# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Intune App Packager is a Python CLI tool that automates converting Windows EXE applications to .intunewin format for Microsoft Intune deployment. It wraps Microsoft's Win32 Content Prep Tool (IntuneWinAppUtil.exe) and provides application analysis, batch processing, and configuration management capabilities.

## Development Setup

### Installation

```bash
# Install in development mode
pip install -e .

# Verify installation
intune-packager --version
```

### Prerequisites

- Python 3.8+ (use `python3` on this system, not `python`)
- Microsoft Win32 Content Prep Tool (IntuneWinAppUtil.exe) - required for conversions
- Optional: pefile library for detailed PE analysis (installed via requirements.txt)

### Validation

```bash
# Validate setup and dependencies
intune-packager validate --tool-path /path/to/IntuneWinAppUtil.exe
```

## Common Commands

### Testing

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

2. **Orchestration Layer** (`orchestrator.py`)
   - Coordinates the complete packaging workflow
   - Manages the analysis → conversion pipeline
   - Handles batch processing of multiple applications
   - Contains the core business logic for workflow coordination
   - Methods: `package_application()`, `package_from_folder()`, `batch_package()`

3. **Converter Layer** (`converter.py`)
   - Wraps IntuneWinAppUtil.exe subprocess calls
   - Manages temporary working directories
   - Handles both single-file and folder-based conversions
   - Automatically finds the tool in common locations or PATH
   - Key method: `convert()` is the core wrapper around IntuneWinAppUtil

4. **Analyzer Layer** (`analyzer.py`)
   - Extracts metadata from PE executables using pefile library
   - Detects installer types (NSIS, Inno Setup, InstallShield, etc.)
   - Generates reports in text/JSON/YAML formats
   - Gracefully degrades if pefile is unavailable
   - Key methods: `analyze()`, `detect_installer_type()`

5. **Configuration Layer** (`config.py`)
   - Loads and validates YAML/JSON configuration files
   - Parses batch processing configurations
   - Generates template configurations
   - Applies defaults and validates required fields

### Key Design Patterns

- **Dependency Injection**: IntuneWinAppUtil.exe path is injected into converter
- **Graceful Degradation**: pefile and PyYAML are optional dependencies with fallbacks
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Pipeline Pattern**: Orchestrator chains analysis → conversion steps
- **Result Objects**: All operations return dictionaries with status, errors, and results

### Data Flow

1. User invokes CLI command → `cli.py`
2. CLI creates `PackageOrchestrator` instance
3. Orchestrator creates `ApplicationAnalyzer` and `IntuneWinConverter` instances
4. For conversion:
   - Analyzer extracts metadata (optional)
   - Converter creates temp folder, copies files, invokes IntuneWinAppUtil.exe
   - Results bubble back up through orchestrator to CLI
5. CLI displays formatted results to user

### Error Handling

- FileNotFoundError: Raised when source files or IntuneWinAppUtil.exe are missing
- ValueError: Raised for invalid configurations or parameters
- RuntimeError: Raised when conversions fail
- All exceptions are caught at CLI layer and displayed with colored error messages
- Batch processing continues on error unless `stop_on_error` is set

## Important Patterns

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

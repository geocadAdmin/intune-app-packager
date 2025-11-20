"""
CLI Module
Command-line interface for the Intune App Packager.
"""

import sys
import os
import logging
from pathlib import Path

import click
from colorama import init, Fore, Style

from . import __version__
from .orchestrator import PackageOrchestrator
from .analyzer import ApplicationAnalyzer
from .config import ConfigManager

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_success(message: str):
    """Print success message in green."""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str):
    """Print error message in red."""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}", err=True)


def print_warning(message: str):
    """Print warning message in yellow."""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message in blue."""
    click.echo(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """
    Intune App Packager - Automated solution for converting Windows applications to .intunewin format.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose mode enabled")


@cli.command()
@click.option('--input', '-i', 'input_file', required=True, type=click.Path(exists=True), 
              help='Path to the EXE file to convert')
@click.option('--output', '-o', 'output_folder', required=True, type=click.Path(),
              help='Output directory for .intunewin file')
@click.option('--tool-path', type=click.Path(exists=True),
              help='Path to IntuneWinAppUtil.exe')
@click.option('--setup-file', help='Name of the setup file (if different from input file name)')
@click.option('--catalog', type=click.Path(exists=True),
              help='Path to catalog folder for signed applications')
@click.option('--no-analyze', is_flag=True, help='Skip application analysis')
@click.option('--quiet', '-q', is_flag=True, help='Suppress conversion output')
@click.pass_context
def convert(ctx, input_file, output_folder, tool_path, setup_file, catalog, no_analyze, quiet):
    """
    Convert a single application to .intunewin format.
    
    Example:
        intune-packager convert -i app.exe -o ./output
    """
    try:
        print_info(f"Converting {input_file} to .intunewin format...")
        
        # Initialize orchestrator
        orchestrator = PackageOrchestrator(intune_win_tool_path=tool_path)
        
        # Package the application
        if setup_file or catalog:
            # Use folder-based conversion if setup_file or catalog is specified
            source_folder = os.path.dirname(input_file) or '.'
            setup_file = setup_file or os.path.basename(input_file)
            
            result = orchestrator.package_from_folder(
                source_folder=source_folder,
                setup_file=setup_file,
                output_folder=output_folder,
                catalog_folder=catalog,
                analyze=not no_analyze,
                quiet=quiet
            )
        else:
            result = orchestrator.package_application(
                source_file=input_file,
                output_folder=output_folder,
                analyze=not no_analyze,
                quiet=quiet
            )
        
        # Display results
        if result['status'] == 'success':
            print_success(f"Conversion successful!")
            print_info(f"Output file: {result.get('output_file')}")
            
            if 'installer_type' in result:
                print_info(f"Detected installer type: {result['installer_type']}")
        else:
            print_error(f"Conversion failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            logger.exception("Detailed error information:")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', 'config_file', required=True, type=click.Path(exists=True),
              help='Path to configuration file (YAML or JSON)')
@click.option('--tool-path', type=click.Path(exists=True),
              help='Path to IntuneWinAppUtil.exe (overrides config)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.pass_context
def batch(ctx, config_file, tool_path, dry_run):
    """
    Process multiple applications using a configuration file.
    
    Example:
        intune-packager batch -c config.yml
    """
    try:
        print_info(f"Loading configuration from {config_file}...")
        
        # Load and parse configuration
        config_manager = ConfigManager()
        raw_config = config_manager.load_config(config_file)
        parsed_config = config_manager.parse_config_for_batch(raw_config)
        
        print_success(f"Configuration loaded: {len(parsed_config['applications'])} applications")
        
        if dry_run:
            print_info("DRY RUN MODE - No actual conversions will be performed")
            print_info("\nApplications to be processed:")
            for i, app in enumerate(parsed_config['applications'], 1):
                name = app.get('name', f'Application {i}')
                source = app.get('source_file') or app.get('source_folder')
                print_info(f"  {i}. {name}")
                print_info(f"     Source: {source}")
                print_info(f"     Output: {app.get('output_folder') or parsed_config.get('default_output_folder')}")
            return
        
        # Use tool_path from command line or config
        final_tool_path = tool_path or parsed_config.get('intune_win_tool')
        
        # Initialize orchestrator
        orchestrator = PackageOrchestrator(intune_win_tool_path=final_tool_path)
        
        # Process batch
        print_info("\nStarting batch processing...")
        results = orchestrator.batch_package(
            applications=parsed_config['applications'],
            default_output_folder=parsed_config.get('default_output_folder'),
            stop_on_error=parsed_config.get('stop_on_error', False)
        )
        
        # Display results
        print_info(f"\nBatch processing completed:")
        print_success(f"  Successful: {results['successful']}")
        if results['failed'] > 0:
            print_error(f"  Failed: {results['failed']}")
        
        # Show details for failed applications
        failed_apps = [app for app in results['applications'] if app.get('status') != 'success']
        if failed_apps:
            print_warning("\nFailed applications:")
            for app in failed_apps:
                idx = app.get('index', '?')
                error = app.get('error', 'Unknown error')
                print_error(f"  {idx}. {error}")
        
        if results['failed'] > 0:
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            logger.exception("Detailed error information:")
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', 'input_file', required=True, type=click.Path(exists=True),
              help='Path to the EXE file to analyze')
@click.option('--output', '-o', 'output_file', type=click.Path(),
              help='Save analysis report to file')
@click.option('--format', '-f', type=click.Choice(['text', 'json', 'yaml']), default='text',
              help='Output format')
@click.pass_context
def analyze(ctx, input_file, output_file, format):
    """
    Analyze an EXE file and extract metadata.
    
    Example:
        intune-packager analyze -i app.exe
        intune-packager analyze -i app.exe -o report.json -f json
    """
    try:
        print_info(f"Analyzing {input_file}...")
        
        # Initialize analyzer
        analyzer = ApplicationAnalyzer()
        
        # Perform analysis
        analysis_result = analyzer.analyze(input_file)
        
        # Detect installer type
        installer_type = analyzer.detect_installer_type(input_file)
        analysis_result['installer_type'] = installer_type
        
        # Generate report
        report = analyzer.generate_report(analysis_result, format=format)
        
        # Output results
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print_success(f"Analysis report saved to {output_file}")
        else:
            click.echo(report)
        
        print_success("Analysis completed")
        
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            logger.exception("Detailed error information:")
        sys.exit(1)


@cli.command()
@click.option('--tool-path', type=click.Path(exists=True),
              help='Path to IntuneWinAppUtil.exe')
@click.pass_context
def validate(ctx, tool_path):
    """
    Validate that all required tools and dependencies are available.
    
    Example:
        intune-packager validate
        intune-packager validate --tool-path /path/to/IntuneWinAppUtil.exe
    """
    try:
        print_info("Validating setup...")
        
        # Initialize orchestrator (this will check for the tool)
        try:
            orchestrator = PackageOrchestrator(intune_win_tool_path=tool_path)
            validation = orchestrator.validate_setup()
        except FileNotFoundError as e:
            print_error(f"IntuneWinAppUtil.exe not found: {e}")
            print_info("\nDownload it from: https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool")
            sys.exit(1)
        
        # Display validation results
        click.echo("\nValidation Results:")
        click.echo("-" * 50)
        
        if validation.get('intune_win_tool'):
            print_success("IntuneWinAppUtil.exe: Found and working")
        else:
            print_error("IntuneWinAppUtil.exe: Not found or not working")
        
        if validation.get('pefile_library'):
            print_success("pefile library: Installed")
        else:
            print_warning("pefile library: Not installed (PE analysis will be limited)")
            print_info("  Install with: pip install pefile")
        
        click.echo("-" * 50)
        
        if validation.get('all_valid'):
            print_success("\n✓ All required components are available")
        else:
            print_warning("\n⚠ Some optional components are missing")
            
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            logger.exception("Detailed error information:")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', 'output_file', required=True, type=click.Path(),
              help='Output file path for template configuration')
@click.option('--format', '-f', type=click.Choice(['yaml', 'json']), default='yaml',
              help='Output format')
@click.pass_context
def init_config(ctx, output_file, format):
    """
    Generate a template configuration file.
    
    Example:
        intune-packager init-config -o config.yml
        intune-packager init-config -o config.json -f json
    """
    try:
        print_info(f"Generating template configuration...")
        
        config_manager = ConfigManager()
        template = config_manager.create_template_config(format=format)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print_success(f"Template configuration saved to {output_file}")
        print_info("Edit the file to customize for your applications")
        
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            logger.exception("Detailed error information:")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        print_warning("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error occurred:")
        sys.exit(1)


if __name__ == '__main__':
    main()

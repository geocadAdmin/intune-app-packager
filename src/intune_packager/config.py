"""
Configuration Manager Module
Handles loading and parsing YAML/JSON configuration files for batch processing.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not available. YAML configuration files cannot be loaded.")

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation for batch processing."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self.yaml_available = YAML_AVAILABLE
    
    def load_config(self, config_path: str) -> Dict:
        """
        Load configuration from a YAML or JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary with configuration data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is unsupported or invalid
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        file_ext = Path(config_path).suffix.lower()
        
        logger.info(f"Loading configuration from {config_path}")
        
        if file_ext in ['.yml', '.yaml']:
            return self._load_yaml(config_path)
        elif file_ext == '.json':
            return self._load_json(config_path)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_ext}")
    
    def _load_yaml(self, config_path: str) -> Dict:
        """Load YAML configuration file."""
        if not self.yaml_available:
            raise ValueError("PyYAML library is not available. Cannot load YAML files.")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if not isinstance(config, dict):
                    raise ValueError("Configuration file must contain a dictionary/object")
                return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load YAML configuration: {e}") from e
    
    def _load_json(self, config_path: str) -> Dict:
        """Load JSON configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if not isinstance(config, dict):
                    raise ValueError("Configuration file must contain a dictionary/object")
                return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load JSON configuration: {e}") from e
    
    def validate_config(self, config: Dict) -> tuple[bool, List[str]]:
        """
        Validate configuration structure and content.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for applications list
        if 'applications' not in config:
            errors.append("Configuration must contain 'applications' key")
            return False, errors
        
        applications = config['applications']
        if not isinstance(applications, list):
            errors.append("'applications' must be a list")
            return False, errors
        
        if len(applications) == 0:
            errors.append("'applications' list is empty")
            return False, errors
        
        # Validate each application
        for i, app in enumerate(applications, 1):
            if not isinstance(app, dict):
                errors.append(f"Application {i}: must be a dictionary")
                continue
            
            # Check required fields
            if 'source_file' not in app and 'source_folder' not in app:
                errors.append(f"Application {i}: must have 'source_file' or 'source_folder'")
            
            # If source_folder is specified, setup_file is required
            if 'source_folder' in app and 'setup_file' not in app:
                errors.append(f"Application {i}: 'setup_file' required when using 'source_folder'")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def parse_config_for_batch(self, config: Dict) -> Dict:
        """
        Parse and prepare configuration for batch processing.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Processed configuration with defaults applied
            
        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, errors = self.validate_config(config)
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
        # Extract global settings
        intune_win_tool = config.get('intune_win_tool')
        default_output_folder = config.get('output_directory') or config.get('output_folder')
        stop_on_error = config.get('stop_on_error', False)
        
        # Process applications
        applications = []
        for app in config['applications']:
            processed_app = {
                'source_file': app.get('source_file'),
                'source_folder': app.get('source_folder'),
                'setup_file': app.get('setup_file'),
                'output_folder': app.get('output_folder') or app.get('output_directory'),
                'catalog_folder': app.get('catalog_folder'),
                'analyze': app.get('analyze', True),
                'quiet': app.get('quiet', False),
            }
            
            # Include optional metadata
            if 'name' in app:
                processed_app['name'] = app['name']
            if 'install_command' in app:
                processed_app['install_command'] = app['install_command']
            if 'uninstall_command' in app:
                processed_app['uninstall_command'] = app['uninstall_command']
            
            applications.append(processed_app)
        
        return {
            'intune_win_tool': intune_win_tool,
            'default_output_folder': default_output_folder,
            'stop_on_error': stop_on_error,
            'applications': applications
        }
    
    def save_config(self, config: Dict, output_path: str, format: str = 'yaml') -> None:
        """
        Save configuration to a file.
        
        Args:
            config: Configuration dictionary to save
            output_path: Path where to save the configuration
            format: Output format - 'yaml' or 'json'
            
        Raises:
            ValueError: If format is unsupported or YAML is not available
        """
        if format == 'yaml':
            if not self.yaml_available:
                raise ValueError("PyYAML library is not available. Cannot save YAML files.")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
        elif format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Configuration saved to {output_path}")
    
    def create_template_config(self, format: str = 'yaml') -> str:
        """
        Create a template configuration string.
        
        Args:
            format: Output format - 'yaml' or 'json'
            
        Returns:
            Template configuration as a string
        """
        template = {
            'intune_win_tool': 'C:\\Tools\\IntuneWinAppUtil.exe',
            'output_directory': 'C:\\IntunePackages',
            'stop_on_error': False,
            'applications': [
                {
                    'name': 'Example Application 1',
                    'source_file': 'C:\\Installers\\app1-setup.exe',
                    'setup_file': 'app1-setup.exe',
                    'install_command': 'app1-setup.exe /silent',
                    'uninstall_command': 'C:\\Program Files\\App1\\uninstall.exe /S',
                    'analyze': True
                },
                {
                    'name': 'Example Application 2',
                    'source_folder': 'C:\\Installers\\App2',
                    'setup_file': 'setup.exe',
                    'output_folder': 'C:\\IntunePackages\\App2',
                    'install_command': 'setup.exe /quiet',
                    'uninstall_command': 'msiexec /x {PRODUCT-GUID} /quiet'
                }
            ]
        }
        
        if format == 'yaml':
            if not self.yaml_available:
                raise ValueError("PyYAML library is not available.")
            return yaml.dump(template, default_flow_style=False, sort_keys=False)
        elif format == 'json':
            return json.dumps(template, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

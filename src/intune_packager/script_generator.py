"""
Script Generator Module
Generates PowerShell install/uninstall/detection scripts from templates.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader, Template

from .models.app_profile import ApplicationProfile

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates PowerShell scripts from templates using application profiles."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the script generator.
        
        Args:
            templates_dir: Path to templates directory. If None, uses default location.
        """
        if templates_dir is None:
            # Default to templates/ in project root
            package_dir = Path(__file__).parent.parent.parent
            templates_dir = package_dir / "templates"
        
        self.templates_dir = Path(templates_dir)
        
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        logger.info(f"ScriptGenerator initialized with templates from: {self.templates_dir}")
    
    def generate_install_script(self, profile: ApplicationProfile) -> str:
        """
        Generate install.ps1 script from application profile.
        
        Args:
            profile: Application profile containing installer configuration
            
        Returns:
            Generated PowerShell script content
        """
        logger.info(f"Generating install script for {profile.name} v{profile.version}")
        
        # Determine template based on installer count
        if len(profile.installers) > 1:
            template_name = "install/multi_installer.ps1"
        else:
            template_name = "install/multi_installer.ps1"  # Use same template, works for single too
        
        template = self.env.get_template(template_name)
        
        # Prepare template variables
        context = {
            'app_name': profile.name,
            'app_version': profile.version,
            'publisher': profile.publisher,
            'installers': [inst.to_dict() for inst in profile.installers],
            'detection_rules': [rule.to_dict() for rule in profile.detection_rules],
            'shortcuts': [sc.to_dict() for sc in profile.shortcuts] if profile.auto_create_shortcuts else []
        }
        
        script = template.render(**context)
        logger.info(f"Install script generated successfully ({len(script)} characters)")
        
        return script
    
    def generate_uninstall_script(self, profile: ApplicationProfile) -> str:
        """
        Generate uninstall.ps1 script from application profile.
        
        Args:
            profile: Application profile containing uninstall configuration
            
        Returns:
            Generated PowerShell script content
        """
        logger.info(f"Generating uninstall script for {profile.name} v{profile.version}")
        
        # Use multi-strategy template
        template_name = "uninstall/multi_strategy.ps1"
        template = self.env.get_template(template_name)
        
        # Prepare template variables
        context = {
            'app_name': profile.name,
            'app_version': profile.version,
            'publisher': profile.publisher,
            'detection_rules': [rule.to_dict() for rule in profile.detection_rules],
            'processes_to_kill': profile.uninstall.kill_processes,
            'paths_to_remove': profile.uninstall.remove_paths,
            'registry_keys_to_remove': profile.uninstall.remove_registry,
            'shortcuts': [sc.to_dict() for sc in profile.shortcuts]
        }
        
        script = template.render(**context)
        logger.info(f"Uninstall script generated successfully ({len(script)} characters)")
        
        return script
    
    def generate_detection_script(self, profile: ApplicationProfile) -> str:
        """
        Generate detection.ps1 script from application profile.
        
        Args:
            profile: Application profile containing detection rules
            
        Returns:
            Generated PowerShell script content
        """
        logger.info(f"Generating detection script for {profile.name} v{profile.version}")
        
        # Use comprehensive detection template
        template_name = "detection/comprehensive.ps1"
        template = self.env.get_template(template_name)
        
        # Prepare template variables
        context = {
            'app_name': profile.name,
            'app_version': profile.version,
            'publisher': profile.publisher,
            'detection_rules': [rule.to_dict() for rule in profile.detection_rules],
            'custom_detection_script': profile.custom_detection_script
        }
        
        script = template.render(**context)
        logger.info(f"Detection script generated successfully ({len(script)} characters)")
        
        return script
    
    def generate_all_scripts(self, profile: ApplicationProfile) -> Dict[str, str]:
        """
        Generate all three scripts (install, uninstall, detection).
        
        Args:
            profile: Application profile
            
        Returns:
            Dictionary with script names as keys and content as values
        """
        logger.info(f"Generating all scripts for {profile.name} v{profile.version}")
        
        scripts = {
            'install.ps1': self.generate_install_script(profile),
            'uninstall.ps1': self.generate_uninstall_script(profile),
            'detection.ps1': self.generate_detection_script(profile)
        }
        
        logger.info(f"All scripts generated successfully")
        return scripts
    
    def save_scripts(self, profile: ApplicationProfile, output_dir: str) -> Dict[str, str]:
        """
        Generate and save all scripts to specified directory.
        
        Args:
            profile: Application profile
            output_dir: Directory to save scripts
            
        Returns:
            Dictionary mapping script names to their file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving scripts to: {output_path}")
        
        scripts = self.generate_all_scripts(profile)
        file_paths = {}
        
        for script_name, script_content in scripts.items():
            file_path = output_path / script_name
            with open(file_path, 'w', encoding='utf-8', newline='\r\n') as f:
                f.write(script_content)
            
            file_paths[script_name] = str(file_path)
            logger.info(f"Saved {script_name} to {file_path}")
        
        return file_paths
    
    def preview_script(self, profile: ApplicationProfile, script_type: str = 'install') -> str:
        """
        Generate a preview of a specific script type.
        
        Args:
            profile: Application profile
            script_type: Type of script ('install', 'uninstall', 'detection')
            
        Returns:
            Generated script content
        """
        if script_type == 'install':
            return self.generate_install_script(profile)
        elif script_type == 'uninstall':
            return self.generate_uninstall_script(profile)
        elif script_type == 'detection':
            return self.generate_detection_script(profile)
        else:
            raise ValueError(f"Unknown script type: {script_type}")

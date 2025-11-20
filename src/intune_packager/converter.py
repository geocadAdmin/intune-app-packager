"""
IntuneWin Converter Module
Wraps Microsoft Win32 Content Prep Tool functionality for converting applications to .intunewin format.
"""

import os
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class IntuneWinConverter:
    """Handles conversion of EXE files to .intunewin format using Microsoft Win32 Content Prep Tool."""
    
    def __init__(self, intune_win_tool_path: Optional[str] = None):
        """
        Initialize the converter.
        
        Args:
            intune_win_tool_path: Path to IntuneWinAppUtil.exe. If None, attempts to find it in PATH.
        """
        self.intune_win_tool_path = intune_win_tool_path or self._find_intune_tool()
        if not self.intune_win_tool_path or not os.path.exists(self.intune_win_tool_path):
            raise FileNotFoundError(
                "IntuneWinAppUtil.exe not found. Please download it from "
                "https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool"
            )
        
        logger.info(f"Using IntuneWinAppUtil at: {self.intune_win_tool_path}")
    
    def _find_intune_tool(self) -> Optional[str]:
        """Attempt to find IntuneWinAppUtil.exe in common locations."""
        common_paths = [
            "IntuneWinAppUtil.exe",
            "./IntuneWinAppUtil.exe",
            "../tools/IntuneWinAppUtil.exe",
            "C:\\Tools\\IntuneWinAppUtil.exe",
            os.path.join(os.path.expanduser("~"), "Downloads", "IntuneWinAppUtil.exe"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # Try to find in PATH
        tool_path = shutil.which("IntuneWinAppUtil.exe")
        return tool_path if tool_path else None
    
    def convert(
        self,
        source_folder: str,
        setup_file: str,
        output_folder: str,
        catalog_folder: Optional[str] = None,
        quiet: bool = False
    ) -> Dict[str, any]:
        """
        Convert application to .intunewin format.
        
        Args:
            source_folder: Path to folder containing the setup files
            setup_file: Name of the setup file (e.g., "setup.exe")
            output_folder: Path to output folder where .intunewin file will be created
            catalog_folder: Optional path to catalog folder for signed apps
            quiet: Suppress command output
            
        Returns:
            Dictionary with conversion results including output_file path and status
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If conversion fails
        """
        # Validate inputs
        if not os.path.exists(source_folder):
            raise ValueError(f"Source folder does not exist: {source_folder}")
        
        setup_file_path = os.path.join(source_folder, setup_file)
        if not os.path.exists(setup_file_path):
            raise ValueError(f"Setup file does not exist: {setup_file_path}")
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Build command
        cmd = [
            self.intune_win_tool_path,
            "-c", source_folder,
            "-s", setup_file,
            "-o", output_folder
        ]
        
        if catalog_folder:
            if not os.path.exists(catalog_folder):
                raise ValueError(f"Catalog folder does not exist: {catalog_folder}")
            cmd.extend(["-a", catalog_folder])
        
        if quiet:
            cmd.append("-q")
        
        logger.info(f"Running conversion command: {' '.join(cmd)}")
        
        try:
            # Run the conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Conversion successful")
            logger.debug(f"Command output: {result.stdout}")
            
            # Find the generated .intunewin file
            intunewin_file = self._find_intunewin_file(output_folder, setup_file)
            
            return {
                "status": "success",
                "output_file": intunewin_file,
                "output_folder": output_folder,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Conversion failed: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def _find_intunewin_file(self, output_folder: str, setup_file: str) -> Optional[str]:
        """Find the generated .intunewin file in the output folder."""
        # The tool typically names the file as <setup_file_without_extension>.intunewin
        base_name = os.path.splitext(setup_file)[0]
        expected_file = os.path.join(output_folder, f"{base_name}.intunewin")
        
        if os.path.exists(expected_file):
            return expected_file
        
        # Search for any .intunewin file in the output folder
        for file in os.listdir(output_folder):
            if file.endswith(".intunewin"):
                return os.path.join(output_folder, file)
        
        return None
    
    def convert_with_temp_folder(
        self,
        source_file: str,
        output_folder: str,
        quiet: bool = False
    ) -> Dict[str, any]:
        """
        Convert a single application file to .intunewin format using a temporary folder.
        
        This is a convenience method that handles creating a temporary source folder
        for a single file conversion.
        
        Args:
            source_file: Path to the application file (e.g., setup.exe)
            output_folder: Path to output folder
            quiet: Suppress command output
            
        Returns:
            Dictionary with conversion results
        """
        if not os.path.exists(source_file):
            raise ValueError(f"Source file does not exist: {source_file}")
        
        # Create temporary folder
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy source file to temp directory
            temp_file = os.path.join(temp_dir, os.path.basename(source_file))
            shutil.copy2(source_file, temp_file)
            
            logger.info(f"Copied {source_file} to temporary folder {temp_dir}")
            
            # Convert
            return self.convert(
                source_folder=temp_dir,
                setup_file=os.path.basename(source_file),
                output_folder=output_folder,
                quiet=quiet
            )
    
    def validate_tool(self) -> bool:
        """
        Validate that the IntuneWinAppUtil tool is accessible and working.
        
        Returns:
            True if tool is valid, False otherwise
        """
        try:
            result = subprocess.run(
                [self.intune_win_tool_path, "-h"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 or "usage" in result.stdout.lower()
        except Exception as e:
            logger.error(f"Failed to validate tool: {e}")
            return False

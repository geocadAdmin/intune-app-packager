"""
Package Orchestrator Module
Coordinates the complete conversion process from EXE input to .intunewin output.
"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path

from .analyzer import ApplicationAnalyzer
from .converter import IntuneWinConverter

logger = logging.getLogger(__name__)


class PackageOrchestrator:
    """Orchestrates the complete application packaging workflow."""
    
    def __init__(self, intune_win_tool_path: Optional[str] = None):
        """
        Initialize the orchestrator.
        
        Args:
            intune_win_tool_path: Path to IntuneWinAppUtil.exe
        """
        self.analyzer = ApplicationAnalyzer()
        self.converter = IntuneWinConverter(intune_win_tool_path)
        logger.info("PackageOrchestrator initialized")
    
    def package_application(
        self,
        source_file: str,
        output_folder: str,
        analyze: bool = True,
        quiet: bool = False
    ) -> Dict[str, any]:
        """
        Complete workflow to package an application.
        
        Args:
            source_file: Path to the EXE file to package
            output_folder: Output directory for .intunewin file
            analyze: Whether to analyze the application before conversion
            quiet: Suppress conversion output
            
        Returns:
            Dictionary with complete results including analysis and conversion info
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            RuntimeError: If packaging fails
        """
        if not os.path.exists(source_file):
            raise FileNotFoundError(f"Source file not found: {source_file}")
        
        logger.info(f"Starting packaging workflow for: {source_file}")
        
        result = {
            "source_file": source_file,
            "output_folder": output_folder,
            "status": "started"
        }
        
        # Step 1: Analysis (optional but recommended)
        if analyze:
            logger.info("Step 1: Analyzing application")
            try:
                analysis = self.analyzer.analyze(source_file)
                result["analysis"] = analysis
                
                # Detect installer type
                installer_type = self.analyzer.detect_installer_type(source_file)
                result["installer_type"] = installer_type
                logger.info(f"Detected installer type: {installer_type}")
                
            except Exception as e:
                logger.warning(f"Analysis failed, continuing with conversion: {e}")
                result["analysis_error"] = str(e)
        
        # Step 2: Conversion
        logger.info("Step 2: Converting to .intunewin format")
        try:
            conversion_result = self.converter.convert_with_temp_folder(
                source_file=source_file,
                output_folder=output_folder,
                quiet=quiet
            )
            result["conversion"] = conversion_result
            result["output_file"] = conversion_result.get("output_file")
            result["status"] = "success"
            
            logger.info(f"Packaging completed successfully: {conversion_result.get('output_file')}")
            
        except Exception as e:
            error_msg = f"Conversion failed: {e}"
            logger.error(error_msg)
            result["status"] = "failed"
            result["error"] = str(e)
            raise RuntimeError(error_msg) from e
        
        return result
    
    def package_from_folder(
        self,
        source_folder: str,
        setup_file: str,
        output_folder: str,
        catalog_folder: Optional[str] = None,
        analyze: bool = True,
        quiet: bool = False
    ) -> Dict[str, any]:
        """
        Package an application from a folder containing setup files.
        
        This is useful when you have a folder with multiple files needed for installation.
        
        Args:
            source_folder: Path to folder containing setup files
            setup_file: Name of the main setup file
            output_folder: Output directory for .intunewin file
            catalog_folder: Optional catalog folder for signed apps
            analyze: Whether to analyze the application
            quiet: Suppress conversion output
            
        Returns:
            Dictionary with complete results
        """
        setup_file_path = os.path.join(source_folder, setup_file)
        if not os.path.exists(setup_file_path):
            raise FileNotFoundError(f"Setup file not found: {setup_file_path}")
        
        logger.info(f"Starting packaging workflow for folder: {source_folder}")
        
        result = {
            "source_folder": source_folder,
            "setup_file": setup_file,
            "output_folder": output_folder,
            "status": "started"
        }
        
        # Analysis
        if analyze:
            logger.info("Analyzing application")
            try:
                analysis = self.analyzer.analyze(setup_file_path)
                result["analysis"] = analysis
                
                installer_type = self.analyzer.detect_installer_type(setup_file_path)
                result["installer_type"] = installer_type
                
            except Exception as e:
                logger.warning(f"Analysis failed: {e}")
                result["analysis_error"] = str(e)
        
        # Conversion
        logger.info("Converting to .intunewin format")
        try:
            conversion_result = self.converter.convert(
                source_folder=source_folder,
                setup_file=setup_file,
                output_folder=output_folder,
                catalog_folder=catalog_folder,
                quiet=quiet
            )
            result["conversion"] = conversion_result
            result["output_file"] = conversion_result.get("output_file")
            result["status"] = "success"
            
            logger.info(f"Packaging completed: {conversion_result.get('output_file')}")
            
        except Exception as e:
            error_msg = f"Conversion failed: {e}"
            logger.error(error_msg)
            result["status"] = "failed"
            result["error"] = str(e)
            raise RuntimeError(error_msg) from e
        
        return result
    
    def batch_package(
        self,
        applications: list,
        default_output_folder: Optional[str] = None,
        stop_on_error: bool = False
    ) -> Dict[str, any]:
        """
        Package multiple applications in batch.
        
        Args:
            applications: List of application dictionaries with 'source_file' and optional 'output_folder'
            default_output_folder: Default output folder if not specified per application
            stop_on_error: Whether to stop processing on first error
            
        Returns:
            Dictionary with batch results
        """
        logger.info(f"Starting batch packaging of {len(applications)} applications")
        
        results = {
            "total": len(applications),
            "successful": 0,
            "failed": 0,
            "applications": []
        }
        
        for i, app in enumerate(applications, 1):
            source_file = app.get("source_file")
            output_folder = app.get("output_folder", default_output_folder)
            
            if not source_file:
                logger.error(f"Application {i}: No source_file specified, skipping")
                results["applications"].append({
                    "index": i,
                    "status": "skipped",
                    "error": "No source_file specified"
                })
                results["failed"] += 1
                continue
            
            if not output_folder:
                logger.error(f"Application {i}: No output_folder specified, skipping")
                results["applications"].append({
                    "index": i,
                    "source_file": source_file,
                    "status": "skipped",
                    "error": "No output_folder specified"
                })
                results["failed"] += 1
                continue
            
            logger.info(f"Processing application {i}/{len(applications)}: {source_file}")
            
            try:
                # Check if it's a folder or file conversion
                if "source_folder" in app:
                    result = self.package_from_folder(
                        source_folder=app["source_folder"],
                        setup_file=app.get("setup_file", os.path.basename(source_file)),
                        output_folder=output_folder,
                        catalog_folder=app.get("catalog_folder"),
                        analyze=app.get("analyze", True),
                        quiet=app.get("quiet", False)
                    )
                else:
                    result = self.package_application(
                        source_file=source_file,
                        output_folder=output_folder,
                        analyze=app.get("analyze", True),
                        quiet=app.get("quiet", False)
                    )
                
                result["index"] = i
                results["applications"].append(result)
                results["successful"] += 1
                
            except Exception as e:
                logger.error(f"Application {i} failed: {e}")
                results["applications"].append({
                    "index": i,
                    "source_file": source_file,
                    "status": "failed",
                    "error": str(e)
                })
                results["failed"] += 1
                
                if stop_on_error:
                    logger.error("Stopping batch processing due to error")
                    break
        
        logger.info(f"Batch packaging completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def validate_setup(self) -> Dict[str, bool]:
        """
        Validate that all required tools and dependencies are available.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            "intune_win_tool": False,
            "pefile_library": self.analyzer.pefile_available,
        }
        
        # Validate IntuneWinAppUtil
        try:
            validation["intune_win_tool"] = self.converter.validate_tool()
        except Exception as e:
            logger.error(f"Failed to validate IntuneWinAppUtil: {e}")
        
        all_valid = all(validation.values())
        validation["all_valid"] = all_valid
        
        return validation

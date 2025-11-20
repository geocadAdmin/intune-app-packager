"""
Application Analyzer Module
Analyzes EXE files to extract metadata, detect dependencies, and identify installation requirements.
"""

import os
import logging
from typing import Dict, List, Optional
from pathlib import Path

try:
    import pefile
    PEFILE_AVAILABLE = True
except ImportError:
    PEFILE_AVAILABLE = False
    logging.warning("pefile library not available. PE analysis will be limited.")

logger = logging.getLogger(__name__)


class ApplicationAnalyzer:
    """Analyzes Windows executable files to extract metadata and dependencies."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.pefile_available = PEFILE_AVAILABLE
    
    def analyze(self, exe_path: str) -> Dict[str, any]:
        """
        Analyze an EXE file and extract comprehensive metadata.
        
        Args:
            exe_path: Path to the EXE file to analyze
            
        Returns:
            Dictionary containing analysis results
            
        Raises:
            FileNotFoundError: If the EXE file doesn't exist
            ValueError: If the file is not a valid PE executable
        """
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"File not found: {exe_path}")
        
        logger.info(f"Analyzing {exe_path}")
        
        result = {
            "file_path": exe_path,
            "file_name": os.path.basename(exe_path),
            "file_size": os.path.getsize(exe_path),
            "file_size_mb": round(os.path.getsize(exe_path) / (1024 * 1024), 2),
        }
        
        # Basic file information
        result.update(self._get_file_info(exe_path))
        
        # PE-specific analysis if pefile is available
        if self.pefile_available:
            try:
                result.update(self._analyze_pe(exe_path))
            except Exception as e:
                logger.warning(f"PE analysis failed: {e}")
                result["pe_analysis_error"] = str(e)
        else:
            result["pe_analysis_available"] = False
        
        return result
    
    def _get_file_info(self, exe_path: str) -> Dict[str, any]:
        """Extract basic file information."""
        file_path = Path(exe_path)
        
        return {
            "directory": str(file_path.parent),
            "extension": file_path.suffix,
            "created_time": os.path.getctime(exe_path),
            "modified_time": os.path.getmtime(exe_path),
        }
    
    def _analyze_pe(self, exe_path: str) -> Dict[str, any]:
        """
        Perform detailed PE (Portable Executable) analysis.
        
        Args:
            exe_path: Path to the PE file
            
        Returns:
            Dictionary with PE-specific information
        """
        if not self.pefile_available:
            return {}
        
        pe = pefile.PE(exe_path)
        result = {}
        
        # Machine type
        result["machine_type"] = self._get_machine_type(pe.FILE_HEADER.Machine)
        result["is_64bit"] = pe.FILE_HEADER.Machine in [0x8664, 0xAA64]  # AMD64 or ARM64
        
        # Timestamps
        result["compilation_timestamp"] = pe.FILE_HEADER.TimeDateStamp
        
        # File version information
        if hasattr(pe, 'VS_VERSIONINFO'):
            result.update(self._extract_version_info(pe))
        
        # Import information (dependencies)
        result["imported_dlls"] = self._get_imported_dlls(pe)
        
        # Sections
        result["sections"] = [
            {
                "name": section.Name.decode('utf-8').strip('\x00'),
                "virtual_size": section.Misc_VirtualSize,
                "virtual_address": section.VirtualAddress,
            }
            for section in pe.sections
        ]
        
        # Entry point
        result["entry_point"] = hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
        
        # Image base
        result["image_base"] = hex(pe.OPTIONAL_HEADER.ImageBase)
        
        # Subsystem
        result["subsystem"] = self._get_subsystem(pe.OPTIONAL_HEADER.Subsystem)
        
        pe.close()
        return result
    
    def _get_machine_type(self, machine_value: int) -> str:
        """Convert machine type value to readable string."""
        machine_types = {
            0x014c: "I386",
            0x8664: "AMD64",
            0x0200: "IA64",
            0xAA64: "ARM64",
            0x01c4: "ARM",
        }
        return machine_types.get(machine_value, f"Unknown (0x{machine_value:04x})")
    
    def _get_subsystem(self, subsystem_value: int) -> str:
        """Convert subsystem value to readable string."""
        subsystems = {
            1: "Native",
            2: "Windows GUI",
            3: "Windows CUI (Console)",
            5: "OS/2 CUI",
            7: "POSIX CUI",
            9: "Windows CE GUI",
        }
        return subsystems.get(subsystem_value, f"Unknown ({subsystem_value})")
    
    def _extract_version_info(self, pe: 'pefile.PE') -> Dict[str, any]:
        """Extract version information from PE file."""
        version_info = {}
        
        try:
            if hasattr(pe, 'FileInfo'):
                for file_info in pe.FileInfo:
                    if hasattr(file_info, 'StringTable'):
                        for string_table in file_info.StringTable:
                            for entry in string_table.entries.items():
                                key = entry[0].decode('utf-8', errors='ignore')
                                value = entry[1].decode('utf-8', errors='ignore')
                                
                                # Map common keys
                                key_mapping = {
                                    'ProductName': 'product_name',
                                    'FileDescription': 'description',
                                    'FileVersion': 'file_version',
                                    'ProductVersion': 'product_version',
                                    'CompanyName': 'company_name',
                                    'LegalCopyright': 'copyright',
                                    'InternalName': 'internal_name',
                                    'OriginalFilename': 'original_filename',
                                }
                                
                                mapped_key = key_mapping.get(key, key.lower().replace(' ', '_'))
                                version_info[mapped_key] = value
        except Exception as e:
            logger.debug(f"Error extracting version info: {e}")
        
        return version_info
    
    def _get_imported_dlls(self, pe: 'pefile.PE') -> List[str]:
        """Extract list of imported DLLs (dependencies)."""
        imported_dlls = []
        
        try:
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    dll_name = entry.dll.decode('utf-8', errors='ignore')
                    imported_dlls.append(dll_name)
        except Exception as e:
            logger.debug(f"Error extracting imported DLLs: {e}")
        
        return imported_dlls
    
    def detect_installer_type(self, exe_path: str) -> str:
        """
        Attempt to detect the type of installer.
        
        Args:
            exe_path: Path to the EXE file
            
        Returns:
            String indicating installer type (e.g., "NSIS", "Inno Setup", "MSI", "Unknown")
        """
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"File not found: {exe_path}")
        
        # Read first few KB to detect signatures
        with open(exe_path, 'rb') as f:
            header = f.read(8192)
        
        # Check for common installer signatures
        if b'Nullsoft' in header or b'NSIS' in header:
            return "NSIS"
        elif b'Inno Setup' in header or b'InnoSetup' in header:
            return "Inno Setup"
        elif b'Wise Installation' in header:
            return "Wise Installer"
        elif b'InstallShield' in header:
            return "InstallShield"
        elif header[0:2] == b'MZ' and b'This program cannot be run in DOS mode' in header:
            # Basic PE executable, could be various types
            if self.pefile_available:
                try:
                    pe = pefile.PE(exe_path)
                    # Check for MSI-related imports
                    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                        for entry in pe.DIRECTORY_ENTRY_IMPORT:
                            dll_name = entry.dll.decode('utf-8', errors='ignore').lower()
                            if 'msi' in dll_name:
                                pe.close()
                                return "MSI-based"
                    pe.close()
                except:
                    pass
            return "PE Executable"
        
        return "Unknown"
    
    def generate_report(self, analysis_result: Dict[str, any], format: str = "text") -> str:
        """
        Generate a formatted report from analysis results.
        
        Args:
            analysis_result: Dictionary from analyze() method
            format: Output format - "text", "json", or "yaml"
            
        Returns:
            Formatted report string
        """
        if format == "json":
            import json
            return json.dumps(analysis_result, indent=2, default=str)
        elif format == "yaml":
            import yaml
            return yaml.dump(analysis_result, default_flow_style=False)
        else:  # text
            return self._generate_text_report(analysis_result)
    
    def _generate_text_report(self, data: Dict[str, any]) -> str:
        """Generate a human-readable text report."""
        lines = []
        lines.append("=" * 70)
        lines.append("APPLICATION ANALYSIS REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Basic information
        lines.append("BASIC INFORMATION")
        lines.append("-" * 70)
        lines.append(f"File Name:     {data.get('file_name', 'N/A')}")
        lines.append(f"File Path:     {data.get('file_path', 'N/A')}")
        lines.append(f"File Size:     {data.get('file_size_mb', 0)} MB")
        lines.append("")
        
        # Version information
        if 'product_name' in data or 'file_version' in data:
            lines.append("VERSION INFORMATION")
            lines.append("-" * 70)
            if 'product_name' in data:
                lines.append(f"Product Name:  {data['product_name']}")
            if 'file_version' in data:
                lines.append(f"File Version:  {data['file_version']}")
            if 'product_version' in data:
                lines.append(f"Product Ver:   {data['product_version']}")
            if 'company_name' in data:
                lines.append(f"Company:       {data['company_name']}")
            if 'description' in data:
                lines.append(f"Description:   {data['description']}")
            lines.append("")
        
        # Technical information
        if 'machine_type' in data:
            lines.append("TECHNICAL INFORMATION")
            lines.append("-" * 70)
            lines.append(f"Machine Type:  {data['machine_type']}")
            lines.append(f"64-bit:        {data.get('is_64bit', False)}")
            if 'subsystem' in data:
                lines.append(f"Subsystem:     {data['subsystem']}")
            lines.append("")
        
        # Dependencies
        if 'imported_dlls' in data and data['imported_dlls']:
            lines.append("DEPENDENCIES (Imported DLLs)")
            lines.append("-" * 70)
            for dll in data['imported_dlls'][:20]:  # Limit to first 20
                lines.append(f"  - {dll}")
            if len(data['imported_dlls']) > 20:
                lines.append(f"  ... and {len(data['imported_dlls']) - 20} more")
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)

"""
Folder Analyzer Module
Automatically analyzes installer folders and suggests package configuration.
Uses heuristic rules (no AI) to detect structure.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AnalyzedFile:
    """Represents an analyzed file in the package."""
    path: Path
    name: str
    size: int
    type: str  # 'installer', 'executable', 'database', 'config', 'archive', 'license', 'script'
    confidence: float  # 0.0 to 1.0
    suggested_purpose: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class FolderAnalysisResult:
    """Result of folder analysis."""
    main_installer: Optional[AnalyzedFile] = None
    dependencies: List[AnalyzedFile] = field(default_factory=list)
    standalone_executables: List[AnalyzedFile] = field(default_factory=list)
    config_files: List[AnalyzedFile] = field(default_factory=list)
    scripts: List[AnalyzedFile] = field(default_factory=list)
    archives: List[AnalyzedFile] = field(default_factory=list)
    license_files: List[AnalyzedFile] = field(default_factory=list)
    unknown_files: List[AnalyzedFile] = field(default_factory=list)
    confidence_score: float = 0.0
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class FolderAnalyzer:
    """Analyzes installer folders using heuristic rules."""
    
    # Known installer types and their patterns
    INSTALLER_PATTERNS = {
        'nsis': ['nullsoft installer'],
        'innosetup': ['inno setup'],
        'installshield': ['installshield'],
        'msi': ['.msi'],
        'wise': ['wise installer']
    }
    
    # Database installer patterns
    DATABASE_PATTERNS = ['firebird', 'mysql', 'postgres', 'oracle', 'mssql', 'sqlite']
    
    # License/dongle related patterns
    LICENSE_PATTERNS = ['hasp', 'sentinel', 'dongle', 'license', 'lic', 'key', 'activation']
    
    # Config file extensions
    CONFIG_EXTENSIONS = ['.ini', '.cfg', '.conf', '.config', '.def', '.xml', '.json']
    
    # Script extensions
    SCRIPT_EXTENSIONS = ['.bat', '.cmd', '.ps1', '.vbs']
    
    # Known helper tools
    HELPER_TOOLS = ['getip', 'username', 'sysinfo', 'regutil']
    
    def __init__(self):
        """Initialize folder analyzer."""
        logger.info("FolderAnalyzer initialized")
    
    def analyze_folder(self, folder_path: str) -> FolderAnalysisResult:
        """
        Analyze a folder containing installer package.
        
        Args:
            folder_path: Path to folder to analyze
            
        Returns:
            FolderAnalysisResult with detected components
        """
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder not found or not a directory: {folder_path}")
        
        logger.info(f"Analyzing folder: {folder_path}")
        
        result = FolderAnalysisResult()
        
        # Scan all files
        all_files = self._scan_files(folder)
        logger.info(f"Found {len(all_files)} files")
        
        # Classify files
        classified = self._classify_files(all_files)
        
        # Detect main installer
        result.main_installer = self._detect_main_installer(classified['installers'])
        
        # Detect dependencies (databases, runtimes)
        result.dependencies = self._detect_dependencies(classified['installers'], result.main_installer)
        
        # Detect standalone executables (potential replacements)
        result.standalone_executables = self._detect_standalone_executables(
            classified['executables'], 
            result.main_installer
        )
        
        # Other classifications
        result.config_files = classified['configs']
        result.scripts = classified['scripts']
        result.archives = classified['archives']
        result.license_files = classified['licenses']
        result.unknown_files = classified['unknown']
        
        # Calculate confidence and generate suggestions
        result.confidence_score = self._calculate_confidence(result)
        result.warnings = self._generate_warnings(result)
        result.suggestions = self._generate_suggestions(result)
        
        logger.info(f"Analysis complete. Confidence: {result.confidence_score:.2f}")
        
        return result
    
    def _scan_files(self, folder: Path) -> List[Path]:
        """Recursively scan all files in folder."""
        files = []
        for root, dirs, filenames in os.walk(folder):
            for filename in filenames:
                file_path = Path(root) / filename
                # Skip hidden files and Mac metadata
                if not filename.startswith('.') and filename != 'Thumbs.db':
                    files.append(file_path)
        return files
    
    def _classify_files(self, files: List[Path]) -> Dict[str, List[AnalyzedFile]]:
        """Classify files into categories."""
        classified = {
            'installers': [],
            'executables': [],
            'configs': [],
            'scripts': [],
            'archives': [],
            'licenses': [],
            'unknown': []
        }
        
        for file_path in files:
            analyzed = self._analyze_file(file_path)
            
            if analyzed.type == 'installer':
                classified['installers'].append(analyzed)
            elif analyzed.type == 'executable':
                classified['executables'].append(analyzed)
            elif analyzed.type == 'config':
                classified['configs'].append(analyzed)
            elif analyzed.type == 'script':
                classified['scripts'].append(analyzed)
            elif analyzed.type == 'archive':
                classified['archives'].append(analyzed)
            elif analyzed.type == 'license':
                classified['licenses'].append(analyzed)
            else:
                classified['unknown'].append(analyzed)
        
        return classified
    
    def _analyze_file(self, file_path: Path) -> AnalyzedFile:
        """Analyze a single file."""
        name = file_path.name.lower()
        size = file_path.stat().st_size
        ext = file_path.suffix.lower()
        
        analyzed = AnalyzedFile(
            path=file_path,
            name=file_path.name,
            size=size,
            type='unknown',
            confidence=0.5,
            suggested_purpose='Unknown'
        )
        
        # Detect file type based on extension and name patterns
        
        # Scripts
        if ext in self.SCRIPT_EXTENSIONS:
            analyzed.type = 'script'
            analyzed.confidence = 0.9
            analyzed.suggested_purpose = 'Installation script or helper'
            return analyzed
        
        # Config files
        if ext in self.CONFIG_EXTENSIONS:
            analyzed.type = 'config'
            analyzed.confidence = 0.9
            analyzed.suggested_purpose = 'Configuration file'
            return analyzed
        
        # Archives
        if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            analyzed.type = 'archive'
            analyzed.confidence = 0.9
            
            # Check if it's license-related
            if any(pattern in name for pattern in self.LICENSE_PATTERNS):
                analyzed.type = 'license'
                analyzed.suggested_purpose = 'License/dongle drivers'
            else:
                analyzed.suggested_purpose = 'Archive (may contain additional components)'
            
            return analyzed
        
        # MSI installers
        if ext == '.msi':
            analyzed.type = 'installer'
            analyzed.confidence = 1.0
            analyzed.suggested_purpose = 'MSI installer'
            analyzed.metadata['installer_type'] = 'msi'
            return analyzed
        
        # Executables (.exe)
        if ext == '.exe':
            # Check if it's a known installer type
            # This would require reading PE headers or using `file` command
            # For now, use heuristics based on name and size
            
            # Large exe with "install", "setup" in name = likely installer
            if any(keyword in name for keyword in ['install', 'setup', 'deploy']) and size > 1_000_000:
                analyzed.type = 'installer'
                analyzed.confidence = 0.8
                analyzed.suggested_purpose = 'Main installer'
                return analyzed
            
            # Database patterns
            if any(db in name for db in self.DATABASE_PATTERNS):
                analyzed.type = 'installer'
                analyzed.confidence = 0.85
                analyzed.suggested_purpose = 'Database installer (dependency)'
                analyzed.metadata['is_dependency'] = True
                return analyzed
            
            # Helper tools
            if any(tool in name for tool in self.HELPER_TOOLS):
                analyzed.type = 'executable'
                analyzed.confidence = 0.7
                analyzed.suggested_purpose = 'Helper utility'
                return analyzed
            
            # Standalone executable (medium size, not obviously an installer)
            if 1_000_000 < size < 50_000_000:
                analyzed.type = 'executable'
                analyzed.confidence = 0.6
                analyzed.suggested_purpose = 'Standalone executable (possible replacement file)'
                return analyzed
            
            # Very large exe = probably main installer
            if size > 50_000_000:
                analyzed.type = 'installer'
                analyzed.confidence = 0.75
                analyzed.suggested_purpose = 'Main installer (large package)'
                return analyzed
            
            # Small exe = utility or component
            analyzed.type = 'executable'
            analyzed.confidence = 0.5
            analyzed.suggested_purpose = 'Executable utility'
            return analyzed
        
        return analyzed
    
    def _detect_main_installer(self, installers: List[AnalyzedFile]) -> Optional[AnalyzedFile]:
        """Detect the main installer from list of installers."""
        if not installers:
            return None
        
        # Rule 1: Largest installer is usually the main one
        main = max(installers, key=lambda x: x.size)
        
        # Rule 2: Boost confidence if name contains "install" or "setup"
        if any(keyword in main.name.lower() for keyword in ['install', 'setup']):
            main.confidence = min(main.confidence + 0.15, 1.0)
        
        main.suggested_purpose = 'Main installer'
        logger.info(f"Detected main installer: {main.name} ({main.size / 1_000_000:.1f} MB)")
        
        return main
    
    def _detect_dependencies(
        self, 
        installers: List[AnalyzedFile], 
        main_installer: Optional[AnalyzedFile]
    ) -> List[AnalyzedFile]:
        """Detect dependency installers."""
        if not main_installer:
            return installers
        
        dependencies = []
        
        for installer in installers:
            if installer == main_installer:
                continue
            
            # Database installers are dependencies
            if installer.metadata.get('is_dependency'):
                installer.suggested_purpose = 'Dependency installer'
                dependencies.append(installer)
            # Smaller installers are likely dependencies
            elif installer.size < main_installer.size * 0.3:
                installer.suggested_purpose = 'Dependency installer (likely)'
                installer.confidence = 0.7
                dependencies.append(installer)
        
        return dependencies
    
    def _detect_standalone_executables(
        self, 
        executables: List[AnalyzedFile],
        main_installer: Optional[AnalyzedFile]
    ) -> List[AnalyzedFile]:
        """Detect standalone executables that may need to be copied after install."""
        standalone = []
        
        for exe in executables:
            # Medium-sized executables that aren't helper tools
            if 5_000_000 < exe.size < 50_000_000:
                exe.suggested_purpose = 'Possible replacement file (copy after install)'
                exe.confidence = 0.65
                standalone.append(exe)
        
        return standalone
    
    def _calculate_confidence(self, result: FolderAnalysisResult) -> float:
        """Calculate overall confidence score."""
        scores = []
        
        if result.main_installer:
            scores.append(result.main_installer.confidence)
        
        if result.dependencies:
            scores.extend([d.confidence for d in result.dependencies])
        
        if result.standalone_executables:
            scores.extend([s.confidence for s in result.standalone_executables])
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _generate_warnings(self, result: FolderAnalysisResult) -> List[str]:
        """Generate warnings about potential issues."""
        warnings = []
        
        if not result.main_installer:
            warnings.append("No main installer detected. Manual configuration required.")
        
        if result.standalone_executables:
            warnings.append(
                f"Found {len(result.standalone_executables)} standalone executable(s). "
                "These may need to be copied after installation."
            )
        
        if len(result.dependencies) > 1:
            warnings.append(
                f"Found {len(result.dependencies)} dependencies. "
                "Verify installation order."
            )
        
        if result.confidence_score < 0.6:
            warnings.append(
                "Low confidence in analysis. Please review and adjust configuration manually."
            )
        
        return warnings
    
    def _generate_suggestions(self, result: FolderAnalysisResult) -> List[str]:
        """Generate suggestions for user."""
        suggestions = []
        
        if result.main_installer:
            suggestions.append(
                f"Main installer detected: {result.main_installer.name}. "
                "Test silent install arguments."
            )
        
        if result.dependencies:
            suggestions.append(
                "Install dependencies before main application for best results."
            )
        
        if result.standalone_executables:
            for exe in result.standalone_executables:
                suggestions.append(
                    f"Consider adding post-install file replacement for: {exe.name}"
                )
        
        if result.scripts:
            suggestions.append(
                f"Found {len(result.scripts)} script(s). "
                "Review for installation commands and arguments."
            )
        
        if result.config_files:
            suggestions.append(
                f"Found {len(result.config_files)} config file(s). "
                "Consider copying these after installation."
            )
        
        return suggestions
    
    def generate_yaml_draft(self, result: FolderAnalysisResult, app_name: str) -> str:
        """Generate draft YAML configuration from analysis."""
        lines = []
        
        lines.append(f"application:")
        lines.append(f"  name: \"{app_name}\"")
        lines.append(f"  version: \"1.0.0\"  # TODO: Update version")
        lines.append(f"  publisher: \"Unknown\"  # TODO: Update publisher")
        lines.append(f"")
        
        lines.append(f"installers:")
        
        # Add dependencies first
        for dep in result.dependencies:
            lines.append(f"  - name: \"{dep.name}\"")
            lines.append(f"    file: \"{dep.name}\"")
            lines.append(f"    silent_args: \"\"  # TODO: Add silent install arguments")
            lines.append(f"    optional: false")
            lines.append(f"")
        
        # Add main installer
        if result.main_installer:
            lines.append(f"  - name: \"{result.main_installer.name}\"")
            lines.append(f"    file: \"{result.main_installer.name}\"")
            lines.append(f"    silent_args: \"\"  # TODO: Add silent install arguments")
            
            if result.dependencies:
                dep_names = [f'"{dep.name}"' for dep in result.dependencies]
                lines.append(f"    depends_on: [{', '.join(dep_names)}]")
            
            lines.append(f"")
        
        # Add post-install section if standalone executables found
        if result.standalone_executables:
            lines.append(f"post_install:")
            lines.append(f"  file_replacements:")
            for exe in result.standalone_executables:
                lines.append(f"    - source: \"{exe.name}\"")
                lines.append(f"      destination: \"\"  # TODO: Specify destination path")
                lines.append(f"      backup: true")
            lines.append(f"")
        
        # Add config files section
        if result.config_files:
            if not result.standalone_executables:
                lines.append(f"post_install:")
            lines.append(f"  file_copies:")
            for cfg in result.config_files:
                lines.append(f"    - source: \"{cfg.name}\"")
                lines.append(f"      destination: \"\"  # TODO: Specify destination path")
            lines.append(f"")
        
        return "\n".join(lines)

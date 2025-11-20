"""
Application Profile Models
Data structures for application configuration and metadata.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


@dataclass
class Installer:
    """Represents a single installer in a package."""
    name: str
    file: str  # Relative path to installer file
    silent_args: str
    wait_for_completion: bool = True
    timeout: int = 600
    depends_on: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'file': self.file,
            'silent_args': self.silent_args,
            'wait_for_completion': self.wait_for_completion,
            'timeout': self.timeout,
            'depends_on': self.depends_on
        }


@dataclass
class DetectionRule:
    """Represents a detection rule for the application."""
    type: Literal["file", "registry", "process", "script"]
    path: Optional[str] = None
    check_version: bool = False
    min_version: Optional[str] = None
    
    # Registry-specific fields
    hive: Optional[str] = None  # HKLM, HKCU, etc.
    value: Optional[str] = None
    operator: Optional[Literal["Exists", "Equals", "GreaterOrEqual", "LessThan"]] = None
    expected: Optional[str] = None
    
    # Process-specific fields
    process_name: Optional[str] = None
    required: bool = True
    
    # Script-specific fields
    script_content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {'type': self.type}
        if self.path:
            result['path'] = self.path
        if self.check_version:
            result['check_version'] = True
            result['min_version'] = self.min_version
        if self.hive:
            result['hive'] = self.hive
        if self.value:
            result['value'] = self.value
        if self.operator:
            result['operator'] = self.operator
        if self.expected:
            result['expected'] = self.expected
        if self.process_name:
            result['process_name'] = self.process_name
        if not self.required:
            result['required'] = False
        if self.script_content:
            result['script_content'] = self.script_content
        return result


@dataclass
class UninstallStrategy:
    """Defines how the application should be uninstalled."""
    strategy: Literal["standard", "force", "multi"] = "multi"
    
    # Standard uninstall settings
    method: Literal["registry", "command"] = "registry"
    command: Optional[str] = None
    wait: bool = True
    
    # Force removal settings
    force_enabled: bool = True
    kill_processes: List[str] = field(default_factory=list)
    remove_paths: List[str] = field(default_factory=list)
    remove_registry: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy': self.strategy,
            'method': self.method,
            'command': self.command,
            'wait': self.wait,
            'force_enabled': self.force_enabled,
            'kill_processes': self.kill_processes,
            'remove_paths': self.remove_paths,
            'remove_registry': self.remove_registry
        }


@dataclass
class Shortcut:
    """Defines a shortcut to create."""
    name: str
    target: str
    locations: List[Literal["Desktop", "StartMenu"]]
    icon: Optional[str] = None
    arguments: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'name': self.name,
            'target': self.target,
            'locations': self.locations
        }
        if self.icon:
            result['icon'] = self.icon
        if self.arguments:
            result['arguments'] = self.arguments
        if self.description:
            result['description'] = self.description
        return result


@dataclass
class Assignment:
    """Defines an Intune assignment."""
    intent: Literal["available", "required", "uninstall"]
    target_groups: List[str]  # Azure AD group IDs or names
    notification: bool = True
    deadline: Optional[datetime] = None
    restart_grace_period_minutes: Optional[int] = None
    available_in_company_portal: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'intent': self.intent,
            'target_groups': self.target_groups,
            'notification': self.notification,
            'available_in_company_portal': self.available_in_company_portal
        }
        if self.deadline:
            result['deadline'] = self.deadline.isoformat()
        if self.restart_grace_period_minutes:
            result['restart_grace_period_minutes'] = self.restart_grace_period_minutes
        return result


@dataclass
class CompanyPortalMetadata:
    """Company Portal display information."""
    description: str = ""
    icon_path: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    information_url: Optional[str] = None
    privacy_url: Optional[str] = None
    featured: bool = False
    category: Optional[str] = "Productivity"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'description': self.description,
            'icon_path': self.icon_path,
            'screenshots': self.screenshots,
            'information_url': self.information_url,
            'privacy_url': self.privacy_url,
            'featured': self.featured,
            'category': self.category
        }


@dataclass
class IntuneRequirements:
    """System requirements for the application."""
    minimum_os: str = "1809"  # Windows 10 version
    architecture: Literal["x86", "x64", "arm64"] = "x64"
    minimum_disk_space_mb: int = 100
    minimum_memory_mb: int = 512
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'minimum_os': self.minimum_os,
            'architecture': self.architecture,
            'minimum_disk_space_mb': self.minimum_disk_space_mb,
            'minimum_memory_mb': self.minimum_memory_mb
        }


@dataclass
class IntuneSettings:
    """Intune-specific settings."""
    install_command: str = "powershell.exe -ExecutionPolicy Bypass -File install.ps1"
    uninstall_command: str = "powershell.exe -ExecutionPolicy Bypass -File uninstall.ps1"
    install_time_minutes: int = 15
    allow_available_uninstall: bool = True
    requirements: IntuneRequirements = field(default_factory=IntuneRequirements)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'install_command': self.install_command,
            'uninstall_command': self.uninstall_command,
            'install_time_minutes': self.install_time_minutes,
            'allow_available_uninstall': self.allow_available_uninstall,
            'requirements': self.requirements.to_dict()
        }


@dataclass
class TestingConfig:
    """Testing configuration."""
    sandbox_enabled: bool = True
    verify_install: bool = True
    verify_detection: bool = True
    verify_shortcuts: bool = True
    verify_uninstall: bool = True
    verify_detection_after_uninstall: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sandbox_enabled': self.sandbox_enabled,
            'verify_install': self.verify_install,
            'verify_detection': self.verify_detection,
            'verify_shortcuts': self.verify_shortcuts,
            'verify_uninstall': self.verify_uninstall,
            'verify_detection_after_uninstall': self.verify_detection_after_uninstall
        }


@dataclass
class ApplicationProfile:
    """Complete application profile for packaging and deployment."""
    # Basic metadata
    name: str
    version: str
    publisher: str
    description: str = ""
    
    # Installers
    installers: List[Installer] = field(default_factory=list)
    
    # Detection
    detection_method: Literal["file", "registry", "comprehensive", "custom"] = "comprehensive"
    detection_rules: List[DetectionRule] = field(default_factory=list)
    custom_detection_script: Optional[str] = None
    
    # Uninstall
    uninstall: UninstallStrategy = field(default_factory=UninstallStrategy)
    
    # Shortcuts
    shortcuts: List[Shortcut] = field(default_factory=list)
    auto_create_shortcuts: bool = True
    
    # Intune deployment
    intune: IntuneSettings = field(default_factory=IntuneSettings)
    assignments: List[Assignment] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # App names or IDs
    supersedes: List[str] = field(default_factory=list)  # App names or IDs to replace
    
    # Company Portal
    company_portal: CompanyPortalMetadata = field(default_factory=CompanyPortalMetadata)
    
    # Testing
    testing: TestingConfig = field(default_factory=TestingConfig)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            'application': {
                'name': self.name,
                'version': self.version,
                'publisher': self.publisher,
                'description': self.description
            },
            'installers': [i.to_dict() for i in self.installers],
            'detection': {
                'method': self.detection_method,
                'rules': [r.to_dict() for r in self.detection_rules],
                'custom_script': self.custom_detection_script
            },
            'uninstall': self.uninstall.to_dict(),
            'shortcuts': {
                'auto_create': self.auto_create_shortcuts,
                'locations': [s.to_dict() for s in self.shortcuts]
            },
            'intune': self.intune.to_dict(),
            'assignments': [a.to_dict() for a in self.assignments],
            'dependencies': self.dependencies,
            'supersedence': self.supersedes,
            'company_portal': self.company_portal.to_dict(),
            'testing': self.testing.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationProfile':
        """Create profile from dictionary."""
        app = data.get('application', {})
        
        # Parse installers
        installers = [
            Installer(**inst) for inst in data.get('installers', [])
        ]
        
        # Parse detection rules
        detection = data.get('detection', {})
        detection_rules = [
            DetectionRule(**rule) for rule in detection.get('rules', [])
        ]
        
        # Parse uninstall strategy
        uninstall_data = data.get('uninstall', {})
        if uninstall_data:
            # Flatten nested structure from YAML
            strategy = uninstall_data.get('strategy', 'multi')
            standard_data = uninstall_data.get('standard', {})
            force_data = uninstall_data.get('force', {})
            
            uninstall = UninstallStrategy(
                strategy=strategy,
                method=standard_data.get('method', 'registry'),
                command=standard_data.get('command'),
                wait=standard_data.get('wait', True),
                force_enabled=force_data.get('enabled', True),
                kill_processes=force_data.get('kill_processes', []),
                remove_paths=force_data.get('remove_paths', []),
                remove_registry=force_data.get('remove_registry', [])
            )
        else:
            uninstall = UninstallStrategy()
        
        # Parse shortcuts
        shortcuts_data = data.get('shortcuts', {})
        shortcuts = [
            Shortcut(**sc) for sc in shortcuts_data.get('locations', [])
        ]
        
        # Parse Intune settings
        intune_data = data.get('intune', {})
        if intune_data:
            # Parse nested requirements
            req_data = intune_data.get('requirements', {})
            requirements = IntuneRequirements(**req_data) if req_data else IntuneRequirements()
            
            # Parse assignments from intune.assignments
            intune_assignments = intune_data.get('assignments', [])
            
            intune = IntuneSettings(
                install_command=intune_data.get('install_command', 'powershell.exe -ExecutionPolicy Bypass -File install.ps1'),
                uninstall_command=intune_data.get('uninstall_command', 'powershell.exe -ExecutionPolicy Bypass -File uninstall.ps1'),
                install_time_minutes=intune_data.get('install_time_minutes', 15),
                allow_available_uninstall=intune_data.get('allow_available_uninstall', True),
                requirements=requirements
            )
        else:
            intune_assignments = []
            intune = IntuneSettings()
        
        # Parse assignments (combine root level and intune level)
        root_assignments = data.get('assignments', [])
        all_assignments = root_assignments + intune_assignments
        assignments = [
            Assignment(**assign) for assign in all_assignments
        ]
        
        # Parse Company Portal metadata
        cp_data = data.get('company_portal', {})
        company_portal = CompanyPortalMetadata(**cp_data) if cp_data else CompanyPortalMetadata()
        
        # Parse testing config
        test_data = data.get('testing', {})
        testing = TestingConfig(**test_data) if test_data else TestingConfig()
        
        return cls(
            name=app.get('name', ''),
            version=app.get('version', ''),
            publisher=app.get('publisher', ''),
            description=app.get('description', ''),
            installers=installers,
            detection_method=detection.get('method', 'comprehensive'),
            detection_rules=detection_rules,
            custom_detection_script=detection.get('custom_script'),
            uninstall=uninstall,
            shortcuts=shortcuts,
            auto_create_shortcuts=shortcuts_data.get('auto_create', True),
            intune=intune,
            assignments=assignments,
            dependencies=data.get('dependencies', []),
            supersedes=data.get('supersedence', []),
            company_portal=company_portal,
            testing=testing
        )

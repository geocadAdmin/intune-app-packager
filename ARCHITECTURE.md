# Intune App Packager - Architecture

## Overview

Complete Intune application packaging and deployment solution with zero manual Intune portal interaction required.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron + React GUI                      │
│  ┌────────────┬──────────────┬─────────────┬──────────────┐ │
│  │ App Setup  │ Script Gen   │ Group Select│ Deployment   │ │
│  │ Wizard     │ & Preview    │ (Azure AD)  │ Monitor      │ │
│  └────────────┴──────────────┴─────────────┴──────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ IPC / REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Python Backend (FastAPI)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Workflow Orchestrator                                  │ │
│  │  (analyze → generate → build → test → deploy → monitor)│ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────┐ │
│  │ Enhanced │ Script   │ Package  │ Sandbox  │ Intune    │ │
│  │ Analyzer │ Generator│ Builder  │ Tester   │ API Client│ │
│  └──────────┴──────────┴──────────┴──────────┴───────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼──────┐  ┌───────▼────────┐
│ IntuneWinAppUtil│  │   Windows   │  │ Microsoft Graph│
│      .exe       │  │   Sandbox   │  │   API (Intune) │
└─────────────────┘  └─────────────┘  └────────────────┘
```

## Technology Stack

### Frontend (GUI)
- **Framework:** Electron 28+
- **UI Library:** React 18+
- **State Management:** Zustand or Redux Toolkit
- **Styling:** Tailwind CSS + shadcn/ui
- **Forms:** React Hook Form + Zod validation
- **API Client:** Axios

### Backend
- **Runtime:** Python 3.8+
- **API Framework:** FastAPI
- **Authentication:** MSAL (Microsoft Authentication Library)
- **Config:** PyYAML
- **PE Analysis:** pefile
- **Async:** asyncio for Graph API calls

### Communication
- **GUI ↔ Backend:** REST API (FastAPI server)
- **Electron IPC:** For file operations, subprocess management

### Microsoft Integration
- **Authentication:** Azure AD (OAuth 2.0)
- **API:** Microsoft Graph API v1.0
- **Scopes Required:**
  - `DeviceManagementApps.ReadWrite.All`
  - `Group.Read.All`
  - `DeviceManagementManagedDevices.Read.All`

## Core Modules

### 1. Enhanced Analyzer (`analyzer.py`)

**Purpose:** Deep analysis of installers to extract metadata for script generation.

**Capabilities:**
- PE executable analysis (version, publisher, architecture)
- Installer type detection (NSIS, InnoSetup, MSI, etc.)
- Predict installation paths
- Detect registry keys
- Find shortcuts
- Identify dependencies

**Output:** Application profile with all detected metadata

### 2. Script Generator (`script_generator.py`)

**Purpose:** Generate PowerShell scripts from templates using analyzed data.

**Templates:**
- `install.ps1` - Handles single/multi-installer scenarios
- `uninstall.ps1` - Multi-strategy uninstall (standard → force)
- `detection.ps1` - Comprehensive detection (file + registry + version)

**Features:**
- Template variable substitution
- Conditional logic based on installer type
- Logging and error handling built-in
- Intune exit code compliance

### 3. Template Manager (`template_manager.py`)

**Purpose:** Manage script templates and allow customization.

**Template Types:**
- Single installer
- Multi-installer (e.g., Firebird + EWMapa)
- Portable apps (no installer, just copy)
- MSI-based
- Custom (user-defined)

**Storage:** `templates/` directory with Jinja2 syntax

### 4. Package Builder (`package_builder.py`)

**Purpose:** Create complete Intune package with all required files.

**Output Structure:**
```
package/
├── installers/
│   ├── Firebird-3.0.exe
│   └── EWMapa-Setup.exe
├── install.ps1
├── uninstall.ps1
├── detection.ps1
└── app-icon.png
```

**Then:** Wraps with IntuneWinAppUtil.exe → `.intunewin`

### 5. Intune API Client (`intune_api.py`)

**Purpose:** Complete automation of Intune operations via Microsoft Graph API.

**Core Operations:**

#### Authentication
```python
async def authenticate(tenant_id, client_id, client_secret=None):
    """Interactive or service principal auth"""
```

#### App Management
```python
async def upload_intunewin(file_path, app_metadata):
    """Upload .intunewin to Azure Storage"""

async def create_win32_app(app_config):
    """Create Win32 app in Intune"""
    
async def update_app(app_id, new_version_config):
    """Update existing app"""
```

#### Group & Assignment
```python
async def list_azure_groups(search_query=None):
    """Get all Azure AD groups for selection"""
    
async def assign_app(app_id, assignments):
    """Assign to groups with deployment settings"""
    # assignments = [
    #   {
    #     "target": "group_id",
    #     "intent": "available" | "required" | "uninstall",
    #     "settings": {...}
    #   }
    # ]
```

#### Advanced Features
```python
async def set_dependencies(app_id, dependency_ids):
    """Set app dependencies (install order)"""
    
async def set_supersedence(app_id, superseded_app_ids):
    """Replace old app versions"""
    
async def get_deployment_status(app_id):
    """Monitor deployment progress"""
```

### 6. Deployment Manager (`deployment_manager.py`)

**Purpose:** Orchestrate complete deployment workflow.

**Workflow:**
```python
async def deploy_app(config):
    1. Validate app config
    2. Build package
    3. (Optional) Test in Sandbox
    4. Upload to Intune
    5. Configure app metadata
    6. Assign to groups
    7. Set dependencies/supersedence
    8. Monitor initial deployment
    9. Return deployment summary
```

### 7. Sandbox Tester (`sandbox_tester.py`)

**Purpose:** Automated testing in Windows Sandbox before production deployment.

**Test Sequence:**
1. Create Sandbox config (`.wsb` file)
2. Copy package to Sandbox
3. Run `install.ps1`
4. Verify:
   - Exit code = 0
   - Files created at expected paths
   - Registry keys present
   - Shortcuts created
   - Detection script returns 0
5. Run `uninstall.ps1`
6. Verify complete removal
7. Generate test report

**Note:** Works only on Windows 10/11 Pro with Sandbox enabled.

### 8. Application Profile Model (`models/app_profile.py`)

**Purpose:** Standardized data model for application configuration.

```python
@dataclass
class Installer:
    name: str
    file_path: str
    silent_args: str
    depends_on: List[str] = []
    timeout: int = 600
    wait_for_completion: bool = True

@dataclass
class DetectionRule:
    type: Literal["file", "registry", "script"]
    path: str
    check_version: bool = False
    min_version: Optional[str] = None
    
@dataclass
class Assignment:
    intent: Literal["available", "required", "uninstall"]
    target_groups: List[str]
    notification: bool = True
    deadline: Optional[datetime] = None
    
@dataclass
class ApplicationProfile:
    name: str
    version: str
    publisher: str
    installers: List[Installer]
    detection: List[DetectionRule]
    uninstall_strategy: str
    shortcuts: List[dict]
    assignments: List[Assignment]
    dependencies: List[str] = []
    supersedes: List[str] = []
    
    # Company Portal metadata
    description: str = ""
    icon_path: Optional[str] = None
    screenshots: List[str] = []
    privacy_url: Optional[str] = None
    information_url: Optional[str] = None
```

## User Workflow

### GUI Workflow (Primary)

```
1. Launch App → Authenticate with Azure AD
   ↓
2. Create New App → Wizard Opens
   ↓
3. Add Installers (drag & drop or browse)
   - For multi-installer: set order & dependencies
   ↓
4. Auto-Analyze → Detection rules suggested
   - User can modify/add custom rules
   ↓
5. Generate Scripts → Preview in editor
   - User can customize if needed
   ↓
6. Configure Intune Settings
   - Company Portal: description, icon, screenshots
   - Assignment: select groups from dropdown
   - Deployment type: Required/Available/Uninstall
   - Dependencies: select from existing apps
   - Supersedence: select apps to replace
   ↓
7. (Optional) Test in Sandbox
   - Runs automated tests
   - Shows pass/fail results
   ↓
8. Deploy to Intune
   - Progress bar shows: build → upload → assign
   - Real-time status updates
   ↓
9. Monitor Deployment
   - Dashboard shows install status per device/user
   - Drill down into failures
```

### CLI Workflow (Advanced/Automation)

```bash
# Create app profile interactively
intune-packager init-app --name "EWMapa" --wizard

# Or from config file
intune-packager deploy \
  --config ewmapa.yml \
  --test-sandbox \
  --assign-groups "IT-Dept,Sales" \
  --mode available \
  --monitor

# Update existing app
intune-packager update \
  --config ewmapa-v2.2.yml \
  --supersede "EWMapa 2.1.0"
```

## Configuration File Format

```yaml
application:
  name: "EWMapa"
  version: "2.1.0"
  publisher: "YourCompany"
  description: "Enterprise mapping application"
  
installers:
  - name: "Firebird Database"
    file: "installers/Firebird-3.0.exe"
    silent_args: "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
    wait_for_completion: true
    timeout: 600
    
  - name: "EWMapa Application"
    file: "installers/EWMapa-Setup.exe"
    silent_args: "/S"
    depends_on: ["Firebird Database"]
    wait_for_completion: true
    timeout: 300

detection:
  method: "comprehensive"
  rules:
    - type: "file"
      path: "C:\\Program Files\\EWMapa\\EWMapa.exe"
      check_version: true
      min_version: "2.1.0"
      
    - type: "registry"
      hive: "HKLM"
      path: "SOFTWARE\\EWMapa"
      value: "Version"
      operator: "GreaterOrEqual"
      expected: "2.1.0"
      
    - type: "registry"
      hive: "HKLM"
      path: "SOFTWARE\\Firebird\\Firebird Server\\Instances"
      value: "DefaultInstance"
      operator: "Exists"

uninstall:
  strategy: "multi"  # standard, force, multi
  standard:
    method: "registry"  # Use UninstallString from registry
    wait: true
  force:
    enabled: true
    kill_processes:
      - "EWMapa.exe"
      - "fbserver.exe"
    remove_paths:
      - "C:\\Program Files\\EWMapa"
      - "C:\\Program Files\\Firebird"
    remove_registry:
      - "HKLM:\\SOFTWARE\\EWMapa"
      - "HKLM:\\SOFTWARE\\Firebird"

shortcuts:
  auto_create: true
  locations:
    - name: "EWMapa"
      target: "C:\\Program Files\\EWMapa\\EWMapa.exe"
      locations: ["Desktop", "StartMenu"]
      icon: "C:\\Program Files\\EWMapa\\EWMapa.exe,0"

company_portal:
  description: |
    EWMapa is an enterprise mapping and geospatial analysis tool.
    
    Features:
    - Advanced mapping capabilities
    - Real-time data visualization
    - Enterprise database integration
  
  icon: "assets/ewmapa-icon.png"
  screenshots:
    - "assets/screenshot1.png"
    - "assets/screenshot2.png"
  
  information_url: "https://yourcompany.com/ewmapa"
  privacy_url: "https://yourcompany.com/privacy"
  
  featured: true
  category: "Productivity"

intune:
  install_command: "powershell.exe -ExecutionPolicy Bypass -File install.ps1"
  uninstall_command: "powershell.exe -ExecutionPolicy Bypass -File uninstall.ps1"
  install_time_minutes: 15
  allow_available_uninstall: true
  
  requirements:
    minimum_os: "1809"  # Windows 10 1809
    architecture: "x64"
    minimum_disk_space_mb: 500
    minimum_memory_mb: 2048
  
  assignments:
    - intent: "available"
      target_groups:
        - "IT-Department"
        - "Sales-Team"
      notification: true
      available_in_company_portal: true
      
    - intent: "required"
      target_groups:
        - "Accounting-Team"
      notification: true
      deadline: "2025-12-01T00:00:00Z"
      restart_grace_period_minutes: 1440
      
  dependencies:
    - name: ".NET Framework 4.8"
      type: "dependency"
      
  supersedence:
    - app_name: "EWMapa 2.0.0"
      uninstall_previous: true
    - app_name: "EWMapa 1.5.0"
      uninstall_previous: true

testing:
  sandbox_enabled: true
  verify_install: true
  verify_detection: true
  verify_shortcuts: true
  verify_uninstall: true
  verify_detection_after_uninstall: true
```

## Security Considerations

### Authentication
- Use Azure AD service principal for automation
- Interactive browser flow for GUI users
- Token refresh handled automatically
- Tokens stored encrypted in system keychain

### Permissions
- Minimum required Graph API permissions
- Scope validation before operations
- Audit logging of all Intune changes

### Package Security
- Validate installer signatures
- Scan for malware (optional integration)
- Hash verification for installers

## Deployment Phases

### Phase 1: Core Functionality (Current Sprint)
- ✅ Basic project structure
- ✅ Enhanced analyzer
- ✅ Script generator with templates
- ✅ Package builder
- ✅ Intune API client (basic upload)

### Phase 2: GUI Development
- Electron + React setup
- Main app workflow UI
- Group selector
- Deployment monitor
- Settings panel

### Phase 3: Advanced Features
- Windows Sandbox testing
- Deployment analytics
- Multi-tenant support
- Template marketplace
- CI/CD integration

### Phase 4: Enterprise Features
- Role-based access control
- Approval workflows
- Package repository
- Automated updates
- Advanced reporting

## Development Guidelines

### Code Organization
```
src/
├── intune_packager/          # Python backend
│   ├── api/                  # FastAPI endpoints
│   ├── core/                 # Core business logic
│   ├── models/               # Data models
│   ├── services/             # External services (Graph API)
│   └── templates/            # PowerShell templates
│
├── gui/                      # Electron frontend
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API clients
│   │   ├── store/            # State management
│   │   └── utils/            # Utilities
│   └── electron/             # Electron main process
│
└── tests/                    # Tests
    ├── backend/
    └── frontend/
```

### Testing Strategy
- Backend: pytest with mocking Graph API
- Frontend: Jest + React Testing Library
- E2E: Playwright for full workflow tests
- Sandbox testing for real deployment validation

### Build & Distribution
- Backend: PyInstaller for standalone executable
- Frontend: electron-builder for installers
- Package as single installer: MSI for Windows, DMG for macOS

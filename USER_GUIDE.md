# Intune App Packager - Complete User Guide

## Overview

Intune App Packager is a comprehensive solution for packaging Windows applications and deploying them to Microsoft Intune **without any manual work in the Intune portal**. Everything is done through our application - from packaging to deployment to monitoring.

### Key Features

✅ **Multi-installer Support** - Handle complex scenarios like Firebird + EWMapa  
✅ **Smart PowerShell Scripts** - Auto-generated install/uninstall/detection scripts  
✅ **Zero Portal Work** - Complete Intune integration via API  
✅ **Group Assignment** - Visual selection of Azure AD groups  
✅ **Company Portal** - Full control over how apps appear to users  
✅ **Dual Interface** - Both GUI (Electron + React) and CLI available  
✅ **Windows Sandbox Testing** - Test packages before production deployment  
✅ **Deployment Monitoring** - Real-time install status tracking  

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/intune-app-packager.git
cd intune-app-packager

# Install Python dependencies
pip install -e .

# Verify installation
intune-packager --version
```

### Prerequisites

1. **Python 3.8+** installed
2. **IntuneWinAppUtil.exe** downloaded from [Microsoft's GitHub](https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool)
3. **Azure AD permissions**:
   - `DeviceManagementApps.ReadWrite.All`
   - `Group.Read.All`
   - `DeviceManagementManagedDevices.Read.All`
4. **Windows 10/11** for full testing capabilities (Windows Sandbox)

### First Steps

1. **Authenticate with Azure AD**:
```bash
intune-packager auth login --interactive
```

2. **Create your first application config**:
```bash
intune-packager init-app --name "MyApp" --wizard
```

3. **Generate scripts and preview**:
```bash
intune-packager generate-scripts --config myapp.yml --preview
```

4. **Build and deploy**:
```bash
intune-packager deploy --config myapp.yml --test-sandbox
```

## Application Configuration

### YAML Configuration Structure

Every application is defined in a YAML configuration file. Here's the structure:

```yaml
application:
  name: "Your App Name"
  version: "1.0.0"
  publisher: "Your Company"
  description: "Description for Company Portal"

installers:
  - name: "Component 1"
    file: "installer1.exe"
    silent_args: "/S /silent"
    wait_for_completion: true
    timeout: 600
    depends_on: []

detection:
  method: "comprehensive"
  rules:
    - type: "file"
      path: "C:\\Program Files\\App\\app.exe"
      check_version: true
      min_version: "1.0.0"

uninstall:
  strategy: "multi"
  force:
    enabled: true
    kill_processes: ["app.exe"]
    remove_paths: ["C:\\Program Files\\App"]

shortcuts:
  auto_create: true
  locations:
    - name: "AppName"
      target: "C:\\Program Files\\App\\app.exe"
      locations: ["Desktop", "StartMenu"]

intune:
  install_command: "powershell.exe -ExecutionPolicy Bypass -File install.ps1"
  uninstall_command: "powershell.exe -ExecutionPolicy Bypass -File uninstall.ps1"
  
  assignments:
    - intent: "available"
      target_groups:
        - "IT-Department"
        - "Sales-Team"
      notification: true

company_portal:
  description: "Description shown in Company Portal"
  icon: "assets/icon.png"
  screenshots: ["assets/screenshot1.png"]
```

### Configuration Examples

#### Example 1: Simple Single Installer

```yaml
application:
  name: "Notepad++"
  version: "8.5.0"
  publisher: "Don Ho"

installers:
  - name: "Notepad++"
    file: "npp.8.5.Installer.exe"
    silent_args: "/S"

detection:
  rules:
    - type: "file"
      path: "C:\\Program Files\\Notepad++\\notepad++.exe"
      check_version: true
      min_version: "8.5.0"
```

#### Example 2: Multi-Installer (Firebird + EWMapa)

See the complete example in `examples/ewmapa_config.yml`

Key points for multi-installer:
- Use `depends_on` to specify installation order
- Firebird must install before EWMapa
- Detection checks both components
- Uninstall handles both components

## Workflow

### Complete Workflow (GUI)

1. **Launch Application**
   - Opens Electron app
   - Authenticate with Azure AD

2. **Create New Package**
   - Click "New Application"
   - Wizard guides you through setup

3. **Add Installers**
   - Drag & drop .exe files
   - For multi-installer: set dependencies
   - Configure silent install parameters

4. **Configure Detection**
   - Auto-suggested rules based on analysis
   - Add/modify detection rules
   - Preview detection script

5. **Set Uninstall Strategy**
   - Choose: standard, force, or multi-strategy
   - Configure force removal options

6. **Company Portal Settings**
   - Add description, icon, screenshots
   - Set category and URLs

7. **Select Groups**
   - Visual picker shows all Azure AD groups
   - Select which groups get the app
   - Choose: Required, Available, or Uninstall

8. **Test (Optional)**
   - Click "Test in Sandbox"
   - Automated test verifies everything works
   - Shows pass/fail results

9. **Deploy**
   - Click "Deploy to Intune"
   - Progress bar shows: build → upload → assign
   - Real-time status updates

10. **Monitor**
    - Dashboard shows install status
    - Per-device and per-user statistics
    - Drill down into failures

### Complete Workflow (CLI)

```bash
# 1. Create application configuration
intune-packager init-app --name "EWMapa" --output ewmapa.yml

# 2. Edit configuration
# (Edit ewmapa.yml in your favorite editor)

# 3. Generate and preview scripts
intune-packager generate-scripts --config ewmapa.yml --preview

# 4. Test in Windows Sandbox (optional)
intune-packager test-sandbox --config ewmapa.yml

# 5. Deploy to Intune
intune-packager deploy \
  --config ewmapa.yml \
  --groups "IT-Dept,Sales" \
  --mode available \
  --monitor

# 6. Check deployment status
intune-packager status --app-name "EWMapa"
```

## PowerShell Scripts

### What Gets Generated

For each application, three PowerShell scripts are generated:

1. **install.ps1**
   - Handles multi-installer scenarios
   - Checks dependencies
   - Manages installation order
   - Creates shortcuts if missing
   - Comprehensive logging
   - Intune-compliant exit codes

2. **uninstall.ps1**
   - Multi-strategy approach:
     1. Try standard uninstall (registry)
     2. If fails: force removal
   - Kills running processes
   - Removes files and registry keys
   - Removes shortcuts
   - Verifies complete removal

3. **detection.ps1**
   - Multi-layer detection:
     - File existence + version check
     - Registry key validation
     - Process checks (optional)
     - Custom PowerShell logic
   - Returns 0 (detected) or 1 (not detected)

### Script Customization

You can customize generated scripts:

```bash
# Generate scripts to folder
intune-packager generate-scripts --config myapp.yml --output ./scripts

# Edit the scripts manually
code ./scripts/install.ps1

# Use custom scripts in deployment
intune-packager deploy --config myapp.yml --scripts-dir ./scripts
```

## Intune Integration

### Authentication

#### Interactive (GUI Users)
```bash
intune-packager auth login --interactive
```
Opens browser for Azure AD login.

#### Service Principal (Automation)
```bash
intune-packager auth login \
  --tenant-id <tenant-id> \
  --client-id <client-id> \
  --client-secret <secret>
```

### Group Management

#### List Available Groups
```bash
intune-packager groups list
intune-packager groups list --search "IT"
```

#### Assign to Groups
```bash
# Available in Company Portal
intune-packager assign \
  --app-name "EWMapa" \
  --groups "IT-Department,GIS-Team" \
  --mode available \
  --company-portal

# Required installation
intune-packager assign \
  --app-name "EWMapa" \
  --groups "Mapping-Specialists" \
  --mode required \
  --deadline "2025-12-31"
```

### Dependencies & Supersedence

#### Set Dependencies
```bash
intune-packager dependencies \
  --app-name "EWMapa" \
  --requires ".NET Framework 4.8,Visual C++ Redistributable"
```

#### Replace Old Versions
```bash
intune-packager supersede \
  --app-name "EWMapa 2.1.0" \
  --replaces "EWMapa 2.0.0,EWMapa 1.5.0" \
  --uninstall-previous
```

## Windows Sandbox Testing

Test your packages in an isolated environment before deploying to production.

### Prerequisites
- Windows 10/11 Pro or Enterprise
- Windows Sandbox feature enabled
- Virtualization enabled in BIOS

### Enable Windows Sandbox
```powershell
# Run as Administrator
Enable-WindowsOptionalFeature -FeatureName "Containers-DisposableClientVM" -All -Online
```

### Run Tests

**Via GUI:**
1. Click "Test in Sandbox" button
2. Wait for automated tests
3. Review test report

**Via CLI:**
```bash
intune-packager test-sandbox --config ewmapa.yml
```

### Test Sequence

1. Create isolated Sandbox environment
2. Copy package to Sandbox
3. Run `install.ps1`
4. Verify:
   - Exit code = 0
   - Files created
   - Registry keys present
   - Shortcuts created
   - Detection script returns 0
5. Run `uninstall.ps1`
6. Verify complete removal
7. Detection script returns 1
8. Generate test report

## Deployment Monitoring

### Real-time Status

**GUI Dashboard:**
- Live deployment statistics
- Install success/failure rates
- Device-by-device status
- User-based filtering
- Error details

**CLI Monitoring:**
```bash
# Watch deployment
intune-packager status --app-name "EWMapa" --watch

# Get detailed report
intune-packager status --app-name "EWMapa" --detailed --output report.json
```

### Status Information

- **Pending**: Deployment created, not yet installed
- **Installing**: Installation in progress
- **Installed**: Successfully installed
- **Failed**: Installation failed (with error details)
- **Not Applicable**: Device/user not in target group

## Troubleshooting

### Common Issues

#### "IntuneWinAppUtil.exe not found"
**Solution**: Download from Microsoft's GitHub and specify path:
```bash
intune-packager --tool-path /path/to/IntuneWinAppUtil.exe
```

#### "Authentication failed"
**Solution**: Check your Azure AD permissions and re-authenticate:
```bash
intune-packager auth login --interactive
```

#### "Detection script fails"
**Problem**: Application detected as not installed even though it is.

**Solution**: Review detection rules:
```bash
intune-packager analyze --input app.exe --suggest-detection
```

#### "Force uninstall leaves files"
**Solution**: Add paths to force removal:
```yaml
uninstall:
  force:
    remove_paths:
      - "C:\\Program Files\\App"
      - "C:\\ProgramData\\App"
```

### Debug Mode

Enable verbose logging:
```bash
# CLI
intune-packager deploy --config myapp.yml --verbose

# Check logs
cat $env:ProgramData\IntuneAppPackager\Logs\*.log
```

## Best Practices

### Configuration
✅ Always test in Windows Sandbox first  
✅ Use version checks in detection rules  
✅ Include both file and registry detection  
✅ Set realistic timeout values  
✅ Test silent install parameters manually first  

### Deployment
✅ Start with "Available" assignment for pilot groups  
✅ Monitor deployment before expanding to more groups  
✅ Use supersedence to replace old versions automatically  
✅ Set appropriate restart grace periods  
✅ Provide clear Company Portal descriptions  

### Maintenance
✅ Keep application configs in version control  
✅ Document custom detection logic  
✅ Review deployment logs regularly  
✅ Update supersedence chains for new versions  
✅ Archive old package configurations  

## Advanced Topics

### Custom Detection Scripts

Add custom PowerShell logic to detection:

```yaml
detection:
  custom_script: |
    # Check if service is running
    $service = Get-Service -Name "MyAppService" -ErrorAction SilentlyContinue
    if (!$service -or $service.Status -ne "Running") {
        return $false
    }
    
    # Check license file
    $license = Test-Path "C:\\ProgramData\\MyApp\\license.key"
    return $license
```

### Conditional Installation

Install components based on conditions:

```yaml
installers:
  - name: "32-bit Component"
    file: "component_x86.exe"
    condition: "[Environment]::Is64BitOperatingSystem -eq $false"
    
  - name: "64-bit Component"
    file: "component_x64.exe"
    condition: "[Environment]::Is64BitOperatingSystem -eq $true"
```

### Pre/Post Install Actions

```yaml
installers:
  - name: "Main App"
    file: "app.exe"
    pre_install_script: |
      # Stop services before install
      Stop-Service -Name "OldAppService" -Force
    post_install_script: |
      # Configure after install
      Set-ItemProperty -Path "HKLM:\SOFTWARE\App" -Name "Configured" -Value 1
```

## FAQ

**Q: Can I use this on macOS for development?**  
A: Yes! The GUI and CLI work on macOS. However, IntuneWinAppUtil.exe requires Windows (or Wine). Windows Sandbox testing requires Windows.

**Q: Do I need to go into Intune portal at all?**  
A: No! Everything is done through this application.

**Q: Can I automate this in CI/CD?**  
A: Yes! Use the CLI with service principal authentication.

**Q: What happens if installation fails?**  
A: The PowerShell scripts provide detailed logs. Check logs in `C:\ProgramData\IntuneAppPackager\Logs\`.

**Q: Can I update an existing app?**  
A: Yes! Use the `update` command or set supersedence to automatically replace old versions.

**Q: How do I handle portable apps (no installer)?**  
A: Configure as file-copy deployment. See `examples/portable_app.yml`.

## Support

### Getting Help

- **Documentation**: Full docs in `docs/` directory
- **Examples**: See `examples/` for common scenarios  
- **Issues**: GitHub Issues for bug reports
- **Logs**: Check `C:\ProgramData\IntuneAppPackager\Logs\`

### Reporting Bugs

Include:
1. Application config (YAML file)
2. Generated PowerShell scripts
3. Log files
4. IntuneWinAppUtil.exe output
5. Intune deployment error (if any)

## Next Steps

1. ✅ Complete the Quick Start
2. ✅ Review the EWMapa example (`examples/ewmapa_config.yml`)
3. ✅ Create your first application config
4. ✅ Test in Windows Sandbox
5. ✅ Deploy to a pilot group
6. ✅ Monitor deployment
7. ✅ Expand to production groups

---

**For developers**: See `ARCHITECTURE.md` and `WARP.md` for technical details and development guide.

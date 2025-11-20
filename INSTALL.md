# Instalacja - Intune App Packager

## 🚀 Metoda 1: Jeden Plik - Standalone Installer (REKOMENDOWANA)

**User NIE potrzebuje mieć Pythona zainstalowanego!**

### Krok 1: Zbuduj Installer (raz, przez developera)

```bash
# Upewnij się że masz Pythona 3.8+
python3 --version

# Zainstaluj projekt
cd /Users/rogtom/projects/intune-app-packager
python3 setup_complete.py

# Zbuduj standalone executable
python3 build_installer.py
```

**Rezultat**: Plik `dist/IntuneAppPackager-Installer` (lub `.exe` na Windows)

### Krok 2: Dystrybuuj Installer

Wyślij user tylko JEDEN plik:
- macOS: `dist/IntuneAppPackager-Installer`
- Windows: `dist/IntuneAppPackager-Installer.exe`

### Krok 3: User uruchamia Installer

```bash
# macOS/Linux
./IntuneAppPackager-Installer

# Windows  
IntuneAppPackager-Installer.exe
```

**Co się stanie**:
1. Otworzy się GUI (graficzny interface)
2. User wybiera config file (lub używa przykładu)
3. Klik "Generate Scripts"
4. Gotowe! PowerShell scripts są wygenerowane

---

## 🐍 Metoda 2: Z Pythonem (dla developerów)

### Instalacja

```bash
cd /Users/rogtom/projects/intune-app-packager
python3 setup_complete.py
```

### Uruchomienie GUI

```bash
# Uruchom graficzny interface
python3 -m intune_packager.installer_gui
```

### Lub użyj Python API

```python
from intune_packager.models import ApplicationProfile
from intune_packager.script_generator import ScriptGenerator
import yaml

# Load config
with open('examples/ewmapa_config.yml', 'r') as f:
    config = yaml.safe_load(f)

# Generate scripts
profile = ApplicationProfile.from_dict(config)
generator = ScriptGenerator()
scripts = generator.generate_all_scripts(profile)

# Save
for name, content in scripts.items():
    with open(f'output/{name}', 'w') as f:
        f.write(content)
```

---

## 📦 Co jest w pakiecie?

Po instalacji masz:
- ✅ Python package z wszystkimi dependencies
- ✅ PowerShell templates (install/uninstall/detection)
- ✅ Example configurations (EWMapa + Firebird)
- ✅ Graficzny interface (GUI)
- ✅ Kompletną dokumentację

---

## 🎯 Quick Start

### 1. Uruchom GUI

```bash
# Jeśli masz standalone installer:
./IntuneAppPackager-Installer

# Jeśli masz Pythona:
python3 -m intune_packager.installer_gui
```

### 2. W GUI:
1. Klik "Use Example" (użyje EWMapa config)
2. Wybierz output directory
3. Klik "Generate Scripts"
4. Gotowe!

### 3. Sprawdź output:
```bash
# Skrypty są w:
~/IntunePackages/EWMapa_2.1.0/
  - install.ps1
  - uninstall.ps1
  - detection.ps1
```

---

## 📚 Dokumentacja

- **USER_GUIDE.md** - Kompletny przewodnik użytkownika
- **ARCHITECTURE.md** - Architektura techniczna
- **PROJECT_STATUS.md** - Status implementacji
- **examples/ewmapa_config.yml** - Przykład konfiguracji

---

## ⚙️ Zaawansowane

### Budowanie na różnych platformach

**macOS**:
```bash
python3 build_installer.py
# Tworzy: dist/IntuneAppPackager-Installer (macOS executable)
```

**Windows**:
```bash
python build_installer.py
# Tworzy: dist/IntuneAppPackager-Installer.exe
```

**Linux**:
```bash
python3 build_installer.py
# Tworzy: dist/IntuneAppPackager-Installer (Linux executable)
```

### Wielkość pakietu

Standalone installer to ~50-80MB (zawiera Python + wszystkie dependencies)

### Wymagania systemowe

- **macOS**: 10.13+
- **Windows**: 7/10/11
- **Linux**: Dowolna dystrybucja z glibc 2.17+

---

## 🔧 Troubleshooting

### "Permission denied" na macOS/Linux

```bash
chmod +x IntuneAppPackager-Installer
./IntuneAppPackager-Installer
```

### Build fails podczas `build_installer.py`

```bash
# Zainstaluj PyInstaller
python3 -m pip install pyinstaller

# Spróbuj ponownie
python3 build_installer.py
```

### GUI nie otwiera się

```bash
# Test czy tkinter działa
python3 -c "import tkinter; print('OK')"

# Jeśli nie działa, zainstaluj:
# macOS: brew install python-tk
# Ubuntu: sudo apt-get install python3-tk
# Windows: tkinter jest wbudowany
```

---

## ✅ Weryfikacja instalacji

```bash
# Test 1: Import module
python3 -c "from intune_packager import ScriptGenerator; print('✅ Works!')"

# Test 2: Generate example
python3 examples/generate_example.py

# Test 3: Open GUI
python3 -m intune_packager.installer_gui
```

---

## 🎉 Gotowe!

Masz teraz działający Intune App Packager!

**Dla użytkowników końcowych**: Wystarczy uruchomić `IntuneAppPackager-Installer`  
**Dla developerów**: Zobacz `USER_GUIDE.md` i `ARCHITECTURE.md`

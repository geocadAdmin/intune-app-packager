# 🚀 START HERE - Intune App Packager

## Co to jest?

**Jeden installer** który generuje PowerShell scripts dla deploymentu aplikacji do Microsoft Intune.  
**User nie potrzebuje Pythona** - wszystko jest w jednym pliku!

---

## ⚡ Quick Start (3 kroki)

### 1️⃣ Zainstaluj (raz)

```bash
cd /Users/rogtom/projects/intune-app-packager
python3 setup_complete.py
```

### 2️⃣ Zbuduj Installer

```bash
python3 build_installer.py
```

**Rezultat**: `dist/IntuneAppPackager-Installer` (jeden plik ~50-80MB)

### 3️⃣ Uruchom!

```bash
./dist/IntuneAppPackager-Installer
```

**GUI się otworzy!** 🎉

---

## 🖥️ Jak używać GUI

1. **Kliknij "Use Example"** - załaduje przykład (EWMapa + Firebird)
2. **Wybierz output folder** - gdzie zapisać scripts
3. **Klik "Generate Scripts"** - gotowe!

Scripts są w: `~/IntunePackages/EWMapa_2.1.0/`

---

## 📁 Co zostało wygenerowane?

```
~/IntunePackages/EWMapa_2.1.0/
├── install.ps1      ← Instaluje Firebird + EWMapa (w kolejności)
├── uninstall.ps1    ← Odinstalowuje (standard → force)
└── detection.ps1    ← Sprawdza czy zainstalowane
```

**Te skrypty** możesz użyć w Intune do deployment!

---

## 📚 Więcej informacji

- **INSTALL.md** - Szczegółowa instrukcja instalacji
- **USER_GUIDE.md** - Kompletny przewodnik (579 linii!)
- **ARCHITECTURE.md** - Architektura techniczna
- **PROJECT_STATUS.md** - Co jest zrobione / co pozostało
- **examples/ewmapa_config.yml** - Prawdziwy przykład konfiguracji

---

## 🎯 Dla kogo to jest?

### IT Admins (użytkownicy końcowi):
✅ Pobierz `IntuneAppPackager-Installer`  
✅ Uruchom (nie trzeba Pythona!)  
✅ Generuj PowerShell scripts  
✅ Deploy do Intune  

### Developers (ty):
✅ `python3 setup_complete.py` - instalacja  
✅ `python3 build_installer.py` - build  
✅ Rozdaj installer użytkownikom  

---

## 🔥 Kluczowe Featury

### ✨ Multi-Installer Support
Firebird musi być przed EWMapa? **No problem!**  
Automatyczna kolejność i dependencies.

### ✨ Smart Detection
Sprawdza:
- Czy pliki istnieją (+ wersja)
- Czy registry keys są OK
- Czy Firebird service działa
- Custom PowerShell logic

### ✨ Force Uninstall
Próbuje standard uninstall.  
Nie działa? **Force mode**:
- Kill processes
- Delete files
- Clean registry
- Remove shortcuts

### ✨ Comprehensive Logging
Wszystkie logi w: `C:\ProgramData\IntuneAppPackager\Logs\`

---

## 🐛 Problem?

### GUI nie działa?

```bash
# Test tkinter
python3 -c "import tkinter"

# Zainstaluj jeśli trzeba:
# macOS: brew install python-tk
```

### Build fails?

```bash
pip install pyinstaller
python3 build_installer.py
```

### Inny problem?

Zobacz: `INSTALL.md` → sekcja Troubleshooting

---

## 📞 Next Steps

### Jeśli chcesz tylko używać:
1. ✅ Uruchom `setup_complete.py`
2. ✅ Test GUI: `python3 -m intune_packager.installer_gui`
3. ✅ Generuj scripts!

### Jeśli chcesz dystrybuować:
1. ✅ Build installer: `python3 build_installer.py`
2. ✅ Wyślij `dist/IntuneAppPackager-Installer` do userów
3. ✅ Oni uruchamiają - **zero setup!**

### Jeśli chcesz rozwijać:
1. ✅ Przeczytaj `ARCHITECTURE.md`
2. ✅ Przeczytaj `PROJECT_STATUS.md`
3. ✅ Zobacz co pozostało do zrobienia

---

## 💡 Pro Tips

**Tip 1**: Stwórz własny config file (jak `ewmapa_config.yml`)  
**Tip 2**: Użyj GUI do przetestowania przed buildem  
**Tip 3**: Na Windows potrzebujesz też `IntuneWinAppUtil.exe` (do .intunewin)  

---

## 🎉 Gotowe!

Masz wszystko czego potrzebujesz:
- ✅ Działający kod
- ✅ GUI interface
- ✅ Build system (PyInstaller)
- ✅ Przykłady (EWMapa + Firebird)
- ✅ Kompletną dokumentację

**Powodzenia!** 🚀

"""
Simple GUI Installer for Intune App Packager
Uses tkinter (built into Python) for cross-platform GUI.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import yaml

try:
    from intune_packager.models import ApplicationProfile
    from intune_packager.script_generator import ScriptGenerator
except ImportError:
    # If running as standalone, these will be bundled
    pass


class InstallerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Intune App Packager - Setup")
        self.root.geometry("800x600")
        
        # Variables
        self.config_file = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.home() / "IntunePackages"))
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create GUI widgets."""
        # Header
        header = tk.Frame(self.root, bg="#0078D4", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="Intune App Packager",
            font=("Arial", 20, "bold"),
            bg="#0078D4",
            fg="white"
        )
        title.pack(pady=15)
        
        # Footer
        footer = tk.Frame(self.root, height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        footer_label = tk.Label(
            footer,
            text="Intune App Packager v0.2.0 | Read USER_GUIDE.md for documentation",
            font=("Arial", 8),
            fg="gray"
        )
        footer_label.pack(pady=5)
        
        # Create canvas with scrollbar for main content
        canvas = tk.Canvas(self.root)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Main content inside scrollable frame
        content = tk.Frame(scrollable_frame, padx=20, pady=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Instructions
        instructions = tk.Label(
            content,
            text="Generate PowerShell scripts for Intune deployment",
            font=("Arial", 12),
            wraplength=700
        )
        instructions.pack(pady=10)
        
        # Configuration file selection
        config_frame = tk.LabelFrame(content, text="Application Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(config_frame, text="Config File (YAML):").pack(anchor=tk.W)
        
        file_frame = tk.Frame(config_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        tk.Entry(file_frame, textvariable=self.config_file, width=60).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(file_frame, text="Browse...", command=self.browse_config).pack(side=tk.LEFT)
        tk.Button(file_frame, text="Use Example", command=self.use_example).pack(side=tk.LEFT, padx=5)
        
        # Output directory
        output_frame = tk.LabelFrame(content, text="Output Directory", padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(output_frame, text="Scripts will be saved to:").pack(anchor=tk.W)
        
        out_frame = tk.Frame(output_frame)
        out_frame.pack(fill=tk.X, pady=5)
        
        tk.Entry(out_frame, textvariable=self.output_dir, width=60).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(out_frame, text="Browse...", command=self.browse_output).pack(side=tk.LEFT)
        
        # Progress/Log area
        log_frame = tk.LabelFrame(content, text="Status", padx=10, pady=10)
        log_frame.pack(fill=tk.X, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.pack(fill=tk.X)
        
        # Buttons
        button_frame = tk.Frame(content)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.generate_btn = tk.Button(
            button_frame,
            text="Generate Scripts",
            command=self.generate_scripts,
            bg="#0078D4",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Open Output Folder",
            command=self.open_output,
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit,
            padx=20,
            pady=10
        ).pack(side=tk.RIGHT, padx=5)
    
    def log(self, message):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def browse_config(self):
        """Browse for config file."""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")]
        )
        if filename:
            self.config_file.set(filename)
            self.log(f"Selected config: {filename}")
    
    def use_example(self):
        """Use example configuration."""
        # Try to find example
        possible_paths = [
            Path("examples/ewmapa_config.yml"),
            Path(__file__).parent.parent.parent / "examples" / "ewmapa_config.yml",
        ]
        
        if getattr(sys, 'frozen', False):
            # Running as executable
            bundle_dir = Path(sys._MEIPASS)
            possible_paths.insert(0, bundle_dir / "examples" / "ewmapa_config.yml")
        
        for path in possible_paths:
            if path.exists():
                self.config_file.set(str(path))
                self.log(f"Using example config: {path}")
                return
        
        messagebox.showwarning("Example Not Found", "Example configuration file not found")
    
    def browse_output(self):
        """Browse for output directory."""
        dirname = filedialog.askdirectory(title="Select Output Directory")
        if dirname:
            self.output_dir.set(dirname)
            self.log(f"Output directory: {dirname}")
    
    def open_output(self):
        """Open output directory in file explorer."""
        output_path = Path(self.output_dir.get())
        if output_path.exists():
            import platform
            import subprocess
            
            if platform.system() == "Windows":
                os.startfile(output_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(output_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_path)])
        else:
            messagebox.showwarning("Directory Not Found", f"Output directory does not exist:\n{output_path}")
    
    def generate_scripts(self):
        """Generate PowerShell scripts."""
        config_path = self.config_file.get()
        output_path = self.output_dir.get()
        
        if not config_path:
            messagebox.showerror("Error", "Please select a configuration file")
            return
        
        if not Path(config_path).exists():
            messagebox.showerror("Error", f"Configuration file not found:\n{config_path}")
            return
        
        # Disable button during generation
        self.generate_btn.config(state=tk.DISABLED)
        
        # Run generation in thread to keep GUI responsive
        thread = threading.Thread(target=self._generate_scripts_thread, args=(config_path, output_path))
        thread.daemon = True
        thread.start()
    
    def _generate_scripts_thread(self, config_path, output_path):
        """Generate scripts in background thread."""
        try:
            self.log("="*60)
            self.log("Starting script generation...")
            self.log(f"Config: {config_path}")
            self.log(f"Output: {output_path}")
            self.log("")
            
            # Load configuration
            self.log("Loading configuration...")
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Create profile
            self.log("Creating application profile...")
            profile = ApplicationProfile.from_dict(config_data)
            self.log(f"  Application: {profile.name} v{profile.version}")
            self.log(f"  Publisher: {profile.publisher}")
            self.log(f"  Installers: {len(profile.installers)}")
            self.log("")
            
            # Generate scripts
            self.log("Generating PowerShell scripts...")
            generator = ScriptGenerator()
            scripts = generator.generate_all_scripts(profile)
            
            # Save scripts
            output_dir = Path(output_path) / f"{profile.name}_{profile.version}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for script_name, script_content in scripts.items():
                script_path = output_dir / script_name
                with open(script_path, 'w', encoding='utf-8', newline='\r\n') as f:
                    f.write(script_content)
                
                lines = len(script_content.split('\n'))
                self.log(f"  ✅ {script_name}: {lines} lines")
            
            self.log("")
            self.log(f"✅ Scripts saved to: {output_dir}")
            self.log("")
            self.log("Generated scripts:")
            self.log("  - install.ps1: Installs application(s)")
            self.log("  - uninstall.ps1: Removes application")
            self.log("  - detection.ps1: Checks if installed")
            self.log("")
            self.log("="*60)
            self.log("✅ Generation completed successfully!")
            self.log("")
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"PowerShell scripts generated successfully!\n\nSaved to:\n{output_dir}"
            ))
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate scripts:\n\n{str(e)}"))
        
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))


def main():
    """Main entry point for GUI."""
    root = tk.Tk()
    app = InstallerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

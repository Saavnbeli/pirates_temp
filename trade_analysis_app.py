import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
import os
import re
from datetime import datetime

# Import your existing functions
try:
    from Create_Trade_Summary import (
        pull_trade_package_data, 
        create_metric_comparison_table, 
        create_metric_comparison_html
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

class TradeAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trade Package Analysis Tool")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        
        # Check if imports are available
        if not IMPORTS_AVAILABLE:
            self.show_import_error()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Trade Package Analysis Tool", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Enter a Notion page URL or page ID to generate trade analysis:",
                                font=('Arial', 10))
        instructions.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=tk.W)
        
        # Input section
        ttk.Label(main_frame, text="Notion URL/ID:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=50)
        self.url_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Paste button
        paste_btn = ttk.Button(main_frame, text="Paste", command=self.paste_from_clipboard)
        paste_btn.grid(row=2, column=2, pady=5, padx=(5, 0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        options_frame.columnconfigure(1, weight=1)
        
        # Plot type selection
        ttk.Label(options_frame, text="Include Plots:").grid(row=0, column=0, sticky=tk.W)
        self.plot_var = tk.StringVar(value="all")
        plot_combo = ttk.Combobox(options_frame, textvariable=self.plot_var, 
                                 values=["all", "war_adjusted", "none"], state="readonly")
        plot_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Auto-open checkbox
        self.auto_open_var = tk.BooleanVar(value=True)
        auto_open_check = ttk.Checkbutton(options_frame, text="Auto-open report when complete",
                                         variable=self.auto_open_var)
        auto_open_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Output directory selection
        ttk.Label(options_frame, text="Save to:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        
        self.output_dir_var = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        dir_frame = ttk.Frame(options_frame)
        dir_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 0), padx=(10, 0))
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(dir_frame, text="Browse", command=self.browse_directory)
        browse_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Generate button
        self.generate_btn = ttk.Button(main_frame, text="Generate Trade Analysis", 
                                      command=self.generate_analysis, style='Accent.TButton')
        self.generate_btn.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=6, column=0, columnspan=3)
        
        # Log text area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="5")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Example text
        self.log("Welcome to Trade Package Analysis Tool!")
        self.log("Example URL: https://www.notion.so/Baez-for-Bednar-233cafa69c5f802e8696e06f99a060d1")
        self.log("Or just paste the page ID: 233cafa69c5f802e8696e06f99a060d1")
    
    def show_import_error(self):
        error_msg = f"Could not import required modules:\n{IMPORT_ERROR}\n\nPlease ensure Create_Trade_Summary.py is in the same directory."
        messagebox.showerror("Import Error", error_msg)
        self.generate_btn.config(state='disabled')
    
    def log(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def paste_from_clipboard(self):
        """Paste from clipboard to URL entry"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_var.set(clipboard_content)
        except tk.TclError:
            self.log("No text in clipboard")
    
    def browse_directory(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def extract_page_id(self, url_or_id):
        """Extract page ID from Notion URL or return as-is if already an ID"""
        url_or_id = url_or_id.strip()
        
        # If it's already a page ID (32 characters, alphanumeric)
        if re.match(r'^[a-f0-9]{32}$', url_or_id.replace('-', '')):
            return url_or_id.replace('-', '')
        
        # Extract from URL
        patterns = [
            r'notion\.so/.*?([a-f0-9]{32})',
            r'notion\.so/.*?([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
            r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
            r'([a-f0-9]{32})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id, re.IGNORECASE)
            if match:
                return match.group(1).replace('-', '')
        
        return None
    
    def generate_analysis(self):
        """Generate trade analysis in a separate thread"""
        if not IMPORTS_AVAILABLE:
            messagebox.showerror("Error", "Required modules not available")
            return
        
        url_or_id = self.url_var.get().strip()
        if not url_or_id:
            messagebox.showerror("Error", "Please enter a Notion URL or page ID")
            return
        
        # Disable button and start progress
        self.generate_btn.config(state='disabled')
        self.progress.start()
        self.status_var.set("Generating analysis...")
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._run_analysis, args=(url_or_id,))
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self, url_or_id):
        """Run the analysis (called from thread)"""
        try:
            # Extract page ID
            page_id = self.extract_page_id(url_or_id)
            if not page_id:
                raise ValueError("Could not extract valid page ID from input")
            
            self.log(f"Extracted page ID: {page_id}")
            self.log("Fetching trade package data...")
            
            # Pull trade package data
            pkg = pull_trade_package_data(page_id)
            if not pkg:
                raise ValueError("Could not retrieve package data. Check page ID and permissions.")
            
            package_name = pkg["package"].get("name", "Unknown")
            self.log(f"Found package: {package_name}")
            
            # Generate analysis
            self.log("Creating metric comparison table...")
            df = create_metric_comparison_table(pkg, save_to_excel=False, output_html=False)
            
            self.log("Generating HTML report...")
            plot_type = self.plot_var.get()
            include_plots = plot_type != "none"
            
            html = create_metric_comparison_html(
                df, 
                package_name=package_name, 
                include_plots=include_plots, 
                package_data=pkg, 
                plot_type=plot_type
            )
            
            # Save file
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', package_name)
            filename = f"{safe_name}_Trade_Summary.html"
            output_dir = self.output_dir_var.get()
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            
            self.log(f"Report saved: {filepath}")
            
            # Auto-open if requested
            if self.auto_open_var.get():
                webbrowser.open(f'file://{os.path.abspath(filepath)}')
                self.log("Report opened in browser")
            
            self._analysis_complete(f"Analysis complete! Report saved to:\n{filepath}")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
            self._analysis_complete(f"Error: {str(e)}", is_error=True)
    
    def _analysis_complete(self, message, is_error=False):
        """Called when analysis is complete (from thread)"""
        def update_ui():
            self.progress.stop()
            self.generate_btn.config(state='normal')
            self.status_var.set("Ready")
            
            if is_error:
                messagebox.showerror("Error", message)
            else:
                messagebox.showinfo("Success", message)
        
        # Schedule UI update on main thread
        self.root.after(0, update_ui)

def main():
    root = tk.Tk()
    app = TradeAnalysisApp(root)
    
    # Center window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()
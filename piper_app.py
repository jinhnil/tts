import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Piper GUI Reader - Simple & Fast Offline Vietnamese TTS App

class PiperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS Tiếng Việt - Đọc Sách Offline")
        self.root.geometry("650x550")
        self.root.minsize(550, 450)

        # Style
        style = ttk.Style()
        style.theme_use("clam")

        # Variables
        self.piper_exe = tk.StringVar(value="piper.exe")
        self.model_path = tk.StringVar(value="vi_VN-vais1000-medium.onnx")
        self.output_file = tk.StringVar(value="output.wav")
        self.status_var = tk.StringVar(value="Sẵn sàng")

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#1e293b", padding=10)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame, 
            text="🎧 Piper TTS Tiếng Việt Offline", 
            font=("Segoe UI", 14, "bold"), 
            bg="#1e293b", 
            fg="#f8fafc"
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame, 
            text="Ứng dụng đọc văn bản / truyện chữ tiếng Việt không cần mạng", 
            font=("Segoe UI", 9), 
            bg="#1e293b", 
            fg="#94a3b8"
        )
        subtitle_label.pack(anchor="w")

        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Cấu hình Piper & Model", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=8)

        # Piper exe path
        ttk.Label(config_frame, text="File Piper.exe:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=self.piper_exe, width=40).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(config_frame, text="Chọn...", command=self.browse_piper).grid(row=0, column=2, pady=2)

        # Model ONNX path
        ttk.Label(config_frame, text="Model ONNX:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=self.model_path, width=40).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(config_frame, text="Chọn...", command=self.browse_model).grid(row=1, column=2, pady=2)

        # Text Input Area
        text_frame = ttk.LabelFrame(self.root, text="Nội dung văn bản / Truyện", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        toolbar = ttk.Frame(text_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="📂 Mở File Text (.txt)", command=self.load_txt_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Xóa hết", command=self.clear_text).pack(side=tk.LEFT, padx=2)

        self.text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10), undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.text_area, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom Action Bar
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill=tk.X)

        self.btn_convert = ttk.Button(
            action_frame, 
            text="▶️ Chuyển văn bản thành File Âm Thanh (WAV)", 
            command=self.start_conversion
        )
        self.btn_convert.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Status Bar
        status_frame = tk.Frame(self.root, bg="#f1f5f9", height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            status_frame, 
            textvariable=self.status_var, 
            font=("Segoe UI", 9), 
            bg="#f1f5f9", 
            fg="#475569"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

    def browse_piper(self):
        filename = filedialog.askopenfilename(
            title="Chọn file piper.exe",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if filename:
            self.piper_exe.set(filename)

    def browse_model(self):
        filename = filedialog.askopenfilename(
            title="Chọn file model ONNX",
            filetypes=[("ONNX Model", "*.onnx"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path.set(filename)

    def load_txt_file(self):
        filename = filedialog.askopenfilename(
            title="Chọn file văn bản .txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.status_var.set(f"Đã mở file: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.status_var.set("Đã xóa văn bản")

    def start_conversion(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập nội dung văn bản!")
            return

        piper = self.piper_exe.get()
        model = self.model_path.get()

        if not os.path.exists(piper) and piper == "piper.exe":
            # Check current dir
            if not os.path.exists("piper.exe"):
                messagebox.showerror("Lỗi", f"Không tìm thấy {piper}! Vui lòng chọn đường dẫn đến piper.exe.")
                return

        if not os.path.exists(model) and model == "vi_VN-vais1000-medium.onnx":
            if not os.path.exists("vi_VN-vais1000-medium.onnx"):
                messagebox.showerror("Lỗi", f"Không tìm thấy {model}! Vui lòng chọn đường dẫn đến file model .onnx.")
                return

        output_path = filedialog.asksaveasfilename(
            title="Lưu file âm thanh",
            defaultextension=".wav",
            filetypes=[("WAV Audio", "*.wav")]
        )
        if not output_path:
            return

        self.btn_convert.config(state=tk.DISABLED)
        self.status_var.set("⏳ Đang tổng hợp âm thanh bằng Piper TTS...")

        thread = threading.Thread(target=self.run_piper_thread, args=(text, piper, model, output_path))
        thread.start()

    def run_piper_thread(self, text, piper, model, output_path):
        try:
            process = subprocess.Popen(
                [piper, "--model", model, "--output_file", output_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = process.communicate(input=text)

            if process.returncode == 0:
                self.root.after(0, self.on_success, output_path)
            else:
                self.root.after(0, self.on_error, stderr)
        except Exception as e:
            self.root.after(0, self.on_error, str(e))

    def on_success(self, output_path):
        self.btn_convert.config(state=tk.NORMAL)
        self.status_var.set(f"✅ Hoàn thành: {os.path.basename(output_path)}")
        
        reply = messagebox.askyesno("Thành công", f"Đã xuất âm thanh thành công!\nFile: {output_path}\n\nBạn có muốn mở nghe ngay không?")
        if reply:
            try:
                os.startfile(output_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở file: {e}")

    def on_error(self, err_msg):
        self.btn_convert.config(state=tk.NORMAL)
        self.status_var.set("❌ Lỗi chuyển đổi âm thanh")
        messagebox.showerror("Lỗi Piper TTS", f"Quá trình chuyển đổi thất bại:\n{err_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PiperApp(root)
    root.mainloop()

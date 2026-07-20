import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import pygame or winsound for built-in audio playback
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    import winsound

class PiperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS Tiếng Việt - Đọc Sách Offline 100%")
        self.root.geometry("700x620")
        self.root.minsize(600, 500)

        # Base dir
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Auto-detect Piper exe
        default_piper = os.path.join(self.base_dir, "piper", "piper.exe")
        if not os.path.exists(default_piper):
            default_piper = os.path.join(self.base_dir, "piper.exe")

        # Auto-detect Model ONNX
        default_model = os.path.join(self.base_dir, "vi_VN-vais1000-medium.onnx")

        # Variables
        self.piper_exe = tk.StringVar(value=default_piper if os.path.exists(default_piper) else "piper/piper.exe")
        self.model_path = tk.StringVar(value=default_model if os.path.exists(default_model) else "vi_VN-vais1000-medium.onnx")
        self.speed_var = tk.DoubleVar(value=1.0)
        self.status_var = tk.StringVar(value="Sẵn sàng")
        self.audio_temp_path = os.path.join(self.base_dir, "temp_piper_output.wav")
        self.is_playing = False

        self.setup_ui()
        self.check_initial_files()

    def check_initial_files(self):
        p_ok = os.path.exists(self.piper_exe.get())
        m_ok = os.path.exists(self.model_path.get())
        if p_ok and m_ok:
            self.status_var.set("✅ Đã tự động kết nối thành công Piper.exe & Model Tiếng Việt!")
        else:
            missing = []
            if not p_ok: missing.append("piper.exe")
            if not m_ok: missing.append("vi_VN-vais1000-medium.onnx")
            self.status_var.set(f"⚠️ Chưa tìm thấy: {', '.join(missing)}")

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#0f172a", padding=12)
        header_frame.pack(fill=tk.X)
        
        title_label = tk.Label(
            header_frame, 
            text="🎧 Piper TTS Tiếng Việt - Ứng Dụng Đọc Sách Offline 100%", 
            font=("Segoe UI", 13, "bold"), 
            bg="#0f172a", 
            fg="#38bdf8"
        )
        title_label.pack(anchor="w")

        subtitle_label = tk.Label(
            header_frame, 
            text="Tự động sử dụng mô hình vi_VN-vais1000-medium.onnx & Piper Engine", 
            font=("Segoe UI", 9), 
            bg="#0f172a", 
            fg="#94a3b8"
        )
        subtitle_label.pack(anchor="w")

        # Configuration Frame (Collapsible or compact)
        config_frame = ttk.LabelFrame(self.root, text="Cấu hình Đường Dẫn (Đã Tự Động Nhận)", padding=8)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # Piper exe path
        ttk.Label(config_frame, text="Piper.exe:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=self.piper_exe, width=48).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(config_frame, text="Browse...", command=self.browse_piper).grid(row=0, column=2, pady=2)

        # Model ONNX path
        ttk.Label(config_frame, text="Model ONNX:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(config_frame, textvariable=self.model_path, width=48).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(config_frame, text="Browse...", command=self.browse_model).grid(row=1, column=2, pady=2)

        # Speed Control
        speed_frame = ttk.Frame(config_frame)
        speed_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=4)
        
        ttk.Label(speed_frame, text="Tốc độ đọc:").pack(side=tk.LEFT, padx=(0, 5))
        self.speed_slider = ttk.Scale(
            speed_frame, 
            from_=0.5, 
            to=2.0, 
            variable=self.speed_var, 
            orient=tk.HORIZONTAL, 
            length=150,
            command=lambda v: self.speed_label.config(text=f"{float(v):.1f}x")
        )
        self.speed_slider.pack(side=tk.LEFT, padx=5)
        self.speed_label = ttk.Label(speed_frame, text="1.0x", font=("Segoe UI", 9, "bold"))
        self.speed_label.pack(side=tk.LEFT, padx=5)

        # Text Input Area
        text_frame = ttk.LabelFrame(self.root, text="Nội Dung Văn Bản / Truyện Chữ", padding=8)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        toolbar = ttk.Frame(text_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="📂 Mở File Truyện (.txt)", command=self.load_txt_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ Xóa hết", command=self.clear_text).pack(side=tk.LEFT, padx=2)

        self.word_count_var = tk.StringVar(value="0 từ | 0 ký tự")
        ttk.Label(toolbar, textvariable=self.word_count_var, font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=5)

        self.text_area = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10), undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.text_area, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area.bind("<KeyRelease>", self.update_word_count)

        # Sample text
        sample_text = "Xin chào! Đây là ứng dụng đọc tiếng Việt offline hoàn chỉnh sử dụng mô hình Piper TTS AI. Bạn có thể dán văn bản hoặc mở file truyện chữ .txt để đọc mượt mà 100% không cần mạng."
        self.text_area.insert("1.0", sample_text)
        self.update_word_count()

        # Audio Action Bar
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill=tk.X)

        self.btn_play = ttk.Button(
            action_frame, 
            text="🔊 ĐỌC NGAY (PLAY)", 
            command=self.start_synthesis_and_play
        )
        self.btn_play.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_stop = ttk.Button(
            action_frame, 
            text="⏹ DỪNG", 
            command=self.stop_playback
        )
        self.btn_stop.pack(side=tk.LEFT, padx=3)

        self.btn_export = ttk.Button(
            action_frame, 
            text="💾 XUẤT FILE WAV/MP3", 
            command=self.export_audio
        )
        self.btn_export.pack(side=tk.LEFT, padx=3)

        # Status Bar
        status_frame = tk.Frame(self.root, bg="#e2e8f0", height=26)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            status_frame, 
            textvariable=self.status_var, 
            font=("Segoe UI", 9, "bold"), 
            bg="#e2e8f0", 
            fg="#0f172a"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

    def update_word_count(self, event=None):
        content = self.text_area.get("1.0", tk.END).strip()
        chars = len(content)
        words = len(content.split()) if content else 0
        self.word_count_var.set(f"{words} từ | {chars} ký tự")

    def browse_piper(self):
        filename = filedialog.askopenfilename(
            title="Chọn file piper.exe",
            filetypes=[("Executable", "*.exe"), ("All Files", "*.*")]
        )
        if filename:
            self.piper_exe.set(filename)
            self.check_initial_files()

    def browse_model(self):
        filename = filedialog.askopenfilename(
            title="Chọn file model ONNX",
            filetypes=[("ONNX Model", "*.onnx"), ("All Files", "*.*")]
        )
        if filename:
            self.model_path.set(filename)
            self.check_initial_files()

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
                self.update_word_count()
                self.status_var.set(f"📂 Đã nạp file: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")

    def clear_text(self):
        self.text_area.delete("1.0", tk.END)
        self.update_word_count()
        self.status_var.set("Đã xóa văn bản")

    def stop_playback(self):
        self.is_playing = False
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        self.status_var.set("⏹ Đã dừng phát âm thanh")

    def start_synthesis_and_play(self):
        self.stop_playback()
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập văn bản cần đọc!")
            return

        piper = self.piper_exe.get()
        model = self.model_path.get()

        if not os.path.exists(piper):
            messagebox.showerror("Lỗi", f"Không tìm thấy file: {piper}")
            return
        if not os.path.exists(model):
            messagebox.showerror("Lỗi", f"Không tìm thấy file model: {model}")
            return

        self.btn_play.config(state=tk.DISABLED)
        self.status_var.set("⏳ Đang tổng hợp âm thanh bằng Piper AI...")

        thread = threading.Thread(target=self.synthesize_and_play_thread, args=(text, piper, model))
        thread.start()

    def synthesize_and_play_thread(self, text, piper, model):
        try:
            rate = self.speed_var.get()
            length_scale = 1.0 / max(0.5, min(2.0, rate))

            cmd = [
                piper,
                "--model", model,
                "--output_file", self.audio_temp_path,
                "--length_scale", str(length_scale)
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            stdout, stderr = process.communicate(input=text)

            if process.returncode == 0:
                self.root.after(0, self.play_generated_audio)
            else:
                self.root.after(0, self.on_error, stderr)
        except Exception as e:
            self.root.after(0, self.on_error, str(e))

    def play_generated_audio(self):
        self.btn_play.config(state=tk.NORMAL)
        if not os.path.exists(self.audio_temp_path):
            self.status_var.set("❌ Lỗi: Không tìm thấy file âm thanh đầu ra")
            return

        self.status_var.set("🔊 Đang phát âm thanh...")
        self.is_playing = True

        def play_thread():
            try:
                if HAS_PYGAME:
                    pygame.mixer.music.load(self.audio_temp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and self.is_playing:
                        pygame.time.Clock().tick(10)
                else:
                    winsound.PlaySound(self.audio_temp_path, winsound.SND_FILENAME)
                
                if self.is_playing:
                    self.root.after(0, lambda: self.status_var.set("✅ Hoàn thành phát âm thanh"))
            except Exception as e:
                print("Audio play error:", e)

        threading.Thread(target=play_thread, daemon=True).start()

    def export_audio(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập văn bản cần đọc!")
            return

        piper = self.piper_exe.get()
        model = self.model_path.get()

        if not os.path.exists(piper) or not os.path.exists(model):
            messagebox.showerror("Lỗi", "Chưa cấu hình đúng đường dẫn Piper hoặc Model!")
            return

        output_path = filedialog.asksaveasfilename(
            title="Xuất file âm thanh WAV",
            defaultextension=".wav",
            filetypes=[("WAV Audio File", "*.wav")]
        )
        if not output_path:
            return

        self.status_var.set("⏳ Đang xuất file âm thanh...")

        def export_thread():
            try:
                rate = self.speed_var.get()
                length_scale = 1.0 / max(0.5, min(2.0, rate))
                cmd = [
                    piper,
                    "--model", model,
                    "--output_file", output_path,
                    "--length_scale", str(length_scale)
                ]
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8"
                )
                proc.communicate(input=text)
                if proc.returncode == 0:
                    self.root.after(0, lambda: messagebox.showinfo("Thành công", f"Đã xuất thành công file âm thanh:\n{output_path}"))
                    self.root.after(0, lambda: self.status_var.set(f"✅ Đã xuất: {os.path.basename(output_path)}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", "Xuất file thất bại!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Lỗi", str(e)))

        threading.Thread(target=export_thread, daemon=True).start()

    def on_error(self, err_msg):
        self.btn_play.config(state=tk.NORMAL)
        self.status_var.set("❌ Lỗi tổng hợp âm thanh Piper")
        messagebox.showerror("Lỗi Piper TTS", f"Tổng hợp âm thanh thất bại:\n{err_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PiperApp(root)
    root.mainloop()

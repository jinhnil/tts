import os
import sys
import time
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Try loading pygame for robust audio control, fallback to winsound
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
    HAS_PYGAME = True
except Exception:
    import winsound

class StandalonePiperDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng Dụng Đọc Truyện Tiếng Việt Offline - Piper AI Desktop")
        self.root.geometry("850x650")
        self.root.minsize(700, 500)

        # Base path detection
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Detect Piper.exe
        default_piper = os.path.join(self.base_dir, "piper", "piper.exe")
        if not os.path.exists(default_piper):
            default_piper = os.path.join(self.base_dir, "piper.exe")

        # Detect Model
        default_model = os.path.join(self.base_dir, "vi_VN-vais1000-medium.onnx")

        # App Variables
        self.piper_exe = default_piper
        self.model_path = default_model
        
        self.paragraphs = []
        self.current_para_index = 0
        self.is_playing = False
        self.is_paused = False

        self.speed_var = tk.DoubleVar(value=1.0)
        self.font_size_var = tk.IntVar(value=13)
        self.status_var = tk.StringVar(value="Sẵn sàng")

        # Audio process reference & thread safety lock
        self.current_process = None
        self.audio_lock = threading.Lock()
        self.play_thread_id = 0

        self.setup_ui()
        self.check_files()

    def check_files(self):
        p_ok = os.path.exists(self.piper_exe)
        m_ok = os.path.exists(self.model_path)
        if p_ok and m_ok:
            self.status_var.set("✅ Đã tự động nhận diện Piper Engine & Model Tiếng Việt thành công!")
        else:
            missing = []
            if not p_ok: missing.append("piper/piper.exe")
            if not m_ok: missing.append("vi_VN-vais1000-medium.onnx")
            self.status_var.set(f"⚠️ Thiếu file: {', '.join(missing)}")

    def setup_ui(self):
        # Configure Colors & Theme
        self.bg_dark = "#0f172a"
        self.fg_light = "#f8fafc"
        self.accent_blue = "#38bdf8"
        self.card_bg = "#1e293b"

        # Top Header Bar
        header = tk.Frame(self.root, bg=self.bg_dark, padding=12)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="📖 Piper AI Desktop Reader - Đọc Truyện Offline",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_dark,
            fg=self.accent_blue
        )
        title.pack(side=tk.LEFT)

        # Settings Controls (Speed & Font Size)
        controls_frame = tk.Frame(header, bg=self.bg_dark)
        controls_frame.pack(side=tk.RIGHT)

        tk.Label(controls_frame, text="Tốc độ:", font=("Segoe UI", 9), bg=self.bg_dark, fg="#94a3b8").pack(side=tk.LEFT, padx=(5, 2))
        
        self.speed_scale = ttk.Scale(
            controls_frame,
            from_=0.5,
            to=2.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=100,
            command=self.on_setting_changed
        )
        self.speed_scale.pack(side=tk.LEFT, padx=2)

        self.speed_lbl = tk.Label(controls_frame, text="1.0x", font=("Segoe UI", 9, "bold"), bg=self.bg_dark, fg=self.accent_blue)
        self.speed_lbl.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(controls_frame, text="Cỡ chữ:", font=("Segoe UI", 9), bg=self.bg_dark, fg="#94a3b8").pack(side=tk.LEFT, padx=(5, 2))
        
        font_spin = ttk.Spinbox(
            controls_frame,
            from_=9,
            to=24,
            textvariable=self.font_size_var,
            width=3,
            command=self.update_font_size
        )
        font_spin.pack(side=tk.LEFT, padx=2)

        # File & Action Toolbar
        toolbar = tk.Frame(self.root, bg=self.card_bg, padding=8)
        toolbar.pack(fill=tk.X)

        btn_open = tk.Button(
            toolbar,
            text="📂 Mở File Truyện (.txt)",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            command=self.open_txt_file
        )
        btn_open.pack(side=tk.LEFT, padx=5)

        btn_clear = tk.Button(
            toolbar,
            text="🗑️ Xóa hết",
            font=("Segoe UI", 9),
            bg="#475569",
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4,
            command=self.clear_text
        )
        btn_clear.pack(side=tk.LEFT, padx=5)

        self.para_count_label = tk.Label(
            toolbar,
            text="0 đoạn | Đoạn hiện tại: 0/0",
            font=("Segoe UI", 9),
            bg=self.card_bg,
            fg="#94a3b8"
        )
        self.para_count_label.pack(side=tk.RIGHT, padx=10)

        # Main Reader Text Display
        main_frame = tk.Frame(self.root, bg="#020617")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.text_display = tk.Text(
            main_frame,
            wrap=tk.WORD,
            font=("Segoe UI", self.font_size_var.get()),
            bg="#020617",
            fg="#e2e8f0",
            insertbackground="white",
            padx=15,
            pady=15,
            undo=True
        )
        self.text_display.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        scrollbar = ttk.Scrollbar(main_frame, command=self.text_display.yview)
        self.text_display.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Tag for Highlighting current paragraph
        self.text_display.tag_config(
            "active_para",
            background="#1e3a8a",
            foreground="#ffffff",
            font=("Segoe UI", self.font_size_var.get(), "bold")
        )

        # Initial Sample Text
        sample_text = (
            "Chào mừng bạn đến với Ứng Dụng Đọc Truyện Tiếng Việt Offline Desktop!\n\n"
            "Ứng dụng chạy trực tiếp 100% trên máy tính của bạn sử dụng mô hình Piper AI Tiếng Việt.\n\n"
            "Bạn có thể mở bất kỳ file truyện chữ .txt nào để thưởng thức giọng đọc mượt mà, "
            "không bị ngắt quãng hay lặp tiếng khi thay đổi đoạn hoặc tốc độ đọc."
        )
        self.text_display.insert("1.0", sample_text)
        self.load_paragraphs_from_text()

        # Bottom Player Navigation Control Bar
        player_bar = tk.Frame(self.root, bg=self.card_bg, padding=10)
        player_bar.pack(fill=tk.X)

        self.btn_prev = tk.Button(
            player_bar,
            text="⏮ Đoạn Trước",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.prev_paragraph
        )
        self.btn_prev.pack(side=tk.LEFT, padx=4)

        self.btn_play = tk.Button(
            player_bar,
            text="▶️ PHÁT / TẠM DỪNG",
            font=("Segoe UI", 11, "bold"),
            bg="#0284c7",
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            command=self.toggle_play_pause
        )
        self.btn_play.pack(side=tk.LEFT, padx=6)

        self.btn_stop = tk.Button(
            player_bar,
            text="⏹ DỪNG",
            font=("Segoe UI", 9, "bold"),
            bg="#ef4444",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.stop_audio
        )
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_next = tk.Button(
            player_bar,
            text="Đoạn Tiếp ⏭",
            font=("Segoe UI", 9, "bold"),
            bg="#334155",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            command=self.next_paragraph
        )
        self.btn_next.pack(side=tk.LEFT, padx=4)

        # Status Footer
        footer = tk.Frame(self.root, bg="#020617", height=24)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#020617",
            fg="#38bdf8"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

    def update_font_size(self):
        sz = self.font_size_var.get()
        self.text_display.config(font=("Segoe UI", sz))
        self.text_display.tag_config(
            "active_para",
            font=("Segoe UI", sz, "bold")
        )

    def on_setting_changed(self, val):
        r = float(val)
        self.speed_lbl.config(text=f"{r:.1f}x")
        # If playing, restart current paragraph cleanly with new speed
        if self.is_playing:
            self.play_paragraph(self.current_para_index)

    def open_txt_file(self):
        filename = filedialog.askopenfilename(
            title="Chọn file truyện (.txt)",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                self.stop_audio()
                self.text_display.delete("1.0", tk.END)
                self.text_display.insert("1.0", content)
                self.load_paragraphs_from_text()
                self.status_var.set(f"📂 Đã mở file: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")

    def clear_text(self):
        self.stop_audio()
        self.text_display.delete("1.0", tk.END)
        self.paragraphs = []
        self.current_para_index = 0
        self.para_count_label.config(text="0 đoạn | Đoạn hiện tại: 0/0")
        self.status_var.set("Đã xóa văn bản")

    def load_paragraphs_from_text(self):
        raw = self.text_display.get("1.0", tk.END)
        lines = [line.strip() for line in raw.split("\n") if line.strip()]
        self.paragraphs = lines if lines else []
        self.current_para_index = 0
        self.update_para_counter()

    def update_para_counter(self):
        total = len(self.paragraphs)
        curr = (self.current_para_index + 1) if total > 0 else 0
        self.para_count_label.config(text=f"Tổng {total} đoạn | Đang đọc: {curr}/{total}")

    def highlight_paragraph(self, index):
        self.text_display.tag_remove("active_para", "1.0", tk.END)
        if index < 0 or index >= len(self.paragraphs):
            return

        target_text = self.paragraphs[index]
        # Find position in text widget
        start_pos = "1.0"
        while True:
            pos = self.text_display.search(target_text[:30], start_pos, stopindex=tk.END)
            if not pos:
                break
            end_pos = f"{pos}+{len(target_text)}c"
            self.text_display.tag_add("active_para", pos, end_pos)
            self.text_display.see(pos)
            break

    def stop_audio(self):
        """Cleanly stop all audio playback & synthesis threads to prevent overlap/looping"""
        with self.audio_lock:
            self.is_playing = False
            self.is_paused = False
            self.play_thread_id += 1 # Invalidate previous threads

            if HAS_PYGAME:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

            if self.current_process:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
                self.current_process = None

            self.text_display.tag_remove("active_para", "1.0", tk.END)
            self.btn_play.config(text="▶️ PHÁT (PLAY)", bg="#0284c7")
            self.status_var.set("⏹ Đã dừng phát")

    def toggle_play_pause(self):
        if self.is_playing:
            if self.is_paused:
                # Resume
                self.is_paused = False
                if HAS_PYGAME:
                    pygame.mixer.music.unpause()
                self.btn_play.config(text="⏸ TẠM DỪNG", bg="#eab308")
                self.status_var.set(f"🔊 Đang đọc đoạn {self.current_para_index + 1}...")
            else:
                # Pause
                self.is_paused = True
                if HAS_PYGAME:
                    pygame.mixer.music.pause()
                self.btn_play.config(text="▶️ TIẾP TỤC", bg="#0284c7")
                self.status_var.set("⏸ Đã tạm dừng")
        else:
            self.load_paragraphs_from_text()
            if not self.paragraphs:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập văn bản để đọc!")
                return
            self.play_paragraph(self.current_para_index)

    def prev_paragraph(self):
        if self.current_para_index > 0:
            self.play_paragraph(self.current_para_index - 1)

    def next_paragraph(self):
        if self.current_para_index < len(self.paragraphs) - 1:
            self.play_paragraph(self.current_para_index + 1)
        else:
            self.stop_audio()
            self.status_var.set("✅ Đã đọc xong toàn bộ văn bản")

    def play_paragraph(self, index):
        """Guaranteed clean paragraph playback with zero audio overlap"""
        self.stop_audio()

        if index < 0 or index >= len(self.paragraphs):
            return

        self.current_para_index = index
        self.update_para_counter()
        self.highlight_paragraph(index)

        self.is_playing = True
        self.is_paused = False
        self.btn_play.config(text="⏸ TẠM DỪNG", bg="#eab308")

        thread_id = self.play_thread_id
        text_content = self.paragraphs[index]

        thread = threading.Thread(
            target=self._synthesize_and_play_worker,
            args=(text_content, thread_id),
            daemon=True
        )
        thread.start()

    def _synthesize_and_play_worker(self, text, thread_id):
        # 1. Check thread validity
        if thread_id != self.play_thread_id or not self.is_playing:
            return

        temp_wav = os.path.join(self.base_dir, f"temp_para_{thread_id}.wav")

        try:
            self.root.after(0, lambda: self.status_var.set(f"⏳ Đang xử lý Piper AI đoạn {self.current_para_index + 1}..."))
            
            rate = self.speed_var.get()
            length_scale = 1.0 / max(0.5, min(2.0, rate))

            # Run Piper Process
            proc = subprocess.Popen(
                [self.piper_exe, "--model", self.model_path, "--output_file", temp_wav, "--length_scale", str(length_scale)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            
            with self.audio_lock:
                if thread_id != self.play_thread_id:
                    proc.kill()
                    return
                self.current_process = proc

            proc.communicate(input=text)

            if thread_id != self.play_thread_id or not self.is_playing:
                self._cleanup_file(temp_wav)
                return

            if not os.path.exists(temp_wav):
                self.root.after(0, lambda: self.status_var.set("❌ Lỗi: Không thể tổng hợp âm thanh"))
                return

            # 2. Play Audio
            self.root.after(0, lambda: self.status_var.set(f"🔊 Đang đọc đoạn {self.current_para_index + 1}/{len(self.paragraphs)}..."))

            if HAS_PYGAME:
                pygame.mixer.music.load(temp_wav)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() or self.is_paused:
                    if thread_id != self.play_thread_id or not self.is_playing:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.05)
            else:
                winsound.PlaySound(temp_wav, winsound.SND_FILENAME)

            self._cleanup_file(temp_wav)

            # 3. Auto-advance to next paragraph if still valid thread
            if thread_id == self.play_thread_id and self.is_playing and not self.is_paused:
                self.root.after(100, self.next_paragraph)

        except Exception as e:
            print(f"Error in paragraph worker: {e}")
            self._cleanup_file(temp_wav)

    def _cleanup_file(self, filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = StandalonePiperDesktopApp(root)
    root.mainloop()

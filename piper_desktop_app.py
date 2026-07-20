import os
import sys
import time
import glob
import subprocess
import threading
import asyncio
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Try loading pygame for robust audio playback
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception:
    import winsound

# Try loading edge-tts for Neural HD Vietnamese voices
HAS_EDGE_TTS = False
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    pass

# Try loading sherpa_kokoro_tts helper
HAS_SHERPA = False
try:
    import sherpa_kokoro_tts
    HAS_SHERPA = True
except ImportError:
    pass

class MultiEngineDesktopReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng Dụng Đọc Truyện Tiếng Việt Multi-Engine Desktop (Sherpa-ONNX, Kokoro & Piper)")
        self.root.geometry("950x700")
        self.root.minsize(750, 550)

        # Base path detection
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Detect Piper.exe
        default_piper = os.path.join(self.base_dir, "piper", "piper.exe")
        if not os.path.exists(default_piper):
            default_piper = os.path.join(self.base_dir, "piper.exe")

        self.piper_exe = default_piper
        self.onnx_models = self.scan_onnx_models()

        # App Variables
        self.paragraphs = []
        self.current_para_index = 0
        self.is_playing = False
        self.is_paused = False

        self.voice_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=1.0)
        self.font_size_var = tk.IntVar(value=13)
        self.status_var = tk.StringVar(value="Sẵn sàng")

        # Thread Safety & Process tracking
        self.current_process = None
        self.audio_lock = threading.Lock()
        self.play_thread_id = 0

        self.setup_ui()

    def scan_onnx_models(self):
        models = glob.glob(os.path.join(self.base_dir, "*.onnx"))
        model_dict = {}
        for m in models:
            filename = os.path.basename(m)
            model_dict[filename] = m
        return model_dict

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
            text="🎧 Đọc Truyện Multi-Engine (Sherpa-ONNX, Kokoro-82M, Edge Neural & Piper)",
            font=("Segoe UI", 12, "bold"),
            bg=self.bg_dark,
            fg=self.accent_blue
        )
        title.pack(side=tk.LEFT)

        # Settings Bar
        settings_frame = tk.Frame(self.root, bg=self.card_bg, padding=8)
        settings_frame.pack(fill=tk.X)

        # Voice Selector Dropdown
        tk.Label(settings_frame, text="Giọng Đọc:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#e2e8f0").pack(side=tk.LEFT, padx=(5, 2))
        
        self.voice_map = {
            "🌟 Microsoft Hoài My (Neural Nữ - Đọc Truyện)": "edge_hoaimy",
            "🌟 Microsoft Nam Minh (Neural Nam - Trầm Ấm)": "edge_namminh",
            "🚀 Sherpa-ONNX Tiếng Việt Engine (K2-FSA Kaldi)": "sherpa_onnx",
            "🔥 Kokoro-82M AI Tiếng Việt (anphunl/Kokoro)": "kokoro_vi",
        }

        # Add all detected ONNX models to voice options
        for name, path in self.onnx_models.items():
            display_name = f"⚡ Piper AI Model: {name}"
            self.voice_map[display_name] = path

        voice_list = list(self.voice_map.keys())
        self.voice_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.voice_var,
            values=voice_list,
            state="readonly",
            width=50
        )
        if voice_list:
            self.voice_combo.current(0)
        self.voice_combo.pack(side=tk.LEFT, padx=5)
        self.voice_combo.bind("<<ComboboxSelected>>", self.on_voice_changed)

        # Speed Slider
        tk.Label(settings_frame, text="Tốc độ:", font=("Segoe UI", 9), bg=self.card_bg, fg="#94a3b8").pack(side=tk.LEFT, padx=(15, 2))
        self.speed_scale = ttk.Scale(
            settings_frame,
            from_=0.5,
            to=2.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=90,
            command=self.on_setting_changed
        )
        self.speed_scale.pack(side=tk.LEFT, padx=2)

        self.speed_lbl = tk.Label(settings_frame, text="1.0x", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.accent_blue)
        self.speed_lbl.pack(side=tk.LEFT, padx=(0, 10))

        # Font Size
        tk.Label(settings_frame, text="Cỡ chữ:", font=("Segoe UI", 9), bg=self.card_bg, fg="#94a3b8").pack(side=tk.LEFT, padx=(5, 2))
        font_spin = ttk.Spinbox(
            settings_frame,
            from_=9,
            to=24,
            textvariable=self.font_size_var,
            width=3,
            command=self.update_font_size
        )
        font_spin.pack(side=tk.LEFT, padx=2)

        # Toolbar Frame
        toolbar = tk.Frame(self.root, bg="#334155", padding=6)
        toolbar.pack(fill=tk.X)

        btn_open = tk.Button(
            toolbar,
            text="📂 Mở File Truyện (.txt)",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            command=self.open_txt_file
        )
        btn_open.pack(side=tk.LEFT, padx=5)

        btn_clear = tk.Button(
            toolbar,
            text="🗑️ Xóa hết",
            font=("Segoe UI", 9),
            bg="#64748b",
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=3,
            command=self.clear_text
        )
        btn_clear.pack(side=tk.LEFT, padx=5)

        self.para_count_label = tk.Label(
            toolbar,
            text="0 đoạn | Đoạn hiện tại: 0/0",
            font=("Segoe UI", 9),
            bg="#334155",
            fg="#cbd5e1"
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
            "Chào mừng bạn đến với Ứng Dụng Đọc Truyện Tiếng Việt Multi-Engine!\n\n"
            "Ứng dụng tự động tích hợp các mô hình giọng đọc Tiếng Việt như Microsoft Hoài My, "
            "Nam Minh Neural và các file model Piper AI (ONNX) có sẵn trong thư mục.\n\n"
            "Bạn có thể mở bất kỳ file truyện chữ .txt nào để đọc mượt mà 100% không cần mạng."
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
            text="▶️ PHÁT (PLAY)",
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

    def on_voice_changed(self, event=None):
        if self.is_playing:
            self.play_paragraph(self.current_para_index)

    def on_setting_changed(self, val):
        r = float(val)
        self.speed_lbl.config(text=f"{r:.1f}x")
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
            self.play_thread_id += 1

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
                self.is_paused = False
                if HAS_PYGAME:
                    pygame.mixer.music.unpause()
                self.btn_play.config(text="⏸ TẠM DỪNG", bg="#eab308")
                self.status_var.set(f"🔊 Đang đọc đoạn {self.current_para_index + 1}...")
            else:
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
        selected_display = self.voice_combo.get()
        voice_target = self.voice_map.get(selected_display, "edge_hoaimy")

        thread = threading.Thread(
            target=self._synthesize_and_play_worker,
            args=(text_content, voice_target, thread_id),
            daemon=True
        )
        thread.start()

    def _synthesize_and_play_worker(self, text, voice_target, thread_id):
        if thread_id != self.play_thread_id or not self.is_playing:
            return

        temp_audio = os.path.join(self.base_dir, f"temp_para_{thread_id}.mp3")

        try:
            self.root.after(0, lambda: self.status_var.set(f"⏳ Đang xử lý âm thanh đoạn {self.current_para_index + 1}..."))
            rate = self.speed_var.get()
            success = False

            # Option A: Edge Neural Voices
            if voice_target in ["edge_hoaimy", "edge_namminh"] and HAS_EDGE_TTS:
                edge_voice = "vi-VN-NamMinhNeural" if voice_target == "edge_namminh" else "vi-VN-HoaiMyNeural"
                rate_pct = int((rate - 1.0) * 100)
                rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

                async def run_edge():
                    comm = edge_tts.Communicate(text, edge_voice, rate=rate_str)
                    await comm.save(temp_audio)

                try:
                    asyncio.run(run_edge())
                    if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
                        success = True
                except Exception as edge_err:
                    print("Edge TTS synthesis failed:", edge_err)

            # Option B: Piper AI Local Model
            if not success:
                model_file = voice_target if os.path.exists(voice_target) else self.model_path
                temp_audio = os.path.join(self.base_dir, f"temp_para_{thread_id}.wav")
                length_scale = 1.0 / max(0.5, min(2.0, rate))

                proc = subprocess.Popen(
                    [self.piper_exe, "--model", model_file, "--output_file", temp_audio, "--length_scale", str(length_scale)],
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
                if os.path.exists(temp_audio) and os.path.getsize(temp_audio) > 0:
                    success = True

            if thread_id != self.play_thread_id or not self.is_playing:
                self._cleanup_file(temp_audio)
                return

            if not success or not os.path.exists(temp_audio):
                self.root.after(0, lambda: self.status_var.set("❌ Lỗi: Không thể tổng hợp âm thanh"))
                return

            # Play Audio
            self.root.after(0, lambda: self.status_var.set(f"🔊 Đang đọc đoạn {self.current_para_index + 1}/{len(self.paragraphs)}..."))

            if HAS_PYGAME:
                pygame.mixer.music.load(temp_audio)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() or self.is_paused:
                    if thread_id != self.play_thread_id or not self.is_playing:
                        pygame.mixer.music.stop()
                        break
                    time.sleep(0.05)
            else:
                winsound.PlaySound(temp_audio, winsound.SND_FILENAME)

            self._cleanup_file(temp_audio)

            # Auto-advance to next paragraph
            if thread_id == self.play_thread_id and self.is_playing and not self.is_paused:
                self.root.after(100, self.next_paragraph)

        except Exception as e:
            print(f"Error in paragraph worker: {e}")
            self._cleanup_file(temp_audio)

    def _cleanup_file(self, filepath):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiEngineDesktopReader(root)
    root.mainloop()

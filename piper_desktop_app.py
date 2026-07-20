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
        self.root.title("🎧 Đọc Truyện AI Pro - VietVoice Studio")
        self.root.geometry("980x720")
        self.root.minsize(760, 560)

        # Base path detection
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Load App Icon if available
        try:
            icon_candidates = [
                os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "app_icon.ico"),
                os.path.join(self.base_dir, "app_icon.ico"),
                os.path.join(os.getcwd(), "app_icon.ico")
            ]
            for ic in icon_candidates:
                if os.path.exists(ic):
                    self.root.iconbitmap(ic)
                    break
        except Exception as e:
            print("Icon loading warning:", e)

        candidate_dirs = [
            os.path.dirname(os.path.abspath(sys.argv[0])),
            os.getcwd(),
            self.base_dir,
            os.path.dirname(self.base_dir),
            os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))),
            getattr(sys, '_MEIPASS', '')
        ]

        # Detect Piper.exe
        self.piper_exe = None
        for d in candidate_dirs:
            if not d:
                continue
            p1 = os.path.join(d, "piper", "piper.exe")
            p2 = os.path.join(d, "piper.exe")
            if os.path.exists(p1):
                self.piper_exe = p1
                break
            elif os.path.exists(p2):
                self.piper_exe = p2
                break

        if not self.piper_exe:
            self.piper_exe = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "piper", "piper.exe")

        # Detect Default ONNX Model
        self.model_path = None
        for d in candidate_dirs:
            if not d:
                continue
            m = os.path.join(d, "vi_VN-vais1000-medium.onnx")
            if os.path.exists(m):
                self.model_path = m
                break

        if not self.model_path:
            self.model_path = os.path.join(self.base_dir, "vi_VN-vais1000-medium.onnx")

        self.onnx_models = self.scan_onnx_models()

        # App Variables
        self.paragraphs = []
        self.current_para_index = 0
        self.is_playing = False
        self.is_paused = False

        self.voice_var = tk.StringVar()
        self.speed_var = tk.DoubleVar(value=1.0)
        self.font_size_var = tk.IntVar(value=13)
        self.sentences_per_chunk_var = tk.IntVar(value=5)
        self.status_var = tk.StringVar(value="Sẵn sàng")

        # Trace setting variables to auto-apply immediately
        self.font_size_var.trace_add("write", self.update_font_size)
        self.sentences_per_chunk_var.trace_add("write", self.on_chunk_setting_changed)

        # Thread Safety & Process tracking
        self.current_process = None
        self.audio_lock = threading.Lock()
        self.play_thread_id = 0

        self.setup_ui()

    def scan_onnx_models(self):
        search_dirs = [
            self.base_dir,
            os.getcwd(),
            os.path.dirname(self.base_dir),
            os.path.dirname(os.path.abspath(sys.argv[0]))
        ]
        model_dict = {}
        for d in search_dirs:
            if d and os.path.exists(d):
                models = glob.glob(os.path.join(d, "*.onnx"))
                for m in models:
                    filename = os.path.basename(m)
                    model_dict[filename] = m

        if not model_dict:
            default_m = os.path.join(self.base_dir, "vi_VN-vais1000-medium.onnx")
            model_dict["vi_VN-vais1000-medium.onnx"] = default_m
        return model_dict

    def setup_ui(self):
        # Configure Premium Dark Color Palette
        self.bg_dark = "#090d16"
        self.card_bg = "#131b2e"
        self.accent_blue = "#38bdf8"
        self.accent_cyan = "#06b6d4"
        self.accent_green = "#10b981"
        self.accent_amber = "#f59e0b"
        self.accent_rose = "#ef4444"
        self.fg_light = "#f8fafc"
        self.fg_muted = "#94a3b8"

        self.root.configure(bg=self.bg_dark)

        # Style TTK Widgets
        style = ttk.Style()
        style.theme_use("clam")

        # Configure Combobox Style
        style.configure("TCombobox", fieldbackground="#1e293b", background="#334155", foreground="#f8fafc", darkcolor="#1e293b", lightcolor="#334155")
        style.map("TCombobox", fieldbackground=[("readonly", "#1e293b")], foreground=[("readonly", "#f8fafc")])

        # Status Footer (Pack to BOTTOM first)
        footer = tk.Frame(self.root, bg="#050811", height=26)
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "bold"),
            bg="#050811",
            fg=self.accent_blue
        )
        self.status_label.pack(side=tk.LEFT, padx=12)

        # Bottom Player Navigation Control Bar (Pack to BOTTOM second)
        player_bar = tk.Frame(self.root, bg=self.card_bg, padx=12, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        player_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(2, 6))

        self.btn_prev = tk.Button(
            player_bar,
            text="⏮ Đoạn Trước",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            activebackground="#334155",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.prev_paragraph
        )
        self.btn_prev.pack(side=tk.LEFT, padx=4)

        self.btn_play = tk.Button(
            player_bar,
            text="▶️ PHÁT (PLAY)",
            font=("Segoe UI", 11, "bold"),
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            relief=tk.FLAT,
            padx=24,
            pady=6,
            cursor="hand2",
            command=self.toggle_play_pause
        )
        self.btn_play.pack(side=tk.LEFT, padx=8)

        self.btn_stop = tk.Button(
            player_bar,
            text="⏹ DỪNG",
            font=("Segoe UI", 9, "bold"),
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.stop_audio
        )
        self.btn_stop.pack(side=tk.LEFT, padx=4)

        self.btn_next = tk.Button(
            player_bar,
            text="Đoạn Tiếp ⏭",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8",
            activebackground="#334155",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.next_paragraph
        )
        self.btn_next.pack(side=tk.LEFT, padx=4)

        # Progress Bar Frame (Pack to BOTTOM third)
        prog_frame = tk.Frame(self.root, bg=self.card_bg, padx=12, pady=4)
        prog_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=2)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            prog_frame,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            maximum=100,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, expand=True)

        # Top Header Card Bar (Pack to TOP)
        header = tk.Frame(self.root, bg="#0d1527", padx=16, pady=12, highlightthickness=1, highlightbackground="#1e293b")
        header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))

        title_box = tk.Frame(header, bg="#0d1527")
        title_box.pack(side=tk.LEFT)

        title = tk.Label(
            title_box,
            text="🎧 ĐỌC TRUYỆN AI PRO (VIETVOICE STUDIO)",
            font=("Segoe UI", 13, "bold"),
            bg="#0d1527",
            fg=self.accent_blue
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            title_box,
            text="Phần mềm đọc truyện chữ Tiếng Việt đa giọng đọc & Offline 100%",
            font=("Segoe UI", 9),
            bg="#0d1527",
            fg=self.fg_muted
        )
        subtitle.pack(anchor="w")

        # Engine Badge
        badge = tk.Label(
            header,
            text="🟢 Engine Sẵn Sàng",
            font=("Segoe UI", 9, "bold"),
            bg="#064e3b",
            fg="#6ee7b7",
            padx=10,
            pady=4
        )
        badge.pack(side=tk.RIGHT)

        # Settings Card Bar (Pack to TOP)
        settings_frame = tk.Frame(self.root, bg=self.card_bg, padx=12, pady=10, highlightthickness=1, highlightbackground="#1e293b")
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Voice Selector Dropdown
        tk.Label(settings_frame, text="🎙️ Giọng Đọc:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#e2e8f0").pack(side=tk.LEFT, padx=(5, 4))
        
        self.voice_map = {
            "🌟 Microsoft Hoài My (Neural Nữ - Đọc Truyện)": "edge_hoaimy",
            "🌟 Microsoft Nam Minh (Neural Nam - Trầm Ấm)": "edge_namminh",
            "⚡ Piper AI Offline (Cục bộ - vais1000)": "piper_local",
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
            width=46
        )
        if voice_list:
            self.voice_combo.current(0)
        self.voice_combo.pack(side=tk.LEFT, padx=5)
        self.voice_combo.bind("<<ComboboxSelected>>", self.on_voice_changed)

        # Speed Slider
        tk.Label(settings_frame, text="⚡ Tốc độ:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#94a3b8").pack(side=tk.LEFT, padx=(15, 2))
        self.speed_scale = ttk.Scale(
            settings_frame,
            from_=0.5,
            to=5.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=95,
            command=self.on_setting_changed
        )
        self.speed_scale.pack(side=tk.LEFT, padx=2)

        self.speed_lbl = tk.Label(settings_frame, text="1.0x", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.accent_blue)
        self.speed_lbl.pack(side=tk.LEFT, padx=(2, 10))

        # Font Size Spinbox
        tk.Label(settings_frame, text="🔤 Cỡ chữ:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#94a3b8").pack(side=tk.LEFT, padx=(5, 2))
        font_spin = ttk.Spinbox(
            settings_frame,
            from_=9,
            to=24,
            textvariable=self.font_size_var,
            width=3,
            command=self.update_font_size
        )
        font_spin.pack(side=tk.LEFT, padx=2)

        # Sentences Per Chunk Spinbox
        tk.Label(settings_frame, text="📝 Câu/đoạn:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#94a3b8").pack(side=tk.LEFT, padx=(10, 2))
        chunk_spin = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=50,
            textvariable=self.sentences_per_chunk_var,
            width=3,
            command=self.on_chunk_setting_changed
        )
        chunk_spin.pack(side=tk.LEFT, padx=2)

        # Toolbar Frame (Pack to TOP)
        toolbar = tk.Frame(self.root, bg="#1e293b", padx=10, pady=8, highlightthickness=1, highlightbackground="#334155")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=2)

        btn_open = tk.Button(
            toolbar,
            text="📂 Mở File Truyện (.txt)",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.open_txt_file
        )
        btn_open.pack(side=tk.LEFT, padx=5)

        btn_clear = tk.Button(
            toolbar,
            text="🗑️ Xóa hết",
            font=("Segoe UI", 9),
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.clear_text
        )
        btn_clear.pack(side=tk.LEFT, padx=5)

        btn_export = tk.Button(
            toolbar,
            text="💾 Xuất File MP3 / WAV",
            font=("Segoe UI", 9, "bold"),
            bg="#8b5cf6",
            fg="white",
            activebackground="#7c3aed",
            activeforeground="white",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.export_audio_file
        )
        btn_export.pack(side=tk.LEFT, padx=5)

        self.para_count_label = tk.Label(
            toolbar,
            text="📖 0 đoạn | Đoạn hiện tại: 0/0",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#38bdf8"
        )
        self.para_count_label.pack(side=tk.RIGHT, padx=10)

        # Main Reader Text Display Container (Pack LAST to fill REMAINING MIDDLE SPACE)
        main_frame = tk.Frame(self.root, bg="#050811", highlightthickness=1, highlightbackground="#1e293b")
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.text_display = tk.Text(
            main_frame,
            wrap=tk.WORD,
            font=("Segoe UI", self.font_size_var.get()),
            bg="#050811",
            fg="#e2e8f0",
            insertbackground="white",
            selectbackground="#2563eb",
            selectforeground="white",
            padx=18,
            pady=18,
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

    def update_font_size(self, *args):
        try:
            sz = int(self.font_size_var.get())
            sz = max(8, min(40, sz))
            self.text_display.config(font=("Segoe UI", sz))
            if hasattr(self, 'paragraphs'):
                for idx in range(len(self.paragraphs)):
                    self.text_display.tag_config(f"body_{idx}", font=("Segoe UI", sz))
        except Exception:
            pass

    def on_voice_changed(self, event=None):
        if self.is_playing:
            self.play_paragraph(self.current_para_index)

    def on_setting_changed(self, val):
        try:
            r = float(val)
            self.speed_lbl.config(text=f"{r:.1f}x")
        except Exception:
            pass

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
        if not raw.strip():
            self.paragraphs = []
            self.current_para_index = 0
            self.update_para_counter()
            return

        sentences = []
        buffer = ""
        length = len(raw)

        for i in range(length):
            char = raw[i]
            buffer += char
            is_delimiter = False

            if char in ["!", "?", "\n"]:
                is_delimiter = True
            elif char == ".":
                next_char = raw[i + 1] if i < length - 1 else None
                prev_char = raw[i - 1] if i > 0 else None
                if next_char != "." and prev_char != ".":
                    is_delimiter = True

            if is_delimiter:
                cleaned = buffer.strip()
                if len(cleaned) >= 3:
                    sentences.append(cleaned)
                    buffer = ""

        leftover = buffer.strip()
        if leftover:
            if len(leftover) < 3 and len(sentences) > 0:
                sentences[-1] += " " + leftover
            else:
                sentences.append(leftover)

        if not sentences and raw.strip():
            sentences.append(raw.strip())

        # Group sentences into chunks based on sentences_per_chunk_var
        sentences_per_chunk = max(1, self.sentences_per_chunk_var.get())
        chunks = []
        curr_chunk = ""
        count = 0

        for s in sentences:
            curr_chunk += (" " if curr_chunk else "") + s
            count += 1
            if count >= sentences_per_chunk:
                chunks.append(curr_chunk)
                curr_chunk = ""
                count = 0

        if curr_chunk:
            chunks.append(curr_chunk)

        self.paragraphs = chunks if chunks else sentences
        self.current_para_index = 0
        self.render_paragraphs()
        self.update_para_counter()

    def render_paragraphs(self):
        """Renders paragraphs as distinct visual cards with #1, #2 headers just like the web version"""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete("1.0", tk.END)

        for idx, p_text in enumerate(self.paragraphs):
            header_str = f"#{idx + 1}\n"
            body_str = f"{p_text}\n\n"
            
            self.text_display.insert(tk.END, header_str, f"header_{idx}")
            self.text_display.tag_config(f"header_{idx}", font=("Consolas", 9, "bold"), foreground="#475569")

            self.text_display.insert(tk.END, body_str, f"body_{idx}")
            self.text_display.tag_config(f"body_{idx}", font=("Segoe UI", self.font_size_var.get()), foreground="#cbd5e1")

        # Bind click to play paragraph
        self.text_display.bind("<Button-1>", self.on_text_click)

    def on_text_click(self, event):
        """Click on any paragraph card to play it directly (matching web behavior)"""
        try:
            index_str = self.text_display.index(f"@{event.x},{event.y}")
            line_num = int(index_str.split(".")[0])

            current_line = 1
            for idx, p_text in enumerate(self.paragraphs):
                body_line_count = len(p_text.split("\n"))
                chunk_lines = 1 + body_line_count + 1
                if current_line <= line_num < current_line + chunk_lines:
                    self.play_paragraph(idx)
                    break
                current_line += chunk_lines
        except Exception as e:
            print("Click handler error:", e)

    def on_chunk_setting_changed(self, *args):
        try:
            val = self.sentences_per_chunk_var.get()
            if val < 1:
                return
            was_playing = self.is_playing
            curr_idx = self.current_para_index
            self.load_paragraphs_from_text()
            if was_playing and self.paragraphs:
                self.play_paragraph(min(curr_idx, len(self.paragraphs) - 1))
        except Exception:
            pass

    def update_para_counter(self):
        total = len(self.paragraphs)
        curr = (self.current_para_index + 1) if total > 0 else 0
        pct = (curr / total * 100) if total > 0 else 0
        if hasattr(self, 'progress_var'):
            self.progress_var.set(pct)
        self.para_count_label.config(text=f"📖 Tổng {total} đoạn | Đang đọc: {curr}/{total} ({pct:.0f}%)")

    def highlight_paragraph(self, index):
        if index < 0 or index >= len(self.paragraphs):
            return

        # Reset tags for all paragraph cards
        for idx in range(len(self.paragraphs)):
            self.text_display.tag_config(f"header_{idx}", font=("Consolas", 9, "bold"), foreground="#475569", background="")
            self.text_display.tag_config(f"body_{idx}", font=("Segoe UI", self.font_size_var.get()), foreground="#cbd5e1", background="")

        # Highlight active paragraph card with Deep Navy Glow & Bright Cyan Header
        self.text_display.tag_config(f"header_{index}", font=("Consolas", 10, "bold"), foreground="#38bdf8", background="#1e3a8a")
        self.text_display.tag_config(f"body_{index}", font=("Segoe UI", self.font_size_var.get(), "bold"), foreground="#ffffff", background="#1e3a8a")

        # Scroll active card cleanly into center view
        try:
            pos = self.text_display.tag_ranges(f"header_{index}")[0]
            self.text_display.see(pos)
        except Exception:
            pass

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
                length_scale = 1.0 / max(0.2, min(5.0, rate))

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
            err_msg = str(e)
            print(f"Error in paragraph worker: {err_msg}")
            self.root.after(0, lambda msg=err_msg: self.status_var.set(f"❌ Lỗi: {msg[:50]}"))
            self._cleanup_file(temp_audio)

    def export_audio_file(self):
        text_content = self.text_display.get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("Cảnh báo", "Không có văn bản để xuất file âm thanh!")
            return

        save_path = filedialog.asksaveasfilename(
            title="Lưu file âm thanh",
            defaultextension=".mp3",
            filetypes=[("MP3 Audio (*.mp3)", "*.mp3"), ("WAV Audio (*.wav)", "*.wav")]
        )
        if not save_path:
            return

        self.status_var.set("⏳ Đang tạo file âm thanh...")
        selected_display = self.voice_combo.get()
        voice_target = self.voice_map.get(selected_display, "edge_hoaimy")

        def worker():
            try:
                rate = self.speed_var.get()
                if voice_target in ["edge_hoaimy", "edge_namminh"] and HAS_EDGE_TTS:
                    edge_voice = "vi-VN-NamMinhNeural" if voice_target == "edge_namminh" else "vi-VN-HoaiMyNeural"
                    rate_pct = int((rate - 1.0) * 100)
                    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"

                    async def run_edge():
                        comm = edge_tts.Communicate(text_content, edge_voice, rate=rate_str)
                        await comm.save(save_path)

                    asyncio.run(run_edge())
                else:
                    model_file = voice_target if os.path.exists(voice_target) else self.model_path
                    length_scale = 1.0 / max(0.2, min(5.0, rate))
                    proc = subprocess.Popen(
                        [self.piper_exe, "--model", model_file, "--output_file", save_path, "--length_scale", str(length_scale)],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8"
                    )
                    proc.communicate(input=text_content)

                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    self.root.after(0, lambda: self.status_var.set(f"✅ Đã xuất file: {os.path.basename(save_path)}"))
                    self.root.after(0, lambda: messagebox.showinfo("Thành công", f"Đã xuất thành công file âm thanh:\n{save_path}"))
                else:
                    self.root.after(0, lambda: self.status_var.set("❌ Lỗi xuất file âm thanh"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: messagebox.showerror("Lỗi", f"Lỗi tạo file âm thanh: {msg}"))

        threading.Thread(target=worker, daemon=True).start()

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

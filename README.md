# 🎧 TTS Reader & Piper TTS Offline Desktop App

Ứng dụng đọc văn bản / truyện chữ Tiếng Việt cao cấp hỗ trợ cả phiên bản Web trực tuyến và ứng dụng **Piper TTS Offline 100%** trên máy tính.

---

## 🚀 1. Ứng dụng Desktop Piper TTS Offline (`piper_app.py`)

Một ứng dụng Desktop đơn giản, nhẹ và nhanh dành riêng cho Windows giúp bạn chuyển đổi văn bản / truyện chữ Tiếng Việt thành file âm thanh mà không cần kết nối mạng.

### Hướng dẫn sử dụng `piper_app.py`:

1. **Chuẩn bị file (Chỉ làm 1 lần)**:
   - Tải `piper_windows_amd64.zip` từ [Piper Releases](https://github.com/rhasspy/piper/releases/latest) và giải nén lấy file `piper.exe`.
   - Tải 2 file model tiếng Việt:
     - [vi_VN-vais1000-medium.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium.onnx)
     - [vi_VN-vais1000-medium.onnx.json](https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium.onnx.json)
   - Đặt `piper.exe` và 2 file model vào cùng thư mục dự án.

2. **Chạy ứng dụng**:
   ```bash
   python piper_app.py
   ```

3. **Tính năng**:
   - 📂 Chọn và đọc file văn bản `.txt` dài hàng trăm trang.
   - 📝 Nhập/Dán nội dung trực tiếp.
   - 🔊 Chuyển đổi thành âm thanh WAV chất lượng cao 100% offline.
   - 🎧 Mở phát âm thanh nghe ngay sau khi hoàn thành.

---

## 🌐 2. Ứng dụng Web App (`npm run dev`)

- Tích hợp giọng **Microsoft Edge Neural** (Hoài My & Nam Minh) và **Google Cloud Audio**.
- Tự động dự phòng 3 lớp đảm bảo phát âm thanh luôn mượt mà.

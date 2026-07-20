import os
import urllib.request
import sys

# Automated Downloader for Extra Vietnamese Piper ONNX Models

MODELS = [
    {
        "name": "vi_VN-vais1000-medium.onnx",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium.onnx"
    },
    {
        "name": "vi_VN-vivos-x_low.onnx",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/vivos/x_low/vi_VN-vivos-x_low.onnx"
    },
    {
        "name": "vi_VN-25hours-single-medium.onnx",
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/vi/vi_VN/25hours/single/medium/vi_VN-25hours-single-medium.onnx"
    },
    {
        "name": "vi_VN-25hours-single-medium.onnx.json",
        "url": "https://huggingface.co/rhasspy/piper-voices/raw/main/vi/vi_VN/25hours/single/medium/vi_VN-25hours-single-medium.onnx.json"
    },
    {
        "name": "vits-piper-vi_VN-vais1000-medium.tar.bz2",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-vi_VN-vais1000-medium.tar.bz2"
    }
]

def download_file(url, filename):
    print(f"⏳ Đang tải: {filename} ...")
    def report(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
        sys.stdout.write(f"\rProgress: {percent}% [{count * block_size} / {total_size} bytes]")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, filename, reporthook=report)
        print(f"\n✅ Đã tải xong: {filename}")
    except Exception as e:
        print(f"\n❌ Lỗi khi tải {filename}: {e}")

if __name__ == "__main__":
    print("==================================================")
    print("  TỰ ĐỘNG TẢI MÔ HÌNH GIỌNG ĐỌC TIẾNG VIỆT PIPER  ")
    print("==================================================")
    for m in MODELS:
        if not os.path.exists(m["name"]):
            download_file(m["url"], m["name"])
        else:
            print(f"✅ Đã có sẵn: {m['name']}")
    print("\n🎉 Hoàn tất! Các model đã sẵn sàng trong ứng dụng.")

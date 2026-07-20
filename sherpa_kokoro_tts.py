import os
import sys
import subprocess

# Sherpa-ONNX & Kokoro-82M Vietnamese TTS Helper Integration

def check_sherpa_installed():
    try:
        import sherpa_onnx
        return True
    except ImportError:
        return False

def check_kokoro_installed():
    try:
        import kokoro
        return True
    except ImportError:
        return False

def install_dependencies():
    print("⏳ Đang cài đặt thư viện sherpa-onnx và kokoro...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sherpa-onnx", "kokoro", "soundfile"])
        print("✅ Đã cài đặt xong thư viện!")
        return True
    except Exception as e:
        print(f"❌ Lỗi cài đặt: {e}")
        return False

def synthesize_sherpa_onnx(text, model_dir, output_wav):
    """
    Synthesize text using Sherpa-ONNX Vietnamese model
    """
    import sherpa_onnx
    import soundfile as sf

    tokens_path = os.path.join(model_dir, "tokens.txt")
    model_path = os.path.join(model_dir, "model.onnx")

    if not os.path.exists(tokens_path) or not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy file model.onnx hoặc tokens.txt trong {model_dir}")

    tts_config = sherpa_onnx.OfflineTtsVitsModelConfig(
        model=model_path,
        tokens=tokens_path,
        data_dir=model_dir
    )
    config = sherpa_onnx.OfflineTtsModelConfig(vits=tts_config)
    tts = sherpa_onnx.OfflineTts(config)

    audio = tts.generate(text)
    sf.write(output_wav, audio.samples, audio.sample_rate)
    return output_wav

if __name__ == "__main__":
    print("Checking Sherpa-ONNX & Kokoro integration status...")
    print("Sherpa-ONNX:", check_sherpa_installed())
    print("Kokoro-82M:", check_kokoro_installed())

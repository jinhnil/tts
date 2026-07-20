import { NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";

export async function POST(req: Request) {
  try {
    const { text, rate = 1.0 } = await req.json();

    if (!text || text.trim() === "") {
      return NextResponse.json({ error: "Văn bản rỗng" }, { status: 400 });
    }

    const baseDir = process.cwd();
    let piperExec = path.join(baseDir, "piper", "piper.exe");
    if (!fs.existsSync(piperExec)) {
      piperExec = path.join(baseDir, "piper.exe");
    }

    const modelPath = path.join(baseDir, "vi_VN-vais1000-medium.onnx");

    if (!fs.existsSync(piperExec)) {
      return NextResponse.json(
        { error: "Không tìm thấy file piper/piper.exe" },
        { status: 404 }
      );
    }

    if (!fs.existsSync(modelPath)) {
      return NextResponse.json(
        { error: "Không tìm thấy file vi_VN-vais1000-medium.onnx" },
        { status: 404 }
      );
    }

    const tempWav = path.join(baseDir, `temp_piper_${Date.now()}_${Math.random().toString(36).slice(2)}.wav`);
    const lengthScale = 1.0 / Math.max(0.5, Math.min(2.0, rate));

    await new Promise<void>((resolve, reject) => {
      const proc = spawn(piperExec, [
        "--model", modelPath,
        "--output_file", tempWav,
        "--length_scale", String(lengthScale),
      ]);

      proc.stdin.write(text);
      proc.stdin.end();

      proc.on("close", (code) => {
        if (code === 0) resolve();
        else reject(new Error(`Piper process exited with code ${code}`));
      });
      proc.on("error", reject);
    });

    if (!fs.existsSync(tempWav)) {
      return NextResponse.json(
        { error: "Tạo file âm thanh Piper thất bại" },
        { status: 500 }
      );
    }

    const audioBuffer = fs.readFileSync(tempWav);
    try {
      fs.unlinkSync(tempWav);
    } catch {}

    return new Response(audioBuffer, {
      headers: {
        "Content-Type": "audio/wav",
        "Content-Length": String(audioBuffer.length),
      },
    });
  } catch (err: any) {
    console.error("API Piper Error:", err);
    return NextResponse.json(
      { error: err?.message || "Piper synthesis error" },
      { status: 500 }
    );
  }
}

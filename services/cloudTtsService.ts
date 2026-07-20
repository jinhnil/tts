// Cloud TTS Service supporting Microsoft Edge Neural Voices (Hoài My & Nam Minh) + Google Vietnamese Audio
import { speakWebSpeech } from "./webSpeechService";

export interface CloudVoice {
  id: string;
  name: string;
  gender: string;
  provider: "edge" | "google";
}

export const CLOUD_VOICES: CloudVoice[] = [
  {
    id: "edge_hoaimy",
    name: "Microsoft Hoài My (Neural Nữ - Edge)",
    gender: "Nữ",
    provider: "edge",
  },
  {
    id: "edge_namminh",
    name: "Microsoft Nam Minh (Neural Nam - Edge)",
    gender: "Nam",
    provider: "edge",
  },
  {
    id: "google_vi",
    name: "Google Tiếng Việt (Audio Cloud)",
    gender: "Nữ",
    provider: "google",
  },
];

let activeAudio: HTMLAudioElement | null = null;
let activeWebSocket: WebSocket | null = null;
let isCancelled = false;

export const stopCloudTTS = () => {
  isCancelled = true;
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }
  if (activeWebSocket) {
    try {
      activeWebSocket.close();
    } catch {}
    activeWebSocket = null;
  }
};

export const pauseCloudTTS = () => {
  if (activeAudio && !activeAudio.paused) {
    activeAudio.pause();
  }
};

export const resumeCloudTTS = () => {
  if (activeAudio && activeAudio.paused) {
    activeAudio.play().catch(() => {});
  }
};

const escapeXml = (unsafe: string): string => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
};

const generateRequestId = (): string => {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

/**
 * Split long text into chunks of maxLen chars
 */
const splitText = (text: string, maxLen = 150): string[] => {
  if (!text || text.length <= maxLen) return [text];
  const sentences = text.match(/[^.!?\n]+[.!?\n]*|\n+/g) || [text];
  const subTexts: string[] = [];
  let current = "";

  for (const s of sentences) {
    if ((current + s).length > maxLen && current.trim().length > 0) {
      subTexts.push(current.trim());
      current = s;
    } else {
      current += s;
    }
  }
  if (current.trim().length > 0) {
    subTexts.push(current.trim());
  }
  return subTexts.length > 0 ? subTexts : [text];
};

/**
 * Synthesize Edge Neural Voice via WebSocket or fallback to Google Audio
 */
const synthesizeEdgeSpeech = (
  text: string,
  voiceName: string, // 'vi-VN-HoaiMyNeural' or 'vi-VN-NamMinhNeural'
  rate: number,
  volume: number,
): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const wsUrl =
      "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1?TrustedClientToken=6A5AA1D4EA6349499208C2C5004A0D8D";

    const ws = new WebSocket(wsUrl);
    activeWebSocket = ws;

    const audioChunks: Uint8Array[] = [];
    const requestId = generateRequestId();

    const timeoutTimer = setTimeout(() => {
      try {
        ws.close();
      } catch {}
      reject(new Error("WebSocket synthesis timeout"));
    }, 8000);

    ws.onopen = () => {
      // 1. Send speech config
      const configMsg =
        `Path: speech.config\r\nX-RequestId: ${requestId}\r\nContent-Type: application/json; charset=utf-8\r\n\r\n` +
        JSON.stringify({
          context: {
            synthesis: {
              audio: {
                metadataversion: "2020-02-25",
                format: "audio-24khz-48kbitrate-mono-mp3",
              },
            },
          },
        });
      ws.send(configMsg);

      // 2. Send SSML
      const ratePct = Math.round((rate - 1.0) * 100);
      const rateStr = ratePct >= 0 ? `+${ratePct}%` : `${ratePct}%`;

      const ssml =
        `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='vi-VN'>` +
        `<voice name='${voiceName}'><prosody rate='${rateStr}' pitch='0%'>` +
        `${escapeXml(text)}` +
        `</prosody></voice></speak>`;

      const ssmlMsg =
        `Path: ssml\r\nX-RequestId: ${requestId}\r\nContent-Type: application/ssml+xml\r\n\r\n` +
        ssml;
      ws.send(ssmlMsg);
    };

    ws.onmessage = async (event) => {
      if (event.data instanceof Blob) {
        const buffer = await event.data.arrayBuffer();
        const view = new DataView(buffer);
        const headerLength = view.getUint16(0);

        if (buffer.byteLength > headerLength + 2) {
          const audioData = new Uint8Array(buffer.slice(headerLength + 2));
          audioChunks.push(audioData);
        }
      } else if (typeof event.data === "string") {
        if (event.data.includes("Path:turn.end")) {
          clearTimeout(timeoutTimer);
          try {
            ws.close();
          } catch {}
          if (audioChunks.length > 0) {
            const blob = new Blob(audioChunks, { type: "audio/mp3" });
            resolve(blob);
          } else {
            reject(new Error("No audio chunks received"));
          }
        }
      }
    };

    ws.onerror = (err) => {
      clearTimeout(timeoutTimer);
      reject(err);
    };
  });
};

/**
 * Play Google Translate Audio chunk
 */
const playGoogleAudioChunk = (
  text: string,
  rate: number,
  volume: number,
): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (isCancelled) return resolve();
    const encoded = encodeURIComponent(text);
    const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=vi&client=tw-ob`;

    const audio = new Audio(url);
    activeAudio = audio;
    audio.playbackRate = Math.max(0.5, Math.min(2.0, rate));
    audio.volume = Math.max(0, Math.min(1, volume / 100));

    audio.onended = () => {
      resolve();
    };
    audio.onerror = (e) => {
      reject(e);
    };
    audio.play().catch(reject);
  });
};

/**
 * Main function to speak text using chosen Cloud Voice
 */
export const speakCloudTTS = (
  text: string,
  voiceId: string, // 'edge_hoaimy' | 'edge_namminh' | 'google_vi'
  rate: number,
  volume: number,
  onEnd: () => void,
  onError: (err: any) => void,
  onProgress?: (percentage: number) => void,
) => {
  stopCloudTTS();
  isCancelled = false;

  const subTexts = splitText(text, 150);
  const totalLength = text.length || 1;
  const charOffsets: number[] = [0];
  for (let i = 0; i < subTexts.length - 1; i++) {
    charOffsets.push(charOffsets[i] + subTexts[i].length);
  }

  let index = 0;

  const playNext = async () => {
    if (index >= subTexts.length || isCancelled) {
      if (!isCancelled) onEnd();
      return;
    }

    const subText = subTexts[index];

    try {
      let playedSuccessfully = false;

      // Tier 1: Try Edge Neural WebSocket if requested
      if (voiceId === "edge_hoaimy" || voiceId === "edge_namminh") {
        const edgeVoiceName =
          voiceId === "edge_namminh"
            ? "vi-VN-NamMinhNeural"
            : "vi-VN-HoaiMyNeural";

        try {
          const audioBlob = await synthesizeEdgeSpeech(
            subText,
            edgeVoiceName,
            rate,
            volume,
          );
          if (!isCancelled) {
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            activeAudio = audio;
            audio.volume = Math.max(0, Math.min(1, volume / 100));

            await new Promise<void>((res, rej) => {
              audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                res();
              };
              audio.onerror = rej;
              audio.play().catch(rej);
            });
            playedSuccessfully = true;
          }
        } catch (wsErr) {
          console.warn("Edge Neural WS failed, trying Google Audio fallback:", wsErr);
        }
      }

      // Tier 2: Try Google Audio if Tier 1 failed or if voiceId === 'google_vi'
      if (!playedSuccessfully && !isCancelled) {
        try {
          await playGoogleAudioChunk(subText, rate, volume);
          playedSuccessfully = true;
        } catch (gErr) {
          console.warn("Google Audio fallback failed:", gErr);
        }
      }

      // Tier 3: If both Cloud methods failed, fallback to Browser WebSpeech
      if (!playedSuccessfully && !isCancelled) {
        console.warn("All Cloud TTS options failed, falling back to Browser WebSpeech");
        speakWebSpeech(
          subText,
          "",
          rate,
          volume,
          () => {
            index++;
            playNext();
          },
          (err) => {
            if (!isCancelled) onError(err);
          },
          false,
          onProgress
        );
        return;
      }

      if (isCancelled) return;

      index++;
      if (onProgress) {
        const totalRead =
          charOffsets[Math.min(index, subTexts.length - 1)] || totalLength;
        onProgress(Math.min(100, Math.floor((totalRead / totalLength) * 100)));
      }
      playNext();
    } catch (err) {
      if (!isCancelled) {
        console.error("Cloud TTS Play Final Error:", err);
        onError(err);
      }
    }
  };

  playNext();
};

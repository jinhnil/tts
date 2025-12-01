import { GoogleGenAI, Modality } from "@google/genai";
import { GeminiVoice } from '../types';

const MAX_RETRIES = 3;
const INITIAL_DELAY_MS = 1000;

const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const generateSpeech = async (
  text: string,
  voice: GeminiVoice,
  apiKey: string
): Promise<ArrayBuffer> => {
  const key = apiKey || process.env.API_KEY;
  
  if (!key) {
    throw new Error("Chưa nhập API Key. Vui lòng vào Cài đặt để nhập khóa API Google Gemini.");
  }

  if (!text || text.trim().length === 0) {
      // Return empty buffer or handle gracefully
      return new ArrayBuffer(0);
  }

  const ai = new GoogleGenAI({ apiKey: key });

  let attempt = 0;
  let lastError: any;

  while (attempt < MAX_RETRIES) {
    try {
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: [{ parts: [{ text: text }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: voice },
            },
          },
        },
      });

      const candidate = response.candidates?.[0];
      const base64Audio = candidate?.content?.parts?.[0]?.inlineData?.data;
      
      if (!base64Audio) {
        // Detailed error checking for debugging
        if (candidate?.finishReason) {
            console.warn("Gemini Finish Reason:", candidate.finishReason);
            if (candidate.finishReason === "SAFETY") {
                 throw new Error("Nội dung bị chặn bởi bộ lọc an toàn của Google (Safety Filter).");
            }
        }
        throw new Error("No audio data received from Gemini. Server response was empty.");
      }

      // Decode Base64 to ArrayBuffer
      const binaryString = atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      return bytes.buffer;

    } catch (error: any) {
      lastError = error;
      // Check if error is retryable (503 Service Unavailable or 429 Too Many Requests)
      const isRetryable = 
        error.status === 503 || 
        error.status === 429 || 
        (error.message && (error.message.includes("503") || error.message.includes("overloaded") || error.message.includes("429")));

      if (isRetryable && attempt < MAX_RETRIES - 1) {
        const delay = INITIAL_DELAY_MS * Math.pow(2, attempt); // 1s, 2s, 4s
        console.warn(`Gemini TTS API Error (Attempt ${attempt + 1}/${MAX_RETRIES}). Retrying in ${delay}ms...`, error);
        await wait(delay);
        attempt++;
        continue;
      } else {
        break;
      }
    }
  }

  console.error("Gemini TTS Final Error:", lastError);
  throw lastError;
};
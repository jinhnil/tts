export const isVietnameseVoice = (voice: SpeechSynthesisVoice): boolean => {
  if (!voice) return false;
  const lang = (voice.lang || "").toLowerCase();
  const name = (voice.name || "").toLowerCase();
  const uri = (voice.voiceURI || "").toLowerCase();
  return (
    lang.startsWith("vi") ||
    lang.includes("vi-") ||
    lang.includes("vi_") ||
    name.includes("vietnamese") ||
    name.includes("tiếng việt") ||
    name.includes("tieng viet") ||
    uri.includes("hoaimy") ||
    uri.includes("namminh") ||
    uri.includes("vi-vn")
  );
};

export const getCleanVoiceName = (voice: SpeechSynthesisVoice): string => {
  if (!voice) return "";
  let name = voice.name || "";
  const lang = voice.lang || "";
  const uri = voice.voiceURI || "";

  // If name contains 'undefined', try to extract real speaker name from voiceURI or lang
  if (name.includes("undefined") || !name) {
    let extractedName = "";

    if (/HoaiMy/i.test(uri) || /HoaiMy/i.test(name)) {
      extractedName = "Hoài My";
    } else if (/NamMinh/i.test(uri) || /NamMinh/i.test(name)) {
      extractedName = "Nam Minh";
    } else {
      // Try to extract speaker name from voiceURI (e.g., "Microsoft Ava Online...", "vi-VN-HoaiMyNeural")
      const uriMatch = uri.match(/([A-Z][a-z0-9]+)(?:Neural|Online|Voice)?/i);
      if (uriMatch && uriMatch[1] && !["Microsoft", "Speech", "Server", "Text"].includes(uriMatch[1])) {
        extractedName = uriMatch[1];
      }
    }

    if (name.includes("undefined")) {
      name = name.replace(/Microsoft\s+undefined/i, extractedName ? `Microsoft ${extractedName}` : "Microsoft");
      name = name.replace(/-\s*undefined$/i, lang ? `(${lang})` : "");
      name = name.replace(/undefined/g, extractedName || lang || "Voice");
    } else {
      name = extractedName ? `${extractedName} (${lang})` : (uri || lang || "Voice");
    }
  }

  // Add friendly indicators for popular Vietnamese voices
  if (/HoaiMy/i.test(uri) || /HoaiMy/i.test(name)) {
    if (!name.includes("Nữ")) name += " (Nữ)";
  } else if (/NamMinh/i.test(uri) || /NamMinh/i.test(name)) {
    if (!name.includes("Nam")) name += " (Nam)";
  }

  return name;
};

export const getVoiceId = (voice: SpeechSynthesisVoice, index: number): string => {
  if (!voice) return `voice_${index}`;
  const base = voice.voiceURI || voice.name || "voice";
  return `${base}__idx_${index}`;
};

export const findVoiceById = (voices: SpeechSynthesisVoice[], id: string): SpeechSynthesisVoice | undefined => {
  if (!id || voices.length === 0) return undefined;

  // 1. Check for index suffix __idx_N
  const match = id.match(/__idx_(\d+)$/);
  if (match) {
    const idx = parseInt(match[1], 10);
    if (!isNaN(idx) && voices[idx]) {
      return voices[idx];
    }
  }

  // 2. Exact match on voiceURI
  const byURI = voices.find((v) => v.voiceURI === id);
  if (byURI) return byURI;

  // 3. Exact match on name
  const byName = voices.find((v) => v.name === id);
  if (byName) return byName;

  return undefined;
};

export const getWebSpeechVoices = (): SpeechSynthesisVoice[] => {
  if (typeof window === "undefined" || !window.speechSynthesis) return [];
  return window.speechSynthesis.getVoices();
};

/**
 * Splits a long text string into smaller sub-chunks (max ~250 chars)
 * at sentence boundaries to prevent Chrome/Edge Web Speech API freeze.
 */
const splitIntoSubTexts = (text: string, maxLen = 250): string[] => {
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

export const GOOGLE_TTS_VOICE_ID = "google_tts_vi_cloud";

let activeAudio: HTMLAudioElement | null = null;

export const speakWebSpeech = (
  text: string,
  voiceURI: string,
  rate: number,
  volume: number, // 0-100
  onEnd: () => void,
  onError: (e: any) => void,
  shouldCancel: boolean = true,
  onProgress?: (percentage: number) => void,
  pitch: number = 1.0,
): SpeechSynthesisUtterance => {
  // Cancel any ongoing speech/audio only if requested
  if (shouldCancel) {
    stopWebSpeech();
  }

  // Handle Google Cloud TTS Online Fallback
  if (voiceURI === GOOGLE_TTS_VOICE_ID) {
    const subTexts = splitIntoSubTexts(text, 120);
    const totalLength = text.length || 1;
    const charOffsets: number[] = [0];
    for (let i = 0; i < subTexts.length - 1; i++) {
      charOffsets.push(charOffsets[i] + subTexts[i].length);
    }

    let subIndex = 0;

    const playNextSub = () => {
      if (subIndex >= subTexts.length) {
        onEnd();
        return;
      }

      const subText = subTexts[subIndex];
      const encoded = encodeURIComponent(subText);
      const url = `https://translate.google.com/translate_tts?ie=UTF-8&q=${encoded}&tl=vi&client=tw-ob`;

      const audio = new Audio(url);
      activeAudio = audio;
      audio.playbackRate = Math.max(0.5, Math.min(2.0, rate));
      audio.volume = Math.max(0, Math.min(1, volume / 100));

      audio.onended = () => {
        subIndex++;
        if (onProgress) {
          const totalRead = charOffsets[Math.min(subIndex, subTexts.length - 1)] || totalLength;
          onProgress(Math.min(100, Math.floor((totalRead / totalLength) * 100)));
        }
        playNextSub();
      };

      audio.onerror = (e) => {
        console.error("Google Cloud TTS Audio Error:", e);
        onError(e);
      };

      audio.play().catch((err) => {
        console.error("Google Cloud TTS Play Error:", err);
        onError(err);
      });
    };

    playNextSub();
    return new SpeechSynthesisUtterance();
  }

  const voices = getWebSpeechVoices();
  const selectedVoice =
    findVoiceById(voices, voiceURI) ||
    voices.find((v) => isVietnameseVoice(v)) ||
    voices[0];

  const subTexts = splitIntoSubTexts(text, 250);
  const totalLength = text.length || 1;

  // Calculate cumulative character offsets for accurate progress tracking
  const charOffsets: number[] = [0];
  for (let i = 0; i < subTexts.length - 1; i++) {
    charOffsets.push(charOffsets[i] + subTexts[i].length);
  }

  let currentSubIndex = 0;
  let activeUtterance: SpeechSynthesisUtterance | null = null;
  let isAborted = false;

  const speakSub = (index: number): SpeechSynthesisUtterance => {
    if (isAborted) return new SpeechSynthesisUtterance();

    const subText = subTexts[index];
    const utterance = new SpeechSynthesisUtterance(subText);
    activeUtterance = utterance;

    if (selectedVoice) {
      utterance.voice = selectedVoice;
      if (
        selectedVoice.lang &&
        selectedVoice.lang !== "undefined" &&
        selectedVoice.lang.trim() !== ""
      ) {
        utterance.lang = selectedVoice.lang;
      }
    } else {
      utterance.lang = "vi-VN";
    }

    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = Math.max(0, Math.min(1, volume / 100));

    utterance.onend = () => {
      if (isAborted) return;
      currentSubIndex++;
      if (currentSubIndex < subTexts.length) {
        speakSub(currentSubIndex);
      } else {
        onEnd();
      }
    };

    utterance.onerror = (e) => {
      if (e.error === "canceled" || e.error === "interrupted") {
        isAborted = true;
        return;
      }
      console.error("Web Speech API Sub-Utterance Error:", e);
      onError(e);
    };

    if (onProgress) {
      utterance.onboundary = (event) => {
        if (isAborted) return;
        const totalRead = charOffsets[index] + event.charIndex;
        const percentage = Math.floor((totalRead / totalLength) * 100);
        onProgress(Math.min(100, Math.max(0, percentage)));
      };
    }

    window.speechSynthesis.speak(utterance);
    return utterance;
  };

  return speakSub(0);
};

export const stopWebSpeech = () => {
  if (activeAudio) {
    activeAudio.pause();
    activeAudio.currentTime = 0;
    activeAudio = null;
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
};

export const pauseWebSpeech = () => {
  if (activeAudio && !activeAudio.paused) {
    activeAudio.pause();
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.pause();
  }
};

export const resumeWebSpeech = () => {
  if (activeAudio && activeAudio.paused) {
    activeAudio.play().catch(() => {});
  }
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.resume();
  }
};


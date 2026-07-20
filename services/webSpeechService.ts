export const isVietnameseVoice = (voice: SpeechSynthesisVoice): boolean => {
  if (!voice) return false;
  const lang = (voice.lang || "").toLowerCase();
  const name = (voice.name || "").toLowerCase();
  return (
    lang.startsWith("vi") ||
    lang.includes("vi-") ||
    lang.includes("vi_") ||
    name.includes("vietnamese") ||
    name.includes("tiếng việt") ||
    name.includes("tieng viet")
  );
};

export const getWebSpeechVoices = (): SpeechSynthesisVoice[] => {
  if (typeof window === "undefined" || !window.speechSynthesis) return [];
  return window.speechSynthesis.getVoices();
};

/**
 * Splits a long text string into smaller sub-chunks (max ~250 chars)
 * at sentence boundaries to prevent Chrome Web Speech API freeze/crash.
 */
const splitIntoSubTexts = (text: string, maxLen = 250): string[] => {
  if (text.length <= maxLen) return [text];

  const sentences = text.match(/[^.!?\n]+[.!?\n]+/g) || [text];
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
  // Cancel any ongoing speech only if requested
  if (shouldCancel) {
    window.speechSynthesis.cancel();
  }

  const voices = getWebSpeechVoices();
  const selectedVoice =
    voices.find((v) => v.voiceURI === voiceURI) ||
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
      utterance.lang = selectedVoice.lang || "vi-VN";
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
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
};

export const pauseWebSpeech = () => {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.pause();
  }
};

export const resumeWebSpeech = () => {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.resume();
  }
};


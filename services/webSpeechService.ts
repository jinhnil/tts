export const getWebSpeechVoices = (): SpeechSynthesisVoice[] => {
  return window.speechSynthesis.getVoices();
};

export const speakWebSpeech = (
  text: string,
  voiceURI: string,
  rate: number,
  volume: number, // 0-100
  onEnd: () => void,
  onError: (e: any) => void,
  shouldCancel: boolean = true,
): SpeechSynthesisUtterance => {
  // Cancel any ongoing speech only if requested
  if (shouldCancel) {
    window.speechSynthesis.cancel();
  }

  // Helper to get voice
  const getVoice = () => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((v) => v.voiceURI === voiceURI) ||
      voices.find((v) => v.lang.startsWith("vi")) ||
      voices[0]
    );
  };

  // If text is short enough, speak directly
  if (text.length < 1000) {
    const utterance = new SpeechSynthesisUtterance(text);
    const voice = getVoice();
    if (voice) utterance.voice = voice;
    utterance.rate = rate;
    utterance.volume = volume / 100;
    utterance.onend = onEnd;
    utterance.onerror = (e) => {
      if (e.error === "canceled" || e.error === "interrupted") return;
      console.error("Web Speech API Error:", e);
      onError(e);
    };
    window.speechSynthesis.speak(utterance);
    return utterance;
  }

  // If text is long, split it into smaller chunks
  // 200 chars is a safe limit for most mobile TTS engines (Android/iOS) to avoid synthesis-failed
  const MAX_CHUNK_LENGTH = 200;

  const chunks: string[] = [];
  let remainingText = text;

  while (remainingText.length > 0) {
    if (remainingText.length <= MAX_CHUNK_LENGTH) {
      chunks.push(remainingText);
      break;
    }

    // Find the nearest punctuation to split safely
    let splitIndex = -1;
    const punctuationRegex = /[.!?,;:]/g;
    let match;

    // Look for punctuation within the safe range
    while ((match = punctuationRegex.exec(remainingText)) !== null) {
      if (match.index < MAX_CHUNK_LENGTH) {
        splitIndex = match.index + 1; // Include the punctuation
      } else {
        break;
      }
    }

    // If no punctuation found, split at near the max length (space)
    if (splitIndex === -1) {
      const spaceIndex = remainingText.lastIndexOf(" ", MAX_CHUNK_LENGTH);
      splitIndex = spaceIndex > 0 ? spaceIndex + 1 : MAX_CHUNK_LENGTH;
    }

    chunks.push(remainingText.slice(0, splitIndex));
    remainingText = remainingText.slice(splitIndex).trim();
  }

  // Chain speech execution
  let currentUtterance: SpeechSynthesisUtterance;

  const speakNextChunk = (index: number) => {
    if (index >= chunks.length) {
      onEnd();
      return;
    }

    const chunkText = chunks[index];
    const utterance = new SpeechSynthesisUtterance(chunkText);
    const voice = getVoice();
    if (voice) utterance.voice = voice;
    utterance.rate = rate;
    utterance.volume = volume / 100;

    utterance.onend = () => speakNextChunk(index + 1);
    utterance.onerror = (e) => {
      if (e.error === "canceled" || e.error === "interrupted") return;
      // On 'synthesis-failed', sometimes retrying or just skipping works,
      // but for now we report it.
      console.error("Web Speech API Error (Chunk " + index + "):", e);
      onError(e);
    };

    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  };

  speakNextChunk(0);

  return new SpeechSynthesisUtterance(chunks[0]);
};

export const stopWebSpeech = () => {
  window.speechSynthesis.cancel();
};

export const pauseWebSpeech = () => {
  window.speechSynthesis.pause();
};

export const resumeWebSpeech = () => {
  window.speechSynthesis.resume();
};

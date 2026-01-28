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

  // If text is long, split it
  const chunkLength = 1000;
  const chunks = text.match(
    new RegExp(`.{1,${chunkLength}}(?:\\s|$)|.{1,${chunkLength}}`, "g"),
  ) || [text];

  // Create a representative utterance (returning the first one allows some control, though imperfect for multi-part)
  // We need to chain them.
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
      console.error("Web Speech API Error (Chunk " + index + "):", e);
      onError(e);
    };

    currentUtterance = utterance; // Update reference if needed externally?
    // Note: external control ref will point to the *first* one returned below.
    // This is a limitation but solves the crash.
    window.speechSynthesis.speak(utterance);
  };

  // Start the chain
  speakNextChunk(0);

  // Return a dummy or the first utterance.
  // Returning a new dummy to satisfy type, but real control is tricky with chaining.
  // Ideally we return the first utterance, but `stopWebSpeech` calls `cancel()` which clears the whole queue anywhere,
  // so external stop() works fine.
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

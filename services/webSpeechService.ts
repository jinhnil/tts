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

  const utterance = new SpeechSynthesisUtterance(text);

  const voices = window.speechSynthesis.getVoices();
  const selectedVoice =
    voices.find((v) => v.voiceURI === voiceURI) ||
    voices.find((v) => v.lang.startsWith("vi")) ||
    voices[0];

  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }

  // Web Speech API rate: 0.1 to 10. Default 1.
  utterance.rate = rate;
  // Web Speech API volume: 0 to 1.
  utterance.volume = volume / 100;

  utterance.onend = () => {
    onEnd();
  };

  utterance.onerror = (e) => {
    // Ignore errors caused by manual cancellation (e.g. clicking Next/Prev/Stop)
    if (e.error === "canceled" || e.error === "interrupted") {
      return;
    }
    console.error("Web Speech API Error:", e);
    onError(e);
  };

  window.speechSynthesis.speak(utterance);
  return utterance;
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

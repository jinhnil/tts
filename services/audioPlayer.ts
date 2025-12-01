/**
 * Manages audio context and playback logic using Web Audio API.
 * This allows for speed (playbackRate) and volume (gain) control
 * without re-generating audio from the server.
 */

export class AudioPlayer {
  private audioContext: AudioContext | null = null;
  private sourceNode: AudioBufferSourceNode | null = null;
  private gainNode: GainNode | null = null;
  private startTime: number = 0;
  private pausedAt: number = 0;
  private isPlaying: boolean = false;
  private currentBuffer: AudioBuffer | null = null;

  constructor() {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (AudioContextClass) {
      this.audioContext = new AudioContext();
    }
  }

  public async decodeAudioData(arrayBuffer: ArrayBuffer): Promise<AudioBuffer> {
    if (!this.audioContext) throw new Error("AudioContext not supported");

    // Gemini 2.5 Flash TTS returns raw PCM 16-bit audio (Little Endian), usually 24kHz.
    // Native decodeAudioData expects a file header (WAV/MP3).
    // We must manually convert PCM to AudioBuffer.
    
    const sampleRate = 24000; // Standard for Gemini 2.5 Flash TTS
    const numChannels = 1; // Mono
    
    // Ensure byte length is even for Int16Array
    const byteLength = arrayBuffer.byteLength;
    const alignedBuffer = byteLength % 2 === 0 
        ? arrayBuffer 
        : arrayBuffer.slice(0, byteLength - 1);

    // Create view for 16-bit integers
    const dataInt16 = new Int16Array(alignedBuffer);
    const frameCount = dataInt16.length;
    
    const buffer = this.audioContext.createBuffer(numChannels, frameCount, sampleRate);
    const channelData = buffer.getChannelData(0);
    
    // Convert Int16 (-32768 to 32767) to Float32 (-1.0 to 1.0)
    for (let i = 0; i < frameCount; i++) {
        channelData[i] = dataInt16[i] / 32768.0;
    }
    
    return buffer;
  }

  public playBuffer(buffer: AudioBuffer, rate: number = 1.0, volume: number = 1.0, offset: number = 0) {
    if (!this.audioContext) return;
    
    this.stop(); // Stop previous if any
    
    this.currentBuffer = buffer;
    this.sourceNode = this.audioContext.createBufferSource();
    this.sourceNode.buffer = buffer;
    
    // Speed control
    this.sourceNode.playbackRate.value = rate;

    // Volume control
    this.gainNode = this.audioContext.createGain();
    this.gainNode.gain.value = volume;

    // Connect graph: Source -> Gain -> Destination
    this.sourceNode.connect(this.gainNode);
    this.gainNode.connect(this.audioContext.destination);

    this.startTime = this.audioContext.currentTime - offset;
    this.pausedAt = offset;
    this.isPlaying = true;

    // Handle end of playback
    this.sourceNode.onended = () => {
        this.isPlaying = false;
        // Trigger generic ended event if needed, but usually handled by React component polling/callback
    };

    // offset must be / rate if we were strictly calculating time, but 
    // start(when, offset) -> offset is in buffer's timeframe (seconds).
    this.sourceNode.start(0, offset); 
  }

  public stop() {
    if (this.sourceNode) {
      try {
        this.sourceNode.stop();
        this.sourceNode.disconnect();
      } catch (e) {
        // Ignore if already stopped
      }
      this.sourceNode = null;
    }
    this.isPlaying = false;
    this.pausedAt = 0;
  }

  public setSpeed(rate: number) {
    if (this.sourceNode && this.sourceNode.playbackRate) {
      this.sourceNode.playbackRate.value = rate;
    }
  }

  public setVolume(volume: number) {
    if (this.gainNode && this.gainNode.gain) {
        // Logarithmic volume feels more natural, but linear is fine for basic
        // Map 0-100 to 0-1
      this.gainNode.gain.value = Math.max(0, Math.min(1, volume / 100));
    }
  }

  public resume() {
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
  }

  public getContext() {
    return this.audioContext;
  }

  public setOnEnded(callback: () => void) {
      // Wrapper to attach to current source if it exists
      if (this.sourceNode) {
          const oldOnEnded = this.sourceNode.onended;
          this.sourceNode.onended = (ev) => {
              if (oldOnEnded) oldOnEnded.call(this.sourceNode!, ev);
              callback();
          }
      }
  }
}
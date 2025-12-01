export interface TextFile {
  name: string;
  path: string; // Relative path or ID
  content: string;
  lastModified: number;
  fileHandle?: File; // Store the native file object for lazy loading
}

export interface Chunk {
  id: number;
  text: string;
}

export enum ReaderState {
  IDLE = 'IDLE',
  LOADING = 'LOADING',
  PLAYING = 'PLAYING',
  PAUSED = 'PAUSED',
}

export type GeminiVoice = 'Puck' | 'Charon' | 'Kore' | 'Fenrir' | 'Zephyr';

export interface ReaderSettings {
  playbackRate: number; // 0.5 to 3.0 (Web Speech limits recommended)
  volume: number; // 0 to 100
  webSpeechVoiceURI: string; // ID for Web Speech voice
  sentencesPerChunk: number;
}

export interface StoredProgress {
  fileName: string;
  chunkIndex: number;
  settings: ReaderSettings;
}
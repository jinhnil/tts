import { Chunk } from '../types';

/**
 * Splits text into chunks based on sentence delimiters.
 * A "chunk" is composed of approximately `sentencesPerChunk` sentences.
 */
export const splitTextIntoChunks = (text: string, sentencesPerChunk: number = 5): Chunk[] => {
  if (!text) return [];

  // Match sentences ending in punctuation (. ! ?) followed by whitespace or end of string.
  // This is a basic heuristic.
  const sentenceRegex = /[^.!?\n]+[.!?\n]+(\s|$)/g;
  
  const matches = text.match(sentenceRegex);
  
  if (!matches) {
    // Fallback if regex fails to find sentences (e.g. no punctuation)
    return [{ id: 0, text: text }];
  }

  const chunks: Chunk[] = [];
  let currentChunkText = '';
  let sentenceCount = 0;
  let chunkId = 0;

  for (const sentence of matches) {
    currentChunkText += sentence;
    sentenceCount++;

    if (sentenceCount >= sentencesPerChunk) {
      chunks.push({
        id: chunkId++,
        text: currentChunkText.trim(),
      });
      currentChunkText = '';
      sentenceCount = 0;
    }
  }

  // Add any remaining text
  if (currentChunkText.trim().length > 0) {
    chunks.push({
      id: chunkId++,
      text: currentChunkText.trim(),
    });
  }

  return chunks;
};
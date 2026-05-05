import { Chunk } from '../types';

/**
 * Splits text into chunks based on specific user rules:
 * 1. Delimiters: . ! ? \n
 * 2. Minimum length: 3 characters (trimmed)
 * 3. Consecutive dots (..) are treated as content, not delimiters.
 */
export const splitTextIntoChunks = (text: string, sentencesPerChunk: number = 5): Chunk[] => {
  if (!text) return [];

  const sentences: string[] = [];
  let buffer = '';

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    buffer += char;

    let isDelimiter = false;

    // Check for delimiters: dot, exclamation, question mark, or newline
    if (char === '!' || char === '?' || char === '\n') {
      isDelimiter = true;
    } else if (char === '.') {
       // Logic for dots: only a single dot is a delimiter. 
       // Consecutive dots (.. or ...) are treated as content.
       const nextChar = i < text.length - 1 ? text[i + 1] : null;
       const prevChar = i > 0 ? text[i - 1] : null;
       
       // If next is dot or prev is dot, it's a sequence -> ignore as delimiter
       if (nextChar !== '.' && prevChar !== '.') {
         isDelimiter = true;
       }
    }

    if (isDelimiter) {
      // Rule: End of sentence by delimiter, min 3 chars
      // We check text content length (ignoring extra whitespace)
      // Example: "Ok." (3 chars) -> Valid. "1." (2 chars) -> Invalid, continue accumulating.
      if (buffer.trim().length >= 3) {
        sentences.push(buffer.trim());
        buffer = '';
      }
    }
  }

  // Handle any remaining text in the buffer
  if (buffer.trim().length > 0) {
    // If the leftover is too short, append to the previous sentence if possible
    if (buffer.trim().length < 3 && sentences.length > 0) {
      sentences[sentences.length - 1] += ' ' + buffer.trim();
    } else {
      sentences.push(buffer.trim());
    }
  }

  // Fallback: If no sentences formed but text exists
  if (sentences.length === 0 && text.trim().length > 0) {
      sentences.push(text.trim());
  }

  // Group sentences into chunks
  const chunks: Chunk[] = [];
  let currentChunkText = '';
  let sentenceCount = 0;
  let chunkId = 0;

  for (const sentence of sentences) {
    // Add space between sentences
    currentChunkText += (currentChunkText.length > 0 ? ' ' : '') + sentence;
    sentenceCount++;

    if (sentenceCount >= sentencesPerChunk) {
      chunks.push({
        id: chunkId++,
        text: currentChunkText,
      });
      currentChunkText = '';
      sentenceCount = 0;
    }
  }

  // Add any remaining text as the last chunk
  if (currentChunkText.length > 0) {
    chunks.push({
      id: chunkId++,
      text: currentChunkText,
    });
  }

  return chunks;
};
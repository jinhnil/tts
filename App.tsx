import React, { useState, useEffect, useCallback } from "react";
import { FileList } from "./components/FileList";
import { Reader } from "./components/Reader";
import { TextFile, ReaderSettings, StoredProgress } from "./types";
import { Loader2 } from "lucide-react";

// Keys for LocalStorage
const PROGRESS_KEY = "tts_reader_progress"; // Renamed key to reflect non-gemini status

const DEFAULT_SETTINGS: ReaderSettings = {
  playbackRate: 1.0,
  volume: 100,
  webSpeechVoiceURI: "",
  sentencesPerChunk: 50,
  viewMode: "continuous",
};

const App: React.FC = () => {
  const [files, setFiles] = useState<TextFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<TextFile | null>(null);
  const [isFileLoading, setIsFileLoading] = useState(false);
  const [storedProgress, setStoredProgress] = useState<
    Record<string, StoredProgress>
  >({});
  const [lastPlayedFile, setLastPlayedFile] = useState<string | undefined>(
    undefined,
  );

  // Load progress from LocalStorage
  useEffect(() => {
    try {
      const savedProgress = localStorage.getItem(PROGRESS_KEY);
      if (savedProgress) {
        setStoredProgress(JSON.parse(savedProgress));
      }
    } catch (e) {
      console.error("Failed to load local storage data", e);
    }
  }, []);

  const saveProgress = useCallback(
    (fileName: string, chunkIndex: number, settings: ReaderSettings) => {
      setStoredProgress((prev) => {
        const newProgress = {
          ...prev,
          [fileName]: {
            fileName,
            chunkIndex,
            settings,
          },
        };
        localStorage.setItem(PROGRESS_KEY, JSON.stringify(newProgress));
        return newProgress;
      });
      setLastPlayedFile(fileName);
    },
    [],
  );

  const handleFileSelect = async (file: TextFile) => {
    if (!file.content && file.fileHandle) {
      setIsFileLoading(true);
      try {
        const text = await file.fileHandle.text();
        const updatedFile = { ...file, content: text };
        setFiles((prev) =>
          prev.map((f) => (f.path === file.path ? updatedFile : f)),
        );
        setSelectedFile(updatedFile);
      } catch (e) {
        console.error("Error reading file", e);
        alert("Không thể đọc file này.");
      } finally {
        setIsFileLoading(false);
      }
    } else {
      setSelectedFile(file);
    }
  };

  const handleBack = () => {
    setSelectedFile(null);
  };

  return (
    <div className="h-screen w-screen bg-gray-950 overflow-hidden text-white font-sans relative">
      {isFileLoading && (
        <div className="absolute inset-0 bg-black/50 z-[2000] flex items-center justify-center backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="animate-spin text-blue-500" size={48} />
            <span className="text-gray-200 font-medium">Đang đọc file...</span>
          </div>
        </div>
      )}

      {!selectedFile ? (
        <FileList
          files={files}
          setFiles={setFiles}
          onFileSelect={handleFileSelect}
          lastPlayedFileName={lastPlayedFile}
        />
      ) : (
        <Reader
          file={selectedFile}
          initialSettings={
            storedProgress[selectedFile.name]?.settings || DEFAULT_SETTINGS
          }
          initialChunkIndex={storedProgress[selectedFile.name]?.chunkIndex || 0}
          onBack={handleBack}
          onSaveProgress={(chunkIndex, settings) =>
            saveProgress(selectedFile.name, chunkIndex, settings)
          }
        />
      )}
    </div>
  );
};

export default App;

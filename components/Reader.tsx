import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useLayoutEffect,
} from "react";
import { TextFile, Chunk, ReaderSettings, ReaderState } from "../types";
import { splitTextIntoChunks } from "../utils/textUtils";
import {
  speakWebSpeech,
  stopWebSpeech,
  pauseWebSpeech,
  resumeWebSpeech,
  getWebSpeechVoices,
} from "../services/webSpeechService";
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  SkipBack,
  SkipForward,
  Settings,
  Volume2,
  Gauge,
  CornerDownRight,
  AlertCircle,
  RotateCw,
  Plus,
  Minus,
  FileText,
  List,
  ArrowRight,
  Save,
  X,
} from "lucide-react";

interface ReaderProps {
  file: TextFile;
  initialSettings: ReaderSettings;
  initialChunkIndex: number;
  onBack: () => void;
  onSaveProgress: (chunkIndex: number, settings: ReaderSettings) => void;
}

export const Reader: React.FC<ReaderProps> = ({
  file,
  initialSettings,
  initialChunkIndex,
  onBack,
  onSaveProgress,
}) => {
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(initialChunkIndex);
  const [readerState, setReaderState] = useState<ReaderState>(ReaderState.IDLE);
  const [settings, setSettings] = useState<ReaderSettings>(initialSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [jumpTarget, setJumpTarget] = useState<string>("");
  const [chunkProgress, setChunkProgress] = useState<number>(0);

  // Web Speech Voices
  const [webSpeechVoices, setWebSpeechVoices] = useState<
    SpeechSynthesisVoice[]
  >([]);

  // Infinite Scroll Visibility
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 0 });

  // Refs
  const activeChunkRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const onSaveProgressRef = useRef(onSaveProgress);
  const previousScrollHeight = useRef<number>(0);
  const isPrepending = useRef<boolean>(false);
  const isSettingUpdate = useRef<boolean>(false);
  const shouldAutoScrollRef = useRef<boolean>(false);

  // Refs for Web Speech
  const webSpeechUtterance = useRef<SpeechSynthesisUtterance | null>(null);

  // Temp settings for the form
  const [tempSettings, setTempSettings] =
    useState<ReaderSettings>(initialSettings);

  const handleOpenSettings = () => {
    setTempSettings(settings);
    setShowSettings(true);
  };

  const handleSaveSettings = () => {
    // If chunk size changed, we need to recalculate current index
    if (tempSettings.sentencesPerChunk !== settings.sentencesPerChunk) {
      const oldSize = settings.sentencesPerChunk;
      const newSize = tempSettings.sentencesPerChunk;
      const currentSentenceIndex = currentChunkIndex * oldSize;
      const newIndex = Math.floor(currentSentenceIndex / newSize);
      setCurrentChunkIndex(newIndex);
    }

    setSettings(tempSettings);
    setShowSettings(false);
  };

  // Pagination State
  const ITEMS_PER_PAGE = 50;
  const [currentPage, setCurrentPage] = useState(
    Math.floor(initialChunkIndex / ITEMS_PER_PAGE),
  );

  const totalPages = Math.ceil(chunks.length / ITEMS_PER_PAGE);

  useEffect(() => {
    setCurrentPage(Math.floor(currentChunkIndex / ITEMS_PER_PAGE));
  }, [currentChunkIndex, ITEMS_PER_PAGE]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 0 && newPage < totalPages) {
      setCurrentPage(newPage);
    }
  };

  useEffect(() => {
    onSaveProgressRef.current = onSaveProgress;
  }, [onSaveProgress]);

  // Load Web Speech Voices
  const loadVoices = useCallback(() => {
    const allVoices = getWebSpeechVoices();

    // Sort: Prioritize Vietnamese voices ('vi', 'vi-VN') to the top
    allVoices.sort((a, b) => {
      const aIsVi = a.lang.toLowerCase().includes("vi");
      const bIsVi = b.lang.toLowerCase().includes("vi");

      if (aIsVi && !bIsVi) return -1;
      if (!aIsVi && bIsVi) return 1;
      return a.name.localeCompare(b.name);
    });

    setWebSpeechVoices(allVoices);

    // Auto-select logic
    setSettings((prev) => {
      const voiceExists = allVoices.some(
        (v) => v.voiceURI === prev.webSpeechVoiceURI,
      );

      if (!prev.webSpeechVoiceURI || !voiceExists) {
        const viVoice = allVoices.find((v) =>
          v.lang.toLowerCase().includes("vi"),
        );
        if (viVoice) {
          return { ...prev, webSpeechVoiceURI: viVoice.voiceURI };
        } else if (allVoices.length > 0) {
          return { ...prev, webSpeechVoiceURI: allVoices[0].voiceURI };
        }
      }
      return prev;
    });
  }, []);

  useEffect(() => {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [loadVoices]);

  // Initialize chunks
  useEffect(() => {
    const generatedChunks = splitTextIntoChunks(
      file.content,
      settings.sentencesPerChunk,
    );
    setChunks(generatedChunks);
    if (currentChunkIndex >= generatedChunks.length) {
      setCurrentChunkIndex(Math.max(0, generatedChunks.length - 1));
    }
  }, [file.content, settings.sentencesPerChunk]);

  // Viewport logic
  useEffect(() => {
    const start = Math.max(0, currentChunkIndex - 5);
    const end = Math.min(chunks.length, currentChunkIndex + 6);
    setVisibleRange({ start, end });
  }, [currentChunkIndex, chunks.length]);

  // Scroll active into view
  useEffect(() => {
    shouldAutoScrollRef.current = true;
    if (activeChunkRef.current) {
      activeChunkRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      shouldAutoScrollRef.current = false;
    }
  }, [currentChunkIndex]);

  useEffect(() => {
    if (shouldAutoScrollRef.current && activeChunkRef.current) {
      activeChunkRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      shouldAutoScrollRef.current = false;
    }
  }, [visibleRange]);

  // Scroll restoration
  useLayoutEffect(() => {
    if (isPrepending.current && containerRef.current) {
      const diff =
        containerRef.current.scrollHeight - previousScrollHeight.current;
      if (diff > 0) containerRef.current.scrollTop += diff;
      isPrepending.current = false;
    }
  }, [visibleRange.start]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollTop < 100 && visibleRange.start > 0) {
      previousScrollHeight.current = scrollHeight;
      isPrepending.current = true;
      setVisibleRange((prev) => ({
        ...prev,
        start: Math.max(0, prev.start - 5),
      }));
    }
    if (
      scrollHeight - scrollTop - clientHeight < 100 &&
      visibleRange.end < chunks.length
    ) {
      setVisibleRange((prev) => ({
        ...prev,
        end: Math.min(chunks.length, prev.end + 5),
      }));
    }
  };

  const progressInterval = useRef<NodeJS.Timeout | null>(null);

  const clearProgressInterval = () => {
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
      progressInterval.current = null;
    }
  };

  const playChunk = useCallback(
    async (index: number, autoPlay: boolean = false) => {
      if (index < 0 || index >= chunks.length) return;

      if (!autoPlay) {
        stopWebSpeech();
      }
      clearProgressInterval(); // Clear any existing interval

      setErrorMsg(null);
      setReaderState(ReaderState.PLAYING);
      setChunkProgress(0);

      // Estimate duration for fallback simulation
      // Avg 70ms per char at 1.0x speed
      const textLength = chunks[index].text.length;
      const estimatedDurationMs = (textLength * 70) / settings.playbackRate;
      const updateInterval = 100;
      const step = (updateInterval / estimatedDurationMs) * 100;

      // Start simulation
      progressInterval.current = setInterval(() => {
        setChunkProgress((prev) => {
          if (prev >= 95) return prev; // Don't complete purely on simulation
          return Math.min(95, prev + step);
        });
      }, updateInterval);

      webSpeechUtterance.current = speakWebSpeech(
        chunks[index].text,
        settings.webSpeechVoiceURI,
        settings.playbackRate,
        settings.volume,
        () => {
          // On End
          clearProgressInterval();
          setChunkProgress(100);
          if (index < chunks.length - 1) {
            setCurrentChunkIndex((prev) => {
              const next = prev + 1;
              playChunk(next, true);
              return next;
            });
          } else {
            setReaderState(ReaderState.IDLE);
          }
        },
        (err) => {
          // On Error
          clearProgressInterval();
          console.error("Reader Error:", err);
          const errorMsg = err.error || "Unknown Error";
          setErrorMsg(`Lỗi trình duyệt: ${errorMsg}`);
          setReaderState(ReaderState.IDLE);
        },
        !autoPlay, // shouldCancel
        (percentage) => {
          // Real progress update
          // Reset interval if we get real data? Or just overwrite?
          // Overwrite is fine.
          setChunkProgress(percentage);
        },
      );
    },
    [chunks, settings],
  );

  // Effect to apply settings immediately when changing volume/rate
  useEffect(() => {
    if (readerState === ReaderState.PLAYING) {
      isSettingUpdate.current = true;
      playChunk(currentChunkIndex);
    }
    // Save progress on setting change
    onSaveProgressRef.current(currentChunkIndex, settings);
  }, [settings.playbackRate, settings.volume, settings.webSpeechVoiceURI]);

  // Save progress on chunk change
  useEffect(() => {
    if (!isSettingUpdate.current) {
      onSaveProgressRef.current(currentChunkIndex, settings);
    }
    isSettingUpdate.current = false;
  }, [currentChunkIndex]);

  const handlePlayPause = () => {
    if (readerState === ReaderState.PLAYING) {
      pauseWebSpeech();
      setReaderState(ReaderState.PAUSED);
    } else if (readerState === ReaderState.PAUSED) {
      resumeWebSpeech();
      setReaderState(ReaderState.PLAYING);
    } else {
      playChunk(currentChunkIndex);
    }
  };

  const handleStop = () => {
    stopWebSpeech();
    clearProgressInterval();
    setReaderState(ReaderState.IDLE);
    setChunkProgress(0); // Reset UI
  };

  const handleNavigate = (offset: number) => {
    handleStop();
    const next = Math.max(
      0,
      Math.min(chunks.length - 1, currentChunkIndex + offset),
    );
    setCurrentChunkIndex(next);
    playChunk(next);
  };

  const handleJump = () => {
    const target = parseInt(jumpTarget);
    if (!isNaN(target) && target > 0 && target <= chunks.length) {
      handleStop();
      setCurrentChunkIndex(target - 1);
      playChunk(target - 1);
      setJumpTarget("");
    }
  };

  const changeChunkSize = (delta: number) => {
    const oldSize = settings.sentencesPerChunk;
    const newSize = Math.max(1, Math.min(200, oldSize + delta));
    if (newSize === oldSize) return;

    // Calculate approximate position to stay on the same sentence
    // Assuming linear distribution mostly accurate for preserving context
    const currentSentenceIndex = currentChunkIndex * oldSize;
    const newIndex = Math.floor(currentSentenceIndex / newSize);

    setSettings((prev) => ({ ...prev, sentencesPerChunk: newSize }));
    setCurrentChunkIndex(newIndex);

    // If playing, we might want to restart the chunk or at least ensure
    // the new chunk text is loaded. But simply updating index is the critical fix.
    // The useEffect will regenerate chunks.
  };

  const visibleChunks = chunks.slice(visibleRange.start, visibleRange.end);
  const hasVietnameseVoice = webSpeechVoices.some((v) =>
    v.lang.toLowerCase().includes("vi"),
  );

  return (
    <div className="flex flex-col h-[100dvh] bg-gray-950 text-gray-100 relative overflow-hidden pt-[env(safe-area-inset-top)]">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-gray-900 border-b border-gray-800 z-50 shrink-0 shadow-md">
        <button
          onClick={onBack}
          className="p-2 hover:bg-gray-800 rounded-full transition-colors flex items-center gap-2"
        >
          <ArrowLeft size={20} />
          <span className="hidden sm:inline text-sm">Quay lại</span>
        </button>
        <h2 className="text-lg font-semibold truncate max-w-[50%] text-gray-200">
          {file.name}
        </h2>
        <button
          onClick={handleOpenSettings}
          className={`p-2 rounded-full transition-colors ${showSettings ? "bg-blue-600 text-white" : "hover:bg-gray-800 text-gray-400"}`}
        >
          <Settings size={20} />
        </button>
      </header>

      {/* Settings Panel - Responsive: Bottom Sheet on Mobile, Dropdown on Desktop */}
      {showSettings && (
        <>
          {/* Backdrop for mobile */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[890] sm:hidden"
            onClick={() => setShowSettings(false)}
          />

          <div
            className={`
                fixed inset-x-0 bottom-0 z-[900] w-full bg-gray-900 border-t border-gray-700 p-5 shadow-2xl 
                animate-in slide-in-from-bottom duration-300 rounded-t-2xl max-h-[75dvh] overflow-y-auto
                sm:absolute sm:top-14 sm:right-4 sm:bottom-auto sm:left-auto sm:w-80 sm:bg-gray-800 sm:border sm:rounded-xl sm:max-h-[80vh] sm:animate-in sm:fade-in sm:zoom-in-95
            `}
          >
            {/* Mobile Drag Handle */}
            <div className="w-12 h-1.5 bg-gray-700 rounded-full mx-auto mb-6 sm:hidden" />
            <div className="mb-5">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  Chế độ hiển thị
                </label>
              </div>
              <div className="grid grid-cols-2 gap-2 bg-gray-700 p-1 rounded-lg">
                <button
                  onClick={() =>
                    setTempSettings((s) => ({ ...s, viewMode: "continuous" }))
                  }
                  className={`flex items-center justify-center gap-2 py-2 rounded-md text-sm transition-all ${
                    tempSettings.viewMode === "continuous"
                      ? "bg-gray-600 text-white shadow"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  <FileText size={16} />
                  <span>Cuộn</span>
                </button>

                <button
                  onClick={() =>
                    setTempSettings((s) => ({ ...s, viewMode: "paginated" }))
                  }
                  className={`flex items-center justify-center gap-2 py-2 rounded-md text-sm transition-all ${
                    tempSettings.viewMode === "paginated"
                      ? "bg-gray-600 text-white shadow"
                      : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  <List size={16} />
                  <span>Danh sách</span>
                </button>
              </div>
            </div>

            <div className="mb-5">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  Giọng đọc (Web Speech)
                </label>
                <button
                  onClick={loadVoices}
                  title="Tải lại giọng"
                  className="p-1 hover:bg-gray-700 rounded text-gray-400"
                >
                  <RotateCw size={14} />
                </button>
              </div>

              {!hasVietnameseVoice && webSpeechVoices.length > 0 && (
                <div className="mb-2 p-2 bg-yellow-900/30 border border-yellow-700 rounded text-xs text-yellow-200">
                  Không tìm thấy giọng Tiếng Việt. Vui lòng kiểm tra gói ngôn
                  ngữ trong cài đặt thiết bị.
                </div>
              )}

              <select
                value={tempSettings.webSpeechVoiceURI}
                onChange={(e) =>
                  setTempSettings((s) => ({
                    ...s,
                    webSpeechVoiceURI: e.target.value,
                  }))
                }
                className="w-full bg-gray-700 border border-gray-600 rounded p-2 text-xs text-white"
              >
                <optgroup label="Tiếng Việt">
                  {webSpeechVoices
                    .filter((v) => v.lang.toLowerCase().includes("vi"))
                    .map((v) => (
                      <option key={v.voiceURI} value={v.voiceURI}>
                        {v.name}
                      </option>
                    ))}
                </optgroup>
                <optgroup label="Ngôn ngữ khác">
                  {webSpeechVoices
                    .filter((v) => !v.lang.toLowerCase().includes("vi"))
                    .map((v) => (
                      <option key={v.voiceURI} value={v.voiceURI}>
                        {v.name} ({v.lang})
                      </option>
                    ))}
                </optgroup>
              </select>
            </div>

            <div className="mb-5">
              <div className="flex justify-between mb-1">
                <label className="text-xs font-bold text-gray-400 uppercase">
                  Tốc độ
                </label>
                <span className="text-xs text-blue-400">
                  {tempSettings.playbackRate.toFixed(1)}x
                </span>
              </div>
              <input
                type="range"
                min="0.5"
                max="3.0"
                step="0.1"
                value={tempSettings.playbackRate}
                onChange={(e) =>
                  setTempSettings((s) => ({
                    ...s,
                    playbackRate: parseFloat(e.target.value),
                  }))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div className="mb-5">
              <div className="flex justify-between mb-1">
                <label className="text-xs font-bold text-gray-400 uppercase">
                  Âm lượng
                </label>
                <span className="text-xs text-blue-400">
                  {tempSettings.volume}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={tempSettings.volume}
                onChange={(e) =>
                  setTempSettings((s) => ({
                    ...s,
                    volume: parseInt(e.target.value),
                  }))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
            </div>

            <div className="mb-4">
              <label className="text-xs font-bold text-gray-400 uppercase block mb-2">
                Số câu mỗi đoạn
              </label>
              <div className="flex items-center gap-3">
                <button
                  onClick={() =>
                    setTempSettings((s) => ({
                      ...s,
                      sentencesPerChunk: Math.max(
                        1,
                        Math.min(200, s.sentencesPerChunk - 1),
                      ),
                    }))
                  }
                  className="w-12 h-12 flex items-center justify-center bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors active:scale-95"
                >
                  <Minus size={24} />
                </button>
                <input
                  type="number"
                  min="1"
                  max="200"
                  value={tempSettings.sentencesPerChunk}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    if (!isNaN(val)) {
                      setTempSettings((s) => ({
                        ...s,
                        sentencesPerChunk: val,
                      }));
                    } else if (e.target.value === "") {
                      // Allow empty temporary state for typing
                      setTempSettings((s) => ({ ...s, sentencesPerChunk: 0 }));
                    }
                  }}
                  onBlur={(e) => {
                    let val = parseInt(e.target.value);
                    if (isNaN(val) || val < 1) val = 1;
                    if (val > 200) val = 200;
                    setTempSettings((s) => ({ ...s, sentencesPerChunk: val }));
                  }}
                  className="flex-1 text-center font-mono text-xl bg-gray-900 border border-gray-700 rounded-lg h-12 text-white outline-none focus:border-blue-500 transition-colors"
                />
                <button
                  onClick={() =>
                    setTempSettings((s) => ({
                      ...s,
                      sentencesPerChunk: Math.max(
                        1,
                        Math.min(200, s.sentencesPerChunk + 1),
                      ),
                    }))
                  }
                  className="w-12 h-12 flex items-center justify-center bg-gray-700 hover:bg-gray-600 rounded-lg text-white transition-colors active:scale-95"
                >
                  <Plus size={24} />
                </button>
              </div>
            </div>

            <button
              onClick={handleSaveSettings}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2 mb-2"
            >
              <Save size={20} />
              <span>Lưu cài đặt</span>
            </button>
            <button
              onClick={() => setShowSettings(false)}
              className="w-full bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-3 rounded-xl active:scale-95 transition-all"
            >
              Hủy
            </button>
          </div>
        </>
      )}

      {/* Main Content */}
      <main
        ref={containerRef}
        onScroll={settings.viewMode === "continuous" ? handleScroll : undefined}
        className="flex-1 overflow-y-auto p-4 md:p-8 space-y-4 scroll-smooth relative pb-60"
      >
        {settings.viewMode === "paginated" && chunks.length > 0 && (
          <div className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur pb-3 pt-1 border-b border-gray-800 mb-4 flex justify-between items-center text-sm font-mono shadow-sm">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 0}
              className="p-2 hover:bg-gray-800 rounded-lg disabled:opacity-30 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft size={18} />
            </button>
            <span className="text-gray-300 font-bold">
              Trang {currentPage + 1} / {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage >= totalPages - 1}
              className="p-2 hover:bg-gray-800 rounded-lg disabled:opacity-30 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowRight size={18} />
            </button>
          </div>
        )}

        {chunks.length > 0 ? (
          <>
            {/* ... Continuous loading indicator ... */}

            {settings.viewMode === "paginated" ? (
              <div className="flex flex-col gap-2">
                {chunks
                  .slice(
                    currentPage * ITEMS_PER_PAGE,
                    (currentPage + 1) * ITEMS_PER_PAGE,
                  )
                  .map((chunk) => {
                    const isActive = chunk.id === currentChunkIndex;
                    return (
                      <div
                        key={chunk.id}
                        ref={isActive ? activeChunkRef : null}
                        onClick={() => {
                          handleStop();
                          setCurrentChunkIndex(chunk.id);
                          playChunk(chunk.id);
                        }}
                        className={`
                                    p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between
                                    ${
                                      isActive
                                        ? "bg-blue-600 text-white border-blue-500 shadow-md transform scale-[1.01]"
                                        : "bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700 hover:border-gray-500"
                                    }
                                `}
                      >
                        <span className="font-medium text-base">
                          Đoạn {chunk.id + 1}
                        </span>
                        {isActive && (
                          <div className="flex flex-col items-end gap-1">
                            <span className="text-xs bg-white/20 px-2 py-0.5 rounded text-white animate-pulse">
                              Đang đọc {chunkProgress}%
                            </span>
                            <div className="w-24 h-1 bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-blue-400 transition-all duration-300 ease-out"
                                style={{ width: `${chunkProgress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
              </div>
            ) : (
              visibleChunks.map((chunk, index) => {
                const isActive = chunk.id === currentChunkIndex;
                return (
                  <div
                    key={chunk.id}
                    ref={isActive ? activeChunkRef : null}
                    onClick={() => {
                      handleStop();
                      setCurrentChunkIndex(chunk.id);
                      playChunk(chunk.id);
                    }}
                    className={`p-5 rounded-xl text-lg md:text-xl leading-relaxed transition-all duration-300 cursor-pointer ${
                      isActive
                        ? "bg-blue-900/20 border-l-4 border-blue-500 text-gray-100 shadow-lg"
                        : "text-gray-400 hover:text-gray-300 hover:bg-gray-900/50"
                    }`}
                  >
                    <span className="text-xs text-gray-600 font-mono block mb-1">
                      #{chunk.id + 1}
                    </span>
                    {chunk.text}
                  </div>
                );
              })
            )}

            {settings.viewMode === "continuous" &&
              visibleRange.end < chunks.length && (
                <div className="text-center py-2 text-gray-600 text-xs animate-pulse">
                  ... tải thêm ...
                </div>
              )}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            Đang xử lý văn bản...
          </div>
        )}
      </main>

      {/* Error Toast */}
      {errorMsg && (
        <div className="fixed top-24 left-1/2 -translate-x-1/2 bg-red-950 text-white px-6 py-4 rounded-xl shadow-2xl z-[1000] border border-red-500 flex flex-col items-center gap-2 max-w-sm text-center animate-in zoom-in-95">
          <div className="flex items-center gap-2 text-red-300 font-bold">
            <AlertCircle size={20} /> Lỗi
          </div>
          <span className="text-sm opacity-90">{errorMsg}</span>
          <button
            onClick={() => setErrorMsg(null)}
            className="mt-2 bg-red-900/50 hover:bg-red-800 px-4 py-1 rounded text-xs"
          >
            Đóng
          </button>
        </div>
      )}

      {/* Footer Controls */}
      <footer className="absolute bottom-0 w-full bg-gray-900/95 backdrop-blur-lg border-t border-gray-800 p-4 z-40 shadow-lg">
        <div className="max-w-2xl mx-auto flex items-center justify-center gap-4 sm:gap-6 mb-4">
          <button
            onClick={() => handleNavigate(-1)}
            className="p-3 text-gray-400 hover:text-white rounded-full disabled:opacity-30"
            disabled={currentChunkIndex === 0}
          >
            <SkipBack size={24} />
          </button>
          <button
            onClick={handlePlayPause}
            className={`w-16 h-16 flex items-center justify-center rounded-full shadow-lg transition-transform active:scale-95 ${
              readerState === ReaderState.LOADING
                ? "bg-gray-700"
                : "bg-blue-600 hover:bg-blue-500 text-white"
            }`}
          >
            {readerState === ReaderState.LOADING ? (
              <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : readerState === ReaderState.PLAYING ? (
              <Pause size={32} fill="currentColor" />
            ) : (
              <Play size={32} fill="currentColor" className="ml-1" />
            )}
          </button>
          <button
            onClick={handleStop}
            className="p-3 text-gray-400 hover:text-red-400 rounded-full"
          >
            <Square size={20} fill="currentColor" />
          </button>
          <button
            onClick={() => handleNavigate(1)}
            className="p-3 text-gray-400 hover:text-white rounded-full disabled:opacity-30"
            disabled={currentChunkIndex >= chunks.length - 1}
          >
            <SkipForward size={24} />
          </button>
        </div>

        <div className="flex flex-wrap justify-center items-center gap-4 text-xs text-gray-500 font-mono pb-safe">
          <div className="flex items-center gap-1">
            <Gauge size={14} />
            <span>{settings.playbackRate}x</span>
          </div>
          <div className="h-4 w-px bg-gray-800"></div>
          <div className="flex items-center gap-1">
            <Volume2 size={14} />
            <span>{settings.volume}%</span>
          </div>
          <div className="w-full sm:w-auto flex justify-center mt-2 sm:mt-0">
            <div className="flex items-center gap-3 bg-gray-800 rounded-xl px-4 py-2 border border-gray-700 shadow-inner">
              <input
                type="number"
                className="w-16 bg-transparent text-center text-white outline-none text-lg font-bold placeholder:text-gray-600"
                placeholder={(currentChunkIndex + 1).toString()}
                value={jumpTarget}
                onChange={(e) => setJumpTarget(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleJump()}
              />
              <span className="text-sm font-medium">/ {chunks.length}</span>
              <button
                onClick={handleJump}
                disabled={!jumpTarget}
                className="p-1 bg-blue-600 text-white rounded-lg disabled:opacity-50 hover:bg-blue-500 transition-colors"
              >
                <CornerDownRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

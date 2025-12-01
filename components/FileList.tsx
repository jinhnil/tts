import React, { useRef, useState } from 'react';
import { TextFile } from '../types';
import { FolderOpen, FileText, ChevronRight, Loader2 } from 'lucide-react';

interface FileListProps {
  files: TextFile[];
  setFiles: (files: TextFile[]) => void;
  onFileSelect: (file: TextFile) => void;
  lastPlayedFileName?: string;
}

export const FileList: React.FC<FileListProps> = ({ 
  files, 
  setFiles, 
  onFileSelect, 
  lastPlayedFileName
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFolderSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    setIsLoading(true);
    const fileList = event.target.files;
    if (!fileList) {
        setIsLoading(false);
        return;
    }

    const txtFiles: TextFile[] = [];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      if (file.name.toLowerCase().endsWith('.txt')) {
        txtFiles.push({
          name: file.name,
          path: file.webkitRelativePath || file.name,
          content: "", 
          fileHandle: file, 
          lastModified: file.lastModified
        });
      }
    }

    txtFiles.sort((a, b) => a.name.localeCompare(b.name));

    setFiles(txtFiles);
    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 p-6 max-w-4xl mx-auto w-full relative">
      <div className="mb-8 text-center mt-12">
        <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500 mb-2">
          Trình đọc TTS (Web Speech)
        </h1>
        <p className="text-gray-400 text-sm">Chọn thư mục để tải danh sách file</p>
      </div>

      <div className="mb-6 flex justify-center">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFolderSelect}
          className="hidden"
          /* @ts-ignore: webkitdirectory is non-standard but supported */
          webkitdirectory=""
          directory=""
          multiple
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl transition-all shadow-lg shadow-blue-900/20 active:scale-95"
        >
          {isLoading ? <Loader2 className="animate-spin" size={20} /> : <FolderOpen size={20} />}
          <span>Mở Thư mục</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-gray-900 rounded-2xl border border-gray-800 shadow-inner p-2">
        {files.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-60">
            <FileText size={48} className="mb-4" />
            <p>Chưa có file .txt nào</p>
          </div>
        ) : (
          <ul className="space-y-1">
            {files.map((file) => (
              <li key={file.path}>
                <button
                  onClick={() => onFileSelect(file)}
                  className={`w-full text-left px-4 py-3 rounded-lg flex items-center justify-between group transition-colors ${
                    file.name === lastPlayedFileName
                      ? 'bg-blue-900/30 border border-blue-800 text-blue-100'
                      : 'hover:bg-gray-800 text-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText size={18} className={file.name === lastPlayedFileName ? "text-blue-400" : "text-gray-500"} />
                    <span className="truncate font-medium">{file.name}</span>
                    {file.name === lastPlayedFileName && (
                        <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full ml-2">Gần đây</span>
                    )}
                  </div>
                  <ChevronRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-500" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
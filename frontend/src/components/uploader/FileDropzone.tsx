import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export interface FileDropzoneProps {
  onFileSelect: (file: File | null) => void;
  selectedFile?: File | null;
  disabled?: boolean;
}

/**
 * Format bytes into human-readable KB / MB.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 KB';
  const k = 1024;
  if (bytes < k * 1024) {
    return `${(bytes / k).toFixed(1)} KB`;
  }
  return `${(bytes / (k * k)).toFixed(2)} MB`;
}

/**
 * CAI Campus Intelligence — Notice PDF Dropzone Component (M02 / M04 / P4)
 * Reference: docs/API_CONTRACTS.md §8.1 (POST /api/v1/uploader/notices)
 *
 * Provides drag-and-drop file upload with client-side validation:
 * - Strictly validates .pdf extension / application/pdf MIME type
 * - Enforces <= 10MB file size limit
 * - Visual drag-over feedback
 * - File preview details (filename, formatted size) with remove action
 */
export const FileDropzone: React.FC<FileDropzoneProps> = ({
  onFileSelect,
  selectedFile: externalSelectedFile,
  disabled = false,
}) => {
  const [internalFile, setInternalFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Support controlled or uncontrolled mode
  const currentFile = externalSelectedFile !== undefined ? externalSelectedFile : internalFile;

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    const isPdf =
      file.name.toLowerCase().endsWith('.pdf') ||
      file.type === 'application/pdf';

    if (!isPdf) {
      return {
        valid: false,
        error: 'Unsupported file type. Only PDF documents (.pdf) are allowed for notice ingestion.',
      };
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return {
        valid: false,
        error: `File size exceeds the 10MB limit (Selected: ${formatFileSize(file.size)}). Please select a file under 10MB.`,
      };
    }

    if (file.size === 0) {
      return {
        valid: false,
        error: 'The selected file is empty (0 bytes). Please upload a valid PDF notice.',
      };
    }

    return { valid: true };
  };

  const processFile = (file: File | null) => {
    if (!file) {
      handleRemove();
      return;
    }

    setErrorMessage(null);
    const validation = validateFile(file);

    if (!validation.valid) {
      setErrorMessage(validation.error || 'Invalid file selected.');
      handleRemove();
      return;
    }

    setInternalFile(file);
    onFileSelect(file);
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    setIsDragOver(true);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // Only deactivate if leaving the container itself
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      processFile(droppedFile);
      e.dataTransfer.clearData();
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const handleBrowseClick = () => {
    if (disabled) return;
    fileInputRef.current?.click();
  };

  const handleRemove = () => {
    setInternalFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onFileSelect(null);
  };

  return (
    <div className="w-full space-y-4">
      {/* Hidden native file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="hidden"
        onChange={handleFileInputChange}
        disabled={disabled}
      />

      {/* Error alert banner */}
      {errorMessage && (
        <div
          role="alert"
          className="bg-rose-50 border-l-4 border-rose-500 p-3.5 rounded-r-lg flex items-start space-x-3 text-rose-800"
        >
          <svg
            className="w-5 h-5 text-rose-500 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div className="flex-1 text-sm font-medium">{errorMessage}</div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-rose-600 transition"
            aria-label="Dismiss error"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Selected file preview card OR Dropzone box */}
      {currentFile ? (
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-3.5 min-w-0">
            {/* PDF File Icon */}
            <div className="w-11 h-11 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center flex-shrink-0 text-rose-600">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zM6 20V4h7v5h5v11H6z" />
                <path d="M9 13h2v3H9zM13 13h2v3h-2z" />
              </svg>
            </div>

            {/* File info */}
            <div className="min-w-0">
              <p className="text-sm font-semibold text-slate-900 truncate" title={currentFile.name}>
                {currentFile.name}
              </p>
              <div className="flex items-center space-x-2 text-xs text-slate-500 mt-0.5">
                <span className="font-medium text-slate-600">
                  {formatFileSize(currentFile.size)}
                </span>
                <span>&bull;</span>
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Ready for upload
                </span>
              </div>
            </div>
          </div>

          {/* Remove / Change actions */}
          <div className="flex items-center space-x-2 flex-shrink-0 ml-4">
            <button
              type="button"
              onClick={handleBrowseClick}
              disabled={disabled}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition disabled:opacity-50"
            >
              Change
            </button>
            <button
              type="button"
              onClick={handleRemove}
              disabled={disabled}
              className="px-3 py-1.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-lg transition disabled:opacity-50 flex items-center space-x-1"
            >
              <svg className="w-3.5 h-3.5 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              <span>Remove</span>
            </button>
          </div>
        </div>
      ) : (
        /* Dropzone area */
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleBrowseClick}
          className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            disabled
              ? 'bg-slate-100 border-slate-300 opacity-60 cursor-not-allowed'
              : isDragOver
              ? 'border-indigo-500 bg-indigo-50/70 ring-4 ring-indigo-100/80 scale-[1.01]'
              : 'border-slate-300 bg-slate-50/60 hover:bg-slate-50 hover:border-indigo-400'
          }`}
          role="region"
          aria-label="Notice PDF dropzone"
        >
          {/* Center Upload Graphic */}
          <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors ${
                isDragOver ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-600'
              }`}
            >
              <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-800">
                {isDragOver ? (
                  <span className="text-indigo-600">Drop your notice PDF here</span>
                ) : (
                  <>
                    <span>Drag and drop notice PDF here, or </span>
                    <span className="text-indigo-600 underline font-semibold">browse files</span>
                  </>
                )}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Accepted format: <span className="font-medium text-slate-700">PDF (.pdf)</span> &bull; Maximum size:{' '}
                <span className="font-medium text-slate-700">10MB</span>
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileDropzone;

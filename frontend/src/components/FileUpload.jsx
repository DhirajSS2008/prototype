import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadFile } from '../api/client';
import ConfidenceBadge from './ConfidenceBadge';

export default function FileUpload({ onUploadComplete }) {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles) => {
    setFiles(acceptedFiles);
    setUploading(true);
    setProgress(0);
    setResults([]);

    const allResults = [];

    for (let i = 0; i < acceptedFiles.length; i++) {
      const file = acceptedFiles[i];
      try {
        const res = await uploadFile(file, (pct) => {
          const overallPct = Math.round(((i + pct / 100) / acceptedFiles.length) * 100);
          setProgress(overallPct);
        });
        allResults.push({
          filename: file.name,
          status: 'success',
          data: res.data,
        });
      } catch (err) {
        allResults.push({
          filename: file.name,
          status: 'error',
          error: err.response?.data?.detail || err.message,
        });
      }
    }

    setResults(allResults);
    setUploading(false);
    setProgress(100);
    if (onUploadComplete) onUploadComplete(allResults);
  }, [onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'],
    },
    disabled: uploading,
  });

  const getFileIcon = (name) => {
    if (name.endsWith('.pdf')) return <FileText size={18} style={{ color: 'var(--color-critical)' }} />;
    return <Image size={18} style={{ color: 'var(--color-defer)' }} />;
  };

  return (
    <div className="space-y-6">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'dropzone-active' : ''} ${uploading ? 'opacity-50 cursor-wait' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div
            className="w-16 h-16 rounded-2xl flex items-center justify-center"
            style={{
              background: isDragActive
                ? 'var(--color-primary-container)'
                : 'var(--color-surface-highest)',
            }}
          >
            <Upload
              size={28}
              style={{ color: isDragActive ? 'var(--color-primary)' : 'var(--color-on-surface-variant)' }}
            />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium" style={{ color: 'var(--color-on-surface)' }}>
              {isDragActive ? 'Drop files here...' : 'Drag & drop bank PDFs, invoices, or receipts'}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-on-surface-variant)' }}>
              Supports PDF, PNG, JPG, TIFF • Max 10MB per file
            </p>
          </div>
          <button className="btn btn-secondary text-xs" type="button">
            Browse Files
          </button>
        </div>
      </div>

      {/* Progress */}
      {uploading && (
        <div className="animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm flex items-center gap-2" style={{ color: 'var(--color-on-surface-variant)' }}>
              <Loader2 size={16} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
              Processing files...
            </span>
            <span className="text-sm font-medium" style={{ color: 'var(--color-primary)' }}>
              {progress}%
            </span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3 animate-fade-in">
          <h3 className="text-headline text-sm font-semibold">Processed Files</h3>
          {results.map((result, idx) => (
            <div
              key={idx}
              className="card flex items-start gap-3"
              style={{
                background: result.status === 'success'
                  ? 'var(--color-surface-container)'
                  : 'rgba(239, 68, 68, 0.06)',
              }}
            >
              <div className="flex-shrink-0 mt-0.5">
                {result.status === 'success' ? (
                  <CheckCircle size={18} style={{ color: 'var(--color-approve)' }} />
                ) : (
                  <AlertCircle size={18} style={{ color: 'var(--color-critical)' }} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  {getFileIcon(result.filename)}
                  <span className="text-sm font-medium truncate">{result.filename}</span>
                </div>

                {result.status === 'success' && result.data && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs" style={{ color: 'var(--color-on-surface-variant)' }}>
                      {result.data.transactions_extracted} transaction{result.data.transactions_extracted !== 1 ? 's' : ''} extracted
                    </p>
                    {result.data.transactions?.map((tx, txIdx) => (
                      <div
                        key={txIdx}
                        className="flex items-center justify-between p-2 rounded-lg text-xs"
                        style={{ background: 'var(--color-surface-low)' }}
                      >
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="truncate">{tx.counterparty || tx.category}</span>
                          <ConfidenceBadge score={tx.confidence} />
                        </div>
                        <span className="font-medium ml-2" style={{
                          color: tx.amount < 0 ? 'var(--color-critical)' : 'var(--color-approve)'
                        }}>
                          ₹{Math.abs(tx.amount).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {result.status === 'error' && (
                  <p className="text-xs mt-1" style={{ color: 'var(--color-critical)' }}>
                    {result.error}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

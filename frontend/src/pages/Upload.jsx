import { useState } from 'react';
import { Upload as UploadIcon, FileText, HelpCircle } from 'lucide-react';
import FileUpload from '../components/FileUpload';

export default function UploadPage() {
  const [uploadResults, setUploadResults] = useState([]);

  const totalExtracted = uploadResults.reduce(
    (sum, r) => sum + (r.data?.transactions_extracted || 0),
    0
  );

  return (
    <div className="space-y-6 animate-fade-in max-w-3xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-headline text-2xl font-bold flex items-center gap-3">
          <UploadIcon size={24} style={{ color: 'var(--color-primary)' }} />
          Upload Documents
        </h2>
        <p className="text-sm mt-1" style={{ color: 'var(--color-on-surface-variant)' }}>
          Upload bank statements, invoices, or receipt images to extract transaction data.
        </p>
      </div>

      {/* Upload Area */}
      <div className="card-glass">
        <FileUpload onUploadComplete={setUploadResults} />
      </div>

      {/* Summary */}
      {uploadResults.length > 0 && (
        <div className="card-glass animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-label">Upload Summary</p>
              <p className="text-display text-xl mt-1">
                {totalExtracted} transaction{totalExtracted !== 1 ? 's' : ''} extracted
              </p>
            </div>
            <div className="text-right">
              <p className="text-label">Files Processed</p>
              <p className="text-display text-xl mt-1">
                {uploadResults.filter((r) => r.status === 'success').length}
                <span className="text-sm font-normal ml-1" style={{ color: 'var(--color-on-surface-variant)' }}>
                  of {uploadResults.length}
                </span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Help Tips */}
      <div
        className="rounded-xl p-4"
        style={{ background: 'var(--color-surface-container)' }}
      >
        <h3 className="text-sm font-semibold flex items-center gap-2 mb-3">
          <HelpCircle size={16} style={{ color: 'var(--color-primary)' }} />
          Tips for Better Extraction
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs"
          style={{ color: 'var(--color-on-surface-variant)' }}>
          <div className="flex items-start gap-2">
            <FileText size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--color-tertiary)' }} />
            <div>
              <p className="font-medium" style={{ color: 'var(--color-on-surface)' }}>Bank PDFs</p>
              <p>Works best with digitally generated PDFs. Scanned PDFs may have lower confidence scores.</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <FileText size={14} className="flex-shrink-0 mt-0.5" style={{ color: 'var(--color-tertiary)' }} />
            <div>
              <p className="font-medium" style={{ color: 'var(--color-on-surface)' }}>Receipt Images</p>
              <p>Use well-lit, high-contrast photos. Avoid blurry or skewed images for best OCR results.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

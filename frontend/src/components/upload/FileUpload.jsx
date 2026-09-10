import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { api } from '../../api/apiClient';
import { UploadCloud, CheckCircle2, XCircle, Loader2 } from 'lucide-react';

const UPLOAD_TYPES = [
  { id: 'fir', label: 'FIR Document', accept: '.pdf,.txt,.docx', description: 'Police reports in PDF or text format' },
  { id: 'callRecords', label: 'Call Records (CDR)', accept: '.csv,.xlsx', description: 'Call detail records in CSV/Excel' },
  { id: 'transactions', label: 'Financial Transactions', accept: '.csv,.xlsx', description: 'Bank transaction records' },
];

function UploadZone({ type, caseId }) {
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    if (caseId) formData.append('case_id', caseId);

    try {
      let response;
      if (type.id === 'fir') response = await api.uploadFIR(formData);
      else if (type.id === 'callRecords') response = await api.uploadCallRecords(formData);
      else response = await api.uploadTransactions(formData);

      setStatus('success');
      setMessage(response.data?.message || 'Upload successful');
    } catch (err) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Upload failed — is the backend running?');
    }
  }, [type, caseId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, maxFiles: 1 });

  return (
    <div className="bg-base-surface border border-base-border rounded-lg p-5">
      <h3 className="text-ink-primary font-medium text-sm">{type.label}</h3>
      <p className="text-ink-faint text-xs mb-4">{type.description}</p>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-md p-8 text-center cursor-pointer transition-colors focus-ring ${
          isDragActive ? 'border-signal bg-signal/5' : 'border-base-border hover:border-base-borderLight'
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mx-auto mb-3 text-ink-faint" size={26} strokeWidth={1.6} />
        {isDragActive ? (
          <p className="text-signal text-sm">Drop file here…</p>
        ) : (
          <>
            <p className="text-ink-muted text-sm mb-1">Drag & drop, or click to browse</p>
            <p className="text-ink-faint text-xs font-mono">{type.accept}</p>
          </>
        )}
      </div>

      {status === 'uploading' && (
        <div className="mt-3 text-signal text-sm flex items-center gap-2">
          <Loader2 size={14} className="animate-spin" /> Uploading…
        </div>
      )}
      {status === 'success' && (
        <div className="mt-3 text-risk-low text-sm flex items-center gap-2">
          <CheckCircle2 size={14} /> {message}
        </div>
      )}
      {status === 'error' && (
        <div className="mt-3 text-risk-critical text-sm flex items-center gap-2">
          <XCircle size={14} /> {message}
        </div>
      )}
    </div>
  );
}

export default function FileUploadPage() {
  const [caseId, setCaseId] = useState('');

  return (
    <div>
      <div className="mb-6 max-w-xs">
        <label className="block text-ink-faint text-xs mb-2">Case ID (optional)</label>
        <input
          type="number"
          value={caseId}
          onChange={e => setCaseId(e.target.value)}
          placeholder="e.g. 1"
          className="w-full bg-base-surface border border-base-border rounded-md px-3 py-2 text-ink-primary placeholder-ink-faint text-sm focus:outline-none focus:border-signal/60 transition-colors"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {UPLOAD_TYPES.map(type => (
          <UploadZone key={type.id} type={type} caseId={caseId} />
        ))}
      </div>
    </div>
  );
}

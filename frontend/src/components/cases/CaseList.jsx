import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/apiClient';
import { FolderClosed, ChevronRight } from 'lucide-react';

export default function CaseList({ onSelect, selectedId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['cases'],
    queryFn: () => api.getCases().then(r => r.data),
  });

  const cases = data?.cases || data || [];

  return (
    <div className="bg-base-surface rounded-lg border border-base-border overflow-hidden">
      <div className="px-4 py-3 border-b border-base-border flex items-center gap-2">
        <FolderClosed size={15} className="text-signal" />
        <span className="text-ink-primary font-medium text-sm">Active Cases</span>
      </div>
      <div className="divide-y divide-base-border/60 max-h-[560px] overflow-y-auto">
        {isLoading && <div className="p-4 text-ink-faint text-sm">Loading cases…</div>}
        {error && <div className="p-4 text-ink-faint text-sm">Backend not reachable (port 8000).</div>}
        {!isLoading && !error && cases.length === 0 && (
          <div className="p-4 text-ink-faint text-sm">No cases yet — create one to get started.</div>
        )}
        {cases.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect?.(c.id)}
            className={`w-full text-left px-4 py-3 flex items-center justify-between gap-2 transition-colors focus-ring ${
              selectedId === c.id ? 'bg-signal/10' : 'hover:bg-base-raised'
            }`}
          >
            <div className="min-w-0">
              <div className="text-ink-primary text-sm font-medium truncate">{c.title || c.case_number}</div>
              <div className="text-ink-faint text-xs font-mono mt-0.5">{c.case_number} · {c.status}</div>
            </div>
            <ChevronRight size={14} className="text-ink-faint shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}

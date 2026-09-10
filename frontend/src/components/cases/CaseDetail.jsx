import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/apiClient';
import { FileText, Phone, Landmark } from 'lucide-react';

export default function CaseDetail({ caseId }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['caseSummary', caseId],
    queryFn: () => api.getCaseSummary(caseId).then(r => r.data),
    enabled: !!caseId,
  });

  if (!caseId) {
    return (
      <div className="bg-base-surface rounded-lg border border-base-border p-10 text-center text-ink-faint text-sm">
        Select a case from the list to view details.
      </div>
    );
  }

  if (isLoading) return <div className="bg-base-surface rounded-lg border border-base-border p-6 text-ink-faint text-sm">Loading case…</div>;
  if (error) return <div className="bg-base-surface rounded-lg border border-base-border p-6 text-ink-faint text-sm">Could not load this case.</div>;

  const c = data?.case || {};

  return (
    <div className="bg-base-surface rounded-lg border border-base-border p-6">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-lg font-semibold text-ink-primary">{c.title || 'Untitled Case'}</h2>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded border border-signal/30 text-signal bg-signal/10">
          {c.status || 'unknown'}
        </span>
      </div>
      <div className="text-ink-faint text-xs font-mono mb-6">{c.case_number}</div>

      <div className="grid grid-cols-3 gap-4">
        <div className="border border-base-border rounded-md p-4 flex items-center gap-3">
          <FileText size={18} className="text-signal" />
          <div>
            <div className="text-xl font-mono text-ink-primary">{data?.total_firs ?? 0}</div>
            <div className="text-[11px] text-ink-faint">FIRs</div>
          </div>
        </div>
        <div className="border border-base-border rounded-md p-4 flex items-center gap-3">
          <Phone size={18} className="text-risk-medium" />
          <div>
            <div className="text-xl font-mono text-ink-primary">{data?.total_call_records ?? 0}</div>
            <div className="text-[11px] text-ink-faint">Call Records</div>
          </div>
        </div>
        <div className="border border-base-border rounded-md p-4 flex items-center gap-3">
          <Landmark size={18} className="text-risk-low" />
          <div>
            <div className="text-xl font-mono text-ink-primary">{data?.total_transactions ?? 0}</div>
            <div className="text-[11px] text-ink-faint">Transactions</div>
          </div>
        </div>
      </div>
    </div>
  );
}

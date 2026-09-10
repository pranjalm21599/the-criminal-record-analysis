import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/apiClient';
import { Target } from 'lucide-react';

const RISK_STYLES = {
  CRITICAL: 'bg-risk-critical/10 text-risk-critical border-risk-critical/30',
  HIGH: 'bg-risk-high/10 text-risk-high border-risk-high/30',
  MEDIUM: 'bg-risk-medium/10 text-risk-medium border-risk-medium/30',
  LOW: 'bg-risk-low/10 text-risk-low border-risk-low/30',
};

export default function RiskTable({ onPersonClick }) {
  const { data, isLoading } = useQuery({
    queryKey: ['riskScores'],
    queryFn: () => api.getRiskScores().then(r => r.data),
  });

  const topSuspects = data?.top_suspects || [];

  return (
    <div className="bg-base-surface rounded-lg border border-base-border p-5">
      <h3 className="text-ink-primary font-medium text-sm flex items-center gap-2 mb-4">
        <Target size={15} className="text-risk-high" />
        Top Suspects by Risk Score
      </h3>

      {isLoading ? (
        <div className="text-ink-faint text-sm">Loading risk scores…</div>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-base-border text-left">
              <th className="py-2 text-ink-faint font-normal text-xs w-8">#</th>
              <th className="py-2 text-ink-faint font-normal text-xs">Person</th>
              <th className="py-2 text-ink-faint font-normal text-xs">Score</th>
              <th className="py-2 text-ink-faint font-normal text-xs">Level</th>
            </tr>
          </thead>
          <tbody>
            {topSuspects.map((person, i) => (
              <tr
                key={person.person}
                className="border-b border-base-border/60 last:border-0 cursor-pointer group"
                onClick={() => onPersonClick?.(person.person)}
              >
                <td className="py-3 text-ink-faint font-mono text-xs">{String(i + 1).padStart(2, '0')}</td>
                <td className="py-3 text-ink-primary font-medium group-hover:text-signal transition-colors">{person.person}</td>
                <td className="py-3">
                  <div className="flex items-center gap-2">
                    <div className="bg-base-border rounded-full h-1.5 w-16 overflow-hidden">
                      <div className="bg-signal h-1.5 rounded-full transition-all" style={{ width: `${person.risk_score}%` }} />
                    </div>
                    <span className="text-ink-primary font-mono text-xs mono-tabular">{person.risk_score}</span>
                  </div>
                </td>
                <td className="py-3">
                  <span className={`px-2 py-0.5 rounded text-[11px] border font-mono ${RISK_STYLES[person.risk_level] || ''}`}>
                    {person.risk_level}
                  </span>
                </td>
              </tr>
            ))}
            {topSuspects.length === 0 && (
              <tr><td colSpan="4" className="py-8 text-center text-ink-faint text-sm">No data yet — run analysis first.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

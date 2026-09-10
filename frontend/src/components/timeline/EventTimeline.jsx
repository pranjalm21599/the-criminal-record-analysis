import { Clock } from 'lucide-react';

// Lightweight custom timeline (no external timeline lib required).
// Pass events as [{ time: '2024-03-14', title: '...', description: '...', type: 'fir'|'call'|'transaction'|'alert' }]
const TYPE_COLOR = {
  fir: 'bg-signal',
  call: 'bg-risk-medium',
  transaction: 'bg-risk-low',
  alert: 'bg-risk-critical',
  default: 'bg-ink-faint',
};

export default function EventTimeline({ events = [] }) {
  return (
    <div className="bg-base-surface rounded-lg border border-base-border p-5">
      <h3 className="text-ink-primary font-medium text-sm flex items-center gap-2 mb-5">
        <Clock size={15} className="text-signal" />
        Case Timeline
      </h3>

      {events.length === 0 ? (
        <div className="text-ink-faint text-sm py-6 text-center">
          No timeline events yet. They'll appear here as evidence is processed.
        </div>
      ) : (
        <div className="relative pl-5">
          <div className="absolute left-[7px] top-1 bottom-1 w-px bg-base-border" />
          <div className="space-y-5">
            {events.map((e, i) => (
              <div key={i} className="relative group">
                <span className={`absolute -left-5 top-1 w-2.5 h-2.5 rounded-full ring-4 ring-base-surface ${TYPE_COLOR[e.type] || TYPE_COLOR.default}`} />
                <div className="text-[11px] font-mono text-ink-faint mb-0.5">{e.time}</div>
                <div className="text-sm text-ink-primary font-medium group-hover:text-signal transition-colors">{e.title}</div>
                {e.description && <div className="text-xs text-ink-muted mt-0.5">{e.description}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

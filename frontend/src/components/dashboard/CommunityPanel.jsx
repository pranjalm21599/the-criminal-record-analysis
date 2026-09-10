import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/apiClient';
import { Users2 } from 'lucide-react';

export default function CommunityPanel() {
  const { data, isLoading } = useQuery({
    queryKey: ['communities'],
    queryFn: () => api.getCommunities().then(r => r.data),
  });

  const communities = data?.communities || [];

  return (
    <div className="bg-base-surface rounded-lg border border-base-border p-5">
      <h3 className="text-ink-primary font-medium text-sm flex items-center gap-2 mb-4">
        <Users2 size={15} className="text-signal" />
        Detected Groups
      </h3>

      {isLoading ? (
        <div className="text-ink-faint text-sm">Loading…</div>
      ) : communities.length === 0 ? (
        <div className="text-ink-faint text-sm py-4 text-center">No groups detected yet.</div>
      ) : (
        <div className="space-y-3">
          {communities.map((c) => (
            <div key={c.label} className="border border-base-border rounded-md p-3 hover:border-base-borderLight transition-colors">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-ink-primary text-sm font-medium">{c.label}</span>
                <span className="text-[11px] font-mono text-ink-faint">{c.size} members</span>
              </div>
              <div className="text-xs text-ink-muted truncate">{(c.members || []).join(', ')}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

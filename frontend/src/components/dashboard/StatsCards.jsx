import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/apiClient';
import { Users, Waypoints, TriangleAlert, FileStack } from 'lucide-react';

function StatCard({ title, value, icon: Icon, accent, subtitle }) {
  return (
    <div className="group bg-base-surface border border-base-border rounded-lg p-5 transition-all hover:border-base-borderLight hover:-translate-y-0.5">
      <div className="flex items-start justify-between">
        <span className="text-ink-muted text-xs font-medium tracking-wide">{title}</span>
        <Icon size={16} className={accent} strokeWidth={1.8} />
      </div>
      <div className="text-3xl font-semibold text-ink-primary mt-3 mono-tabular font-mono">{value}</div>
      {subtitle && <div className="text-[11px] text-ink-faint mt-1">{subtitle}</div>}
    </div>
  );
}

export default function StatsCards() {
  const { data: stats } = useQuery({
    queryKey: ['graphStats'],
    queryFn: () => api.getGraphStats().then(r => r.data),
    refetchInterval: 30000,
  });

  const { data: risks } = useQuery({
    queryKey: ['riskScores'],
    queryFn: () => api.getRiskScores().then(r => r.data),
  });

  const nodeCountMap = {};
  (stats?.node_counts || []).forEach(item => { nodeCountMap[item.node_type] = item.count; });
  const totalRelationships = (stats?.relationship_counts || []).reduce((a, b) => a + b.count, 0);

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard title="TOTAL PERSONS" value={nodeCountMap['Person'] ?? '—'} icon={Users} accent="text-signal" subtitle="Entities in the network" />
      <StatCard title="CONNECTIONS" value={totalRelationships || '—'} icon={Waypoints} accent="text-[#B57BEE]" subtitle="Relationships mapped" />
      <StatCard title="CRITICAL RISK" value={risks?.critical_risk ?? '—'} icon={TriangleAlert} accent="text-risk-critical" subtitle="High priority suspects" />
      <StatCard title="FIRs PROCESSED" value={nodeCountMap['FIR'] ?? '—'} icon={FileStack} accent="text-risk-low" subtitle="Documents analyzed" />
    </div>
  );
}

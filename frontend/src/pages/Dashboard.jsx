import { useState } from 'react';
import Header from '../components/layout/Header';
import StatsCards from '../components/dashboard/StatsCards';
import RiskTable from '../components/dashboard/RiskTable';
import CommunityPanel from '../components/dashboard/CommunityPanel';
import NetworkGraph from '../components/graph/NetworkGraph';
import { api } from '../api/apiClient';
import { RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const [selectedPerson, setSelectedPerson] = useState('');
  const [searchName, setSearchName] = useState('');
  const [running, setRunning] = useState(false);

  const runAnalysis = async () => {
    setRunning(true);
    try { await api.runFullAnalysis(); } catch (e) { /* surfaced via empty tables */ }
    setRunning(false);
  };

  return (
    <div>
      <Header title="Overview" subtitle="Live snapshot of the criminal network under investigation" />

      <div className="flex justify-end mb-5">
        <button
          onClick={runAnalysis}
          disabled={running}
          className="flex items-center gap-2 bg-signal/10 hover:bg-signal/20 text-signal border border-signal/30 px-3.5 py-2 rounded-md text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={running ? 'animate-spin' : ''} />
          {running ? 'Running analysis…' : 'Run Full Analysis'}
        </button>
      </div>

      <div className="mb-6"><StatsCards /></div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2">
            <input
              value={searchName}
              onChange={e => setSearchName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && setSelectedPerson(searchName)}
              placeholder="Enter a person's name to explore their network…"
              className="flex-1 bg-base-surface border border-base-border rounded-md px-3.5 py-2.5 text-sm text-ink-primary placeholder-ink-faint focus:outline-none focus:border-signal/60 transition-colors"
            />
            <button
              onClick={() => setSelectedPerson(searchName)}
              className="bg-signal text-white px-4 py-2.5 rounded-md text-sm font-medium hover:bg-signal-dim transition-colors"
            >
              Explore
            </button>
          </div>
          <NetworkGraph personName={selectedPerson} onNodeClick={(n) => setSelectedPerson(n.label)} />
        </div>

        <div className="space-y-4">
          <RiskTable onPersonClick={setSelectedPerson} />
          <CommunityPanel />
        </div>
      </div>
    </div>
  );
}

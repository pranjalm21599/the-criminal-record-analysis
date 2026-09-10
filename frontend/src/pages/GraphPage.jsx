import { useState } from 'react';
import Header from '../components/layout/Header';
import NetworkGraph from '../components/graph/NetworkGraph';

export default function GraphPage() {
  const [personName, setPersonName] = useState('');
  const [input, setInput] = useState('');

  return (
    <div>
      <Header title="Network Graph" subtitle="Trace connections between people, phones, vehicles, and locations" />
      <div className="flex gap-2 mb-5">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && setPersonName(input)}
          placeholder="Search a name to center the graph on…"
          className="flex-1 max-w-md bg-base-surface border border-base-border rounded-md px-3.5 py-2.5 text-sm text-ink-primary placeholder-ink-faint focus:outline-none focus:border-signal/60 transition-colors"
        />
        <button onClick={() => setPersonName(input)} className="bg-signal text-white px-4 py-2.5 rounded-md text-sm font-medium hover:bg-signal-dim transition-colors">
          Search
        </button>
      </div>
      <NetworkGraph personName={personName} onNodeClick={(n) => setPersonName(n.label)} />
    </div>
  );
}

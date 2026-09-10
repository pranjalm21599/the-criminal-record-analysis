import { useState } from 'react';
import Header from '../components/layout/Header';
import CaseList from '../components/cases/CaseList';
import CaseDetail from '../components/cases/CaseDetail';
import EventTimeline from '../components/timeline/EventTimeline';

export default function CasesPage() {
  const [selectedId, setSelectedId] = useState(null);

  return (
    <div>
      <Header title="Cases" subtitle="Every active investigation being tracked by the system" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div><CaseList onSelect={setSelectedId} selectedId={selectedId} /></div>
        <div className="lg:col-span-2 space-y-6">
          <CaseDetail caseId={selectedId} />
          <EventTimeline events={[]} />
        </div>
      </div>
    </div>
  );
}

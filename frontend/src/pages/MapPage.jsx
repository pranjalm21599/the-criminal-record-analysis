import Header from '../components/layout/Header';
import CrimeMap from '../components/map/CrimeMap';

export default function MapPage() {
  // Wire this up to real geocoded evidence once the backend exposes it.
  const locations = [];

  return (
    <div>
      <Header title="Crime Map" subtitle="Geographic distribution of reported incidents" />
      <CrimeMap locations={locations} />
    </div>
  );
}

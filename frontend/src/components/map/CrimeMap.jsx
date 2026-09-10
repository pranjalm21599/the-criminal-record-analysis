import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPinned } from 'lucide-react';

// locations: [{ lat, lng, label, severity: 'critical'|'high'|'medium'|'low' }]
const SEVERITY_COLOR = {
  critical: '#E5484D',
  high: '#F5A623',
  medium: '#F2C94C',
  low: '#27C93F',
};

export default function CrimeMap({ locations = [], center = [19.076, 72.877], zoom = 11 }) {
  return (
    <div className="bg-base-surface rounded-lg border border-base-border overflow-hidden">
      <div className="px-4 py-3 border-b border-base-border flex items-center gap-2">
        <MapPinned size={15} className="text-signal" />
        <span className="text-ink-primary font-medium text-sm">Crime Locations</span>
        <span className="text-[11px] text-ink-faint font-mono ml-auto">{locations.length} pins</span>
      </div>
      <div style={{ height: '520px' }}>
        <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%', background: '#10161F' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap &copy; CARTO'
          />
          {locations.map((loc, i) => (
            <CircleMarker
              key={i}
              center={[loc.lat, loc.lng]}
              radius={8}
              pathOptions={{
                color: SEVERITY_COLOR[loc.severity] || '#4C9AFF',
                fillColor: SEVERITY_COLOR[loc.severity] || '#4C9AFF',
                fillOpacity: 0.5,
                weight: 2,
              }}
            >
              <Popup>
                <div style={{ fontFamily: 'monospace', fontSize: 12 }}>{loc.label}</div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

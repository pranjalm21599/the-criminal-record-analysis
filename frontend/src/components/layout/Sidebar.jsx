import { Link, useLocation } from 'react-router-dom';
import {
  LayoutGrid, Waypoints, FolderClosed, MapPinned,
  UploadCloud, MessagesSquare, Radar
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutGrid, label: 'Overview' },
  { to: '/graph', icon: Waypoints, label: 'Network Graph' },
  { to: '/cases', icon: FolderClosed, label: 'Cases' },
  { to: '/map', icon: MapPinned, label: 'Crime Map' },
  { to: '/upload', icon: UploadCloud, label: 'Ingest Data' },
  { to: '/chat', icon: MessagesSquare, label: 'AI Assistant' },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-60 h-screen fixed left-0 top-0 bg-base-surface border-r border-base-border flex flex-col z-20">
      <div className="h-16 flex items-center gap-3 px-5 border-b border-base-border">
        <div className="relative w-7 h-7 flex items-center justify-center">
          <Radar size={20} className="text-signal" strokeWidth={2} />
          <span className="absolute inset-0 rounded-full border border-signal/40 animate-pulse_ring" />
        </div>
        <div className="leading-tight">
          <div className="text-ink-primary font-semibold text-sm tracking-tight">CrimeNet AI</div>
          <div className="text-ink-faint text-[11px] font-mono">SIH 2026 · NODE-06</div>
        </div>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => {
          const isActive = location.pathname === to;
          return (
            <Link
              key={to}
              to={to}
              className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors focus-ring ${
                isActive
                  ? 'bg-signal/10 text-ink-primary'
                  : 'text-ink-muted hover:bg-base-raised hover:text-ink-primary'
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 h-4 w-[2px] bg-signal rounded-full" />
              )}
              <Icon size={17} strokeWidth={1.8} className={isActive ? 'text-signal' : ''} />
              <span className="font-medium">{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-base-border">
        <div className="flex items-center gap-2 text-[11px] font-mono text-ink-faint">
          <span className="w-1.5 h-1.5 rounded-full bg-risk-low" />
          SYSTEM ACTIVE
        </div>
      </div>
    </aside>
  );
}

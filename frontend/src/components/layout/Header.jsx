import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';

export default function Header({ title, subtitle }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <header className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-xl font-semibold text-ink-primary tracking-tight">{title}</h1>
        {subtitle && <p className="text-ink-muted text-sm mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-2 bg-base-surface border border-base-border rounded-md px-3 py-1.5 text-ink-faint text-sm w-64 focus-within:border-signal/60 transition-colors">
          <Search size={14} />
          <input
            placeholder="Search a name, phone, or case…"
            className="bg-transparent outline-none text-ink-primary placeholder-ink-faint text-sm w-full"
          />
        </div>
        <div className="font-mono text-xs text-ink-faint mono-tabular hidden sm:block">
          {time.toLocaleTimeString([], { hour12: false })}
        </div>
      </div>
    </header>
  );
}

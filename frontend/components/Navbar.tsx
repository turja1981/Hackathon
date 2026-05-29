'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Brain } from 'lucide-react';
import { clsx } from 'clsx';

const NAV = [
  { href: '/', label: 'Home' },
  { href: '/search', label: 'Search' },
  { href: '/gaps', label: 'Gaps' },
  { href: '/hypotheses', label: 'Hypotheses' },
  { href: '/copilot', label: 'Copilot' },
  { href: '/radar', label: 'Radar' },
  { href: '/ingest', label: 'Ingest' },
];

export default function Navbar() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0f1e]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold text-sky-400 shrink-0">
          <Brain size={22} />
          <span>BioMind AI</span>
          <span className="hidden sm:block text-xs text-gray-600 font-normal">Research Discovery</span>
        </Link>
        <div className="flex items-center gap-0.5 overflow-x-auto">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                'rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors whitespace-nowrap',
                pathname === href
                  ? 'bg-sky-500/20 text-sky-400'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-white/5',
              )}
            >
              {label}
            </Link>
          ))}
        </div>
        <div className="ml-auto text-xs text-gray-600 shrink-0 hidden md:block">
          LangGraph · LiteLLM · FAISS
        </div>
      </div>
    </nav>
  );
}

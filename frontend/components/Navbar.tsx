'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FlaskConical } from 'lucide-react';
import { clsx } from 'clsx';

const NAV = [
  { href: '/', label: 'Home' },
  { href: '/search', label: 'Search' },
  { href: '/hypotheses', label: 'Hypotheses' },
  { href: '/ingest', label: 'Ingest' },
];

export default function Navbar() {
  const pathname = usePathname();
  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0f1e]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-8 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold text-sky-400">
          <FlaskConical size={22} />
          <span>LifeSci AI</span>
        </Link>
        <div className="flex items-center gap-1">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                pathname === href
                  ? 'bg-sky-500/20 text-sky-400'
                  : 'text-gray-400 hover:text-gray-100 hover:bg-white/5',
              )}
            >
              {label}
            </Link>
          ))}
        </div>
        <div className="ml-auto text-xs text-gray-600">
          Powered by LangGraph · LiteLLM · FAISS
        </div>
      </div>
    </nav>
  );
}

'use client';

import { FormEvent, useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';

interface Props {
  onSearch: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
  className?: string;
  initialValue?: string;
}

export default function SearchBar({
  onSearch,
  loading = false,
  placeholder = 'Search life sciences papers… e.g. "CRISPR Alzheimer's treatment"',
  className,
  initialValue = '',
}: Props) {
  const [query, setQuery] = useState(initialValue);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    if (q) onSearch(q);
  };

  return (
    <form onSubmit={handleSubmit} className={clsx('relative flex gap-2', className)}>
      <div className="relative flex-1">
        <Search
          size={18}
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
        />
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={placeholder}
          className="input pl-10"
          disabled={loading}
        />
      </div>
      <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading || !query.trim()}>
        {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
        Search
      </button>
    </form>
  );
}

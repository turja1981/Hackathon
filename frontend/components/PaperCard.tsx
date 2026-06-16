'use client';

import Link from 'next/link';
import { BookOpen, Users, Calendar, ExternalLink, Star } from 'lucide-react';
import type { Paper } from '@/lib/types';

interface Props {
  paper: Paper;
  showScore?: boolean;
}

export default function PaperCard({ paper, showScore = false }: Props) {
  const relevance = paper.score ? Math.round(paper.score * 100) : null;

  return (
    <div className="card group flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <Link
          href={`/paper/${paper.id}`}
          className="font-semibold text-sky-300 hover:text-sky-200 line-clamp-2 leading-snug transition-colors"
        >
          {paper.title}
        </Link>
        {showScore && relevance !== null && (
          <span className="badge shrink-0 bg-bio-100/10 text-bio-500 border border-bio-500/30">
            <Star size={10} />
            {relevance}%
          </span>
        )}
      </div>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
        {paper.authors.length > 0 && (
          <span className="flex items-center gap-1">
            <Users size={11} />
            {paper.authors.slice(0, 2).join(', ')}
            {paper.authors.length > 2 && ` +${paper.authors.length - 2}`}
          </span>
        )}
        {paper.journal && (
          <span className="flex items-center gap-1">
            <BookOpen size={11} />
            <em>{paper.journal}</em>
          </span>
        )}
        {paper.year && (
          <span className="flex items-center gap-1">
            <Calendar size={11} />
            {paper.year}
          </span>
        )}
        {paper.doi && (
          <a
            href={`https://doi.org/${paper.doi}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sky-600 hover:text-sky-400 transition-colors"
            onClick={e => e.stopPropagation()}
          >
            <ExternalLink size={11} />
            DOI
          </a>
        )}
        {paper.url && !paper.doi && (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-green-500 hover:text-green-400 transition-colors"
            onClick={e => e.stopPropagation()}
          >
            <ExternalLink size={11} />
            PubMed
          </a>
        )}
        {paper.source === 'pubmed' && (
          <span className="badge bg-green-900/30 text-green-400 border border-green-700/30">
            PubMed
          </span>
        )}
      </div>

      {/* Abstract preview */}
      <p className="text-sm text-gray-400 line-clamp-3 leading-relaxed">{paper.abstract}</p>

      {/* Keywords */}
      {paper.keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-1">
          {paper.keywords.slice(0, 6).map(kw => (
            <span key={kw} className="badge bg-white/5 text-gray-400 border border-white/10">
              {kw}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

import type { RegisterEntry, SourceRef } from '../types/results.ts';
import { Term } from './Term.tsx';

export const GRADE_TEXT: Record<string, string> = {
  A: 'A: measured',
  B: 'B: derived from measurements',
  C: 'C: judgment',
  R: 'R: set by the challenge rules or a design choice',
};

export function SourceList({ sources }: { sources: SourceRef[] }) {
  if (!sources.length) return null;
  return (
    <ul className="source-list">
      {sources.map((s, i) => (
        <li key={`${s.url}-${i}`}>
          <a href={s.url} target="_blank" rel="noreferrer">
            {s.title}
          </a>
          {s.locator && <span className="muted">, {s.locator}</span>}
          {s.accessed && <span className="muted"> (accessed {s.accessed})</span>}
          {s.quote && <q className="quote">{s.quote}</q>}
        </li>
      ))}
    </ul>
  );
}

export function GradeLine({ e }: { e: RegisterEntry }) {
  return (
    <p className="small muted">
      <Term term="grade">Grade</Term> {GRADE_TEXT[e.grade] ?? e.grade}; confidence {String(e.confidence).replace(/_/g, ' ')}.
    </p>
  );
}

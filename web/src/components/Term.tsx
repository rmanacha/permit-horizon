// A technical term with its plain-language definition from docs/GLOSSARY.md, opened in place.
import { useId, useState, type ReactNode } from 'react';
import { glossaryTerm } from '../content/glossary.ts';

export function Term({ term, children }: { term: string; children?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const g = glossaryTerm(term);
  if (!g) return <>{children}</>;
  return (
    <span className="term">
      <button
        type="button"
        className="term-button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        title={open ? 'Hide the definition' : 'Show the definition'}
      >
        {children ?? g.term}
      </button>
      {open && (
        <span id={id} className="term-def" role="note">
          <strong>{g.term}:</strong> {g.definition}
        </span>
      )}
    </span>
  );
}

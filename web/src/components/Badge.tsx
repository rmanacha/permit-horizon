// Status and exactness labels as design-system Tags. Each tag carries its words (color is never
// the only cue) and opens its glossary definition.
import { statusLabel } from '../lib/format.ts';
import type { Exactness } from '../engine/rescale.ts';
import { Tag, type TagProps } from './ds/Tag.tsx';
import { Term } from './Term.tsx';

const STATUS: Record<string, { tone: TagProps['tone']; term: string }> = {
  register_default: { tone: 'navy', term: 'register-default' },
  user_case: { tone: 'sky', term: 'user-case' },
  assumed_zero: { tone: 'sand', term: 'user-case' },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { tone: 'outline' as const, term: 'register-default' };
  return (
    <Tag tone={s.tone} size="sm">
      <Term term={s.term}>{statusLabel(status)}</Term>
    </Tag>
  );
}

const EXACT: Record<Exactness, { text: string; tone: TagProps['tone']; term: string }> = {
  unchanged: { text: 'register default', tone: 'navy', term: 'register-default' },
  exact: { text: 'exact', tone: 'lime', term: 'exact-rescale' },
  interpolated: { text: 'interpolated', tone: 'sunshine', term: 'interpolated' },
  not_available: { text: 'not computed in the browser', tone: 'coral', term: 'exact-rescale' },
};

export function ExactBadge({ exactness }: { exactness: Exactness }) {
  const e = EXACT[exactness];
  return (
    <Tag tone={e.tone} size="sm">
      <Term term={e.term}>{e.text}</Term>
    </Tag>
  );
}

export function ReviewBadge({ text }: { text: string }) {
  return (
    <Tag tone="outline" size="sm">
      <Term term="human-review">{text}</Term>
    </Tag>
  );
}

export function PlainTag({ children, tone = 'sand' }: { children: string; tone?: TagProps['tone'] }) {
  return (
    <Tag tone={tone} size="sm">
      {children}
    </Tag>
  );
}

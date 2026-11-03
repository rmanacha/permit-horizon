import { statusLabel } from '../lib/format.ts';
import type { Exactness } from '../engine/rescale.ts';
import { Term } from './Term.tsx';

const STATUS_TERM: Record<string, string> = {
  register_default: 'register-default',
  user_case: 'user-case',
  assumed_zero: 'user-case',
};

export function StatusBadge({ status }: { status: string }) {
  const cls = status === 'register_default' ? 'badge-default' : status === 'user_case' ? 'badge-user' : 'badge-zero';
  return (
    <span className={`badge ${cls}`}>
      <Term term={STATUS_TERM[status] ?? 'register-default'}>{statusLabel(status)}</Term>
    </span>
  );
}

const EXACT_TEXT: Record<Exactness, string> = {
  unchanged: 'register default',
  exact: 'exact',
  interpolated: 'interpolated',
  not_available: 'not computed in the browser',
};

export function ExactBadge({ exactness }: { exactness: Exactness }) {
  const cls = {
    unchanged: 'badge-default',
    exact: 'badge-exact',
    interpolated: 'badge-interp',
    not_available: 'badge-na',
  }[exactness];
  const term = exactness === 'interpolated' ? 'interpolated' : 'exact-rescale';
  return (
    <span className={`badge ${cls}`}>
      <Term term={term}>{EXACT_TEXT[exactness]}</Term>
    </span>
  );
}

export function ReviewBadge({ text }: { text: string }) {
  return (
    <span className="badge badge-review">
      <Term term="human-review">{text}</Term>
    </span>
  );
}

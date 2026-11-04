// Controls for the view: the case (share and delay), and one assumption's level or value.
import { useId, useState } from 'react';
import { useView } from '../app/context.tsx';
import { DELAYS, SHARES, encodeCase, type CaseSel, type Choice } from '../lib/route.ts';
import type { Level, RegisterEntry } from '../types/results.ts';
import { Term } from './Term.tsx';
import { Button } from './ds/Button.tsx';
import { Input } from './ds/Input.tsx';
import { Select } from './ds/Select.tsx';

type CaseOption = { key: string; label: string; sel: CaseSel };

const CASE_OPTIONS: CaseOption[] = [
  { key: 'register_default', label: 'Register default (from current law)', sel: { kind: 'register_default' } },
  ...SHARES.flatMap((share) =>
    DELAYS.map((delay) => ({
      key: `${share}-${delay}`,
      label: `${share}% newly affected, ${delay === 0 ? 'starting at once' : `after a ${delay}-year delay`}`,
      sel: { kind: 'eligible', share, delay } as CaseSel,
    })),
  ),
  { key: 'after', label: 'Starts after the five years (zero)', sel: { kind: 'after_horizon' } },
  { key: 'none', label: 'No change to current policy (zero)', sel: { kind: 'no_change' } },
];

export function CaseControl() {
  const { view, update } = useView();
  return (
    <div className="case-control">
      <Select
        label="Case: how much of each reform is new, and when it starts"
        value={encodeCase(view.caseSel) ?? 'register_default'}
        options={CASE_OPTIONS.map((o) => ({ value: o.key, label: o.label }))}
        onChange={(e) => update({ caseSel: CASE_OPTIONS.find((o) => o.key === e.target.value)?.sel ?? { kind: 'register_default' } })}
      />
      <p className="small muted">
        <Term term="register-default">What is a case?</Term>
      </p>
    </div>
  );
}

function levelText(e: RegisterEntry, lv: Level): string {
  const t = e.levels?.[lv];
  if (t) return t;
  const v = e[lv];
  return Array.isArray(v) ? v.join(' / ') : String(v);
}

/** Low / middle / high for one register entry, plus a number box when any value is allowed. */
export function LevelControl({ entry, accepts }: { entry: RegisterEntry; accepts: 'exact' | 'interpolated' | 'levels_only' }) {
  const { view, update } = useView();
  const name = useId();
  const choice: Choice | undefined = view.settings[entry.id];
  const current: Level | null = choice === undefined ? 'mid' : 'level' in choice ? choice.level : null;
  const [draft, setDraft] = useState(choice && 'value' in choice ? String(choice.value) : '');
  const set = (c: Choice | null) => {
    const next = { ...view.settings };
    if (c === null || ('level' in c && c.level === 'mid')) delete next[entry.id];
    else next[entry.id] = c;
    update({ settings: next });
  };
  const fixed = ['low', 'mid', 'high'].every((lv) => JSON.stringify(entry[lv as Level]) === JSON.stringify(entry.mid));
  return (
    <fieldset className="level-control">
      <legend className="sr-only">{entry.label}</legend>
      {!fixed && (
        <div className="segmented" role="radiogroup" aria-label={`${entry.label}: assumption level`}>
          {(['low', 'mid', 'high'] as Level[]).map((lv) => (
            <label key={lv} className={current === lv ? 'segment segment-on' : 'segment'}>
              <input
                type="radio"
                name={name}
                value={lv}
                aria-label={`${entry.label}: ${lv === 'mid' ? 'middle' : lv}, ${levelText(entry, lv)}`}
                checked={current === lv}
                onChange={() => set({ level: lv })}
              />
              <span className="segment-level">{lv === 'mid' ? 'middle' : lv}</span>
              <span className="segment-text">{levelText(entry, lv)}</span>
            </label>
          ))}
        </div>
      )}
      {fixed && <p className="small muted">Fixed at {levelText(entry, 'mid')} (no low or high in the register).</p>}
      {accepts !== 'levels_only' && typeof entry.mid === 'number' && (
        <form
          className="value-form"
          onSubmit={(e) => {
            e.preventDefault();
            const n = Number(draft);
            if (draft.trim() !== '' && Number.isFinite(n)) set({ value: n });
          }}
        >
          <Input
            label={`Or type a value${accepts === 'interpolated' ? ' (between low and high)' : ''}`}
            helper={entry.unit}
            type="number"
            step="any"
            inputMode="decimal"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <Button type="submit" variant="outline" size="sm">
            Use this value
          </Button>
          {choice && 'value' in choice && (
            <Button variant="ghost" size="sm" onClick={() => { setDraft(''); set(null); }}>
              Clear
            </Button>
          )}
        </form>
      )}
    </fieldset>
  );
}

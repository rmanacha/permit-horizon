import { useMemo, useState } from 'react';
import { useShared, useView } from '../app/context.tsx';
import { NeedState, StateResults } from '../components/StateResults.tsx';
import { LevelControl } from '../components/Controls.tsx';
import { GRADE_TEXT, SourceList } from '../components/Sources.tsx';
import { Num } from '../components/Num.tsx';
import { Term } from '../components/Term.tsx';
import { acceptsValue, relevantIds } from '../engine/rescale.ts';
import { fmtCount, fmtShare } from '../lib/format.ts';
import { SHORT } from '../lib/names.ts';
import { EXCLUDED_PARCELS } from '../content/site.ts';
import { SCENARIOS, type RegisterEntry, type Results, type ScenarioName } from '../types/results.ts';

function levelsText(e: RegisterEntry): string {
  const t = (lv: 'low' | 'mid' | 'high') => e.levels?.[lv] ?? (Array.isArray(e[lv]) ? (e[lv] as number[]).join('/') : String(e[lv]));
  return `${t('low')} / ${t('mid')} / ${t('high')}`;
}

function Register({ r }: { r: Results }) {
  const { registers } = useShared();
  const { view, update } = useView();
  const [filter, setFilter] = useState<'all' | ScenarioName | 'baseline'>('all');
  const accepts = useMemo(() => {
    const m = new Map<string, 'exact' | 'interpolated' | 'levels_only'>();
    const rank = { exact: 0, interpolated: 1, levels_only: 2 } as const;
    for (const n of SCENARIOS) {
      const s = r.scenarios[n];
      for (const id of relevantIds(s)) {
        const a = acceptsValue(s, id);
        const prev = m.get(id);
        if (!prev || rank[a] > rank[prev]) m.set(id, a);
      }
    }
    return m;
  }, [r]);
  const rows = registers.assumptions.filter((e) => {
    if (filter === 'all') return true;
    if (filter === 'baseline') return e.scenarios.includes('baseline') || e.scope === 'global';
    return e.scenarios.includes(filter) || e.scenarios.includes('all');
  });
  const changed = Object.keys(view.settings).length;
  return (
    <section aria-labelledby="reg-h">
      <h2 id="reg-h">
        The assumption <Term term="register">register</Term>
      </h2>
      <p className="small muted">
        Every assumption the model uses: {registers.assumptions.length} entries, each with its low, middle and high values, source,{' '}
        <Term term="locator">locator</Term>, arithmetic and <Term term="grade">grade</Term>. For the {accepts.size} that move a
        result in {r.meta.state}, choose a level; the choice applies on every page.{' '}
        {changed > 0 && (
          <button type="button" className="link-button" onClick={() => update({ settings: {} })}>
            Reset all {changed} to the register
          </button>
        )}
      </p>
      <label className="filter">
        Show{' '}
        <select value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
          <option value="all">all assumptions</option>
          <option value="baseline">the baseline and global rules</option>
          {SCENARIOS.map((n) => (
            <option key={n} value={n}>
              {SHORT[n]}
            </option>
          ))}
        </select>
      </label>
      <div className="table-wrap">
        <table className="data-table register-table">
          <thead>
            <tr>
              <th scope="col">Assumption</th>
              <th scope="col">Low / middle / high</th>
              <th scope="col">Grade and confidence</th>
              <th scope="col">Source and locator</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => {
              const acc = accepts.get(e.id);
              return (
                <tr key={e.id}>
                  <th scope="row">
                    {e.label}
                    <div className="small muted">
                      <code>{e.id}</code>; {e.unit}; used in {e.scenarios.join(', ')}
                    </div>
                  </th>
                  <td>
                    {acc ? <LevelControl entry={e} accepts={acc} /> : <span>{levelsText(e)}</span>}
                  </td>
                  <td className="small">
                    {GRADE_TEXT[e.grade] ?? e.grade}; {String(e.confidence).replace(/_/g, ' ')}
                  </td>
                  <td>
                    <SourceList sources={e.sources} />
                    <details className="details">
                      <summary>Arithmetic</summary>
                      <p>{e.citation}</p>
                      <p>{e.rationale}</p>
                    </details>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Sources({ r }: { r: Results }) {
  const { registers } = useShared();
  const st = r.meta.state;
  const mine = registers.sources.filter((s) => !s.only_for || s.only_for.includes(st));
  const used = mine.filter((s) => s.in_model);
  const excluded = mine.filter((s) => !s.in_model);
  return (
    <section aria-labelledby="src-h">
      <h2 id="src-h">Data sources used for {st}</h2>
      <p className="small muted">
        Every dataset behind {st}'s numbers, with its <Term term="vintage">vintage</Term>, licence and access date, from the
        download manifests committed in the repository (<code>data/manifests/</code>).
      </p>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Vintage used</th>
              <th scope="col">Licence or terms</th>
              <th scope="col">Accessed</th>
              <th scope="col">Where it comes from</th>
            </tr>
          </thead>
          <tbody>
            {used.map((s) => (
              <tr key={s.id}>
                <th scope="row">
                  {s.title}
                  {s.only_for && <div className="small muted">Used only for {s.only_for.join(', ')}.</div>}
                  {s.notes && <div className="small muted">{s.notes}</div>}
                </th>
                <td className="small">{(s.vintage_key && r.meta.vintages[s.vintage_key]) || s.vintages.join('; ')}</td>
                <td className="small">{s.license}</td>
                <td className="small">{s.accessed ? (s.accessed[0] === s.accessed[1] ? s.accessed[0] : `${s.accessed[0]} to ${s.accessed[1]}`) : ''}</td>
                <td className="small">
                  <ul className="plain-list">
                    {s.where.map((w) => (
                      <li key={w}>
                        <a href={w} target="_blank" rel="noreferrer">
                          {w.replace(/^https:\/\//, '')}
                        </a>
                      </li>
                    ))}
                  </ul>
                  {s.files} file{s.files === 1 ? '' : 's'}; <code>{s.manifest}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3>Parcel data</h3>
      <p>{EXCLUDED_PARCELS}</p>
      <h3>Downloaded, checked and left out</h3>
      <ul>
        {excluded.map((s) => (
          <li key={s.id}>
            <strong>{s.title}</strong>: {s.why_not}
          </li>
        ))}
      </ul>
    </section>
  );
}

function CrossCheck({ r }: { r: Results }) {
  const p = r.cross_check.housing_units_pep;
  const endKey = `july_${p.end_year}`;
  return (
    <section aria-labelledby="pep-full-h">
      <h2 id="pep-full-h">
        <Term term="pep">{p.label}</Term>
      </h2>
      {p.narrative.map((t) => (
        <p key={t}>{t}</p>
      ))}
      <p className="small muted">
        {p.measure}. Source: {p.source}. Outcome: homes added to the stock; never added to the permit baseline.
      </p>
      {p.state && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">County</th>
                <th scope="col" className="num-col">April 2020, homes</th>
                <th scope="col" className="num-col">July {p.end_year}, homes</th>
                <th scope="col" className="num-col">Net change, homes added to the stock</th>
                <th scope="col" className="num-col">Change</th>
              </tr>
            </thead>
            <tbody>
              {p.county.map((c) => (
                <tr key={c.fips}>
                  <th scope="row">{c.name}</th>
                  <td className="num-col">{fmtCount(c.april_2020)}</td>
                  <td className="num-col">{fmtCount(Number(c[endKey]))}</td>
                  <td className="num-col">{fmtCount(c.net_change)}</td>
                  <td className="num-col">{fmtShare(c.change_share)}</td>
                </tr>
              ))}
              <tr className="total-row">
                <th scope="row">State</th>
                <td className="num-col">{fmtCount(p.state.april_2020)}</td>
                <td className="num-col">{fmtCount(p.state.end)}</td>
                <td className="num-col">{fmtCount(p.state.net_change)}</td>
                <td className="num-col">{fmtShare(p.state.change_share)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
      {p.notes.map((t) => (
        <p key={t} className="small">
          {t}
        </p>
      ))}
    </section>
  );
}

function DataBody({ r }: { r: Results }) {
  const { index } = useShared();
  const name = index.states.find((s) => s.state === r.meta.state)?.name ?? r.meta.state;
  return (
    <>
      <h1>{name}: assumptions and data</h1>
      <p className="lead">
        What the model assumes, where every input comes from, and what was left out. Build{' '}
        <Term term="build-id">
          <code>{r.meta.build_id}</code>
        </Term>
        ; input file fingerprint <code>{r.meta.input_sha256.slice(0, 12)}</code>; run {r.meta.run_date}.
      </p>
      <p>
        Baseline for comparison: <Num value={r.baseline.state.mid} outcome="permits" /> over 2026-2030.
      </p>
      <Register r={r} />
      <Sources r={r} />
      <CrossCheck r={r} />
    </>
  );
}

export function DataPage() {
  const { view } = useView();
  if (!view.state) return <NeedState what="its assumptions and data sources" />;
  return <StateResults state={view.state}>{(r) => <DataBody r={r} />}</StateResults>;
}

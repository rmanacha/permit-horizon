import { useShared, useView } from '../app/context.tsx';
import { StateResults } from '../components/StateResults.tsx';
import { Num } from '../components/Num.tsx';
import { Term } from '../components/Term.tsx';
import { doc } from '../content/site.ts';
import { fmtCount, fmtShare, joinWords } from '../lib/format.ts';
import { Tag, type TagProps } from '../components/ds/Tag.tsx';
import type { LedgerEntry, Results } from '../types/results.ts';

function Backtest({ r }: { r: Results }) {
  const b = r.baseline.band_rule;
  const rt = b.coverage_realtime;
  return (
    <section aria-labelledby="bt-h">
      <h2 id="bt-h">
        How the baseline range did on history (<Term term="backtest">backtest</Term>)
      </h2>
      <p>{b.reading}</p>
      <div className="table-wrap">
        <table className="data-table">
          <caption>
            <Term term="coverage-by-period">Coverage by period</Term>: five-year forecasts for the 50 states and DC, by the year the
            forecast was made
          </caption>
          <thead>
            <tr>
              <th scope="col">Forecasts made in</th>
              <th scope="col" className="num-col">Forecasts</th>
              <th scope="col" className="num-col">Actual inside the range (hits)</th>
              <th scope="col" className="num-col">Above the range</th>
              <th scope="col" className="num-col">Below the range</th>
              <th scope="col" className="num-col">Share inside</th>
            </tr>
          </thead>
          <tbody>
            {b.coverage_by_period.map((p) => (
              <tr key={p.origins.join('-')} className={p.share_inside < 0.7 ? 'warning-row' : undefined}>
                <th scope="row">
                  {p.origins[0]}-{p.origins[1]}
                </th>
                <td className="num-col">{fmtCount(p.runs)}</td>
                <td className="num-col">{fmtCount(p.inside)}</td>
                <td className="num-col">{fmtCount(p.above)}</td>
                <td className="num-col">{fmtCount(p.below)}</td>
                <td className="num-col">{fmtShare(p.share_inside)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p>
        <strong>
          <Term term="real-time-test">Real-time test</Term>:
        </strong>{' '}
        redrawing the range each year from {rt.origins[0]} to {rt.origins[1]} with only the years known then, the actual total fell
        inside in {fmtCount(rt.inside)} of {fmtCount(rt.runs)} forecasts ({fmtShare(rt.share_inside)}), and in under 5% of forecasts made
        in {joinWords(rt.origins_under_5pct.map(String))}.
      </p>
      <p>{b.reading_history}</p>
      <p className="small muted">
        The range is the point times {b.low_ratio} and {b.high_ratio}. {b.applied_to_counties} Evidence:{' '}
        <a href={doc('docs/evidence/baseline_backtest.md')}>baseline backtest</a>.
      </p>
    </section>
  );
}

function SwingBand({ r, name }: { r: Results; name: string }) {
  const a = r.baseline.alternative_band;
  return (
    <section aria-labelledby="alt-h" className="swing-section">
      <h2 id="alt-h">
        Another way to draw the range (<Term term="swing-band">20-year swing range</Term>)
      </h2>
      {!a.available ? (
        <p>{a.reason}</p>
      ) : (
        <>
          <p>
            For {name}: <Num value={a.mid ?? 0} outcome="permits" /> (permits in {a.point_years?.[0]}-{a.point_years?.[1]}), range{' '}
            {fmtCount(a.low ?? 0)} to {fmtCount(a.high ?? 0)} permits. Shown here, apart from the headline range, never as a second band
            on it.
          </p>
          {a.narrative?.map((t) => <p key={t}>{t}</p>)}
          <p className="small">
            <strong>How it is built:</strong> {a.how_built}
          </p>
          <p className="small">
            <strong>Why it is not the headline:</strong> {a.why_not_headline}
          </p>
          <p className="small muted">{a.credit}</p>
        </>
      )}
    </section>
  );
}

const RESULT: Record<LedgerEntry['result'], { text: string; tone: TagProps['tone'] }> = {
  hit: { text: 'hit', tone: 'lime' },
  miss: { text: 'miss', tone: 'coral' },
  pending: { text: 'pending', tone: 'sunshine' },
  not_a_test: { text: 'not a test', tone: 'outline' },
};

function Range({ e }: { e: LedgerEntry }) {
  const p = e.prediction;
  if (!p || (p.mid === null && (p.low === null || p.high === null))) return <span className="muted">none</span>;
  if (p.mid === null) return <>{fmtCount(p.low)} to {fmtCount(p.high)}</>;
  return (
    <>
      {fmtCount(p.low)} / <strong>{fmtCount(p.mid)}</strong> / {fmtCount(p.high)}
    </>
  );
}

function Ledger() {
  const { registers } = useShared();
  const l = registers.validation_ledger;
  const classes = l.classes ?? {};
  return (
    <section aria-labelledby="ledger-h" data-tour="ledger">
      <h2 id="ledger-h">
        The <Term term="validation-ledger">validation ledger</Term>: the model against real reforms
      </h2>
      {l.entries.length === 0 ? (
        <p>
          No entries yet. The ledger will list frozen checks of the scenarios against places that passed a reform, with each
          prediction written down before the outcome was looked at, and every hit and miss.
        </p>
      ) : (
        <>
          <p>
            Every check of the model, including the ones it failed. The <Term term="evidence-class">evidence class</Term> says how
            much each one proves: a <Term term="frozen-holdout">frozen holdout</Term> was predicted and hashed before its outcome was
            fetched; a calibration check is where a number came from, so it cannot also test it.
          </p>
          <div className="table-wrap">
            <table className="data-table">
              <caption>Checks, their predictions (low / middle / high) and what happened</caption>
              <thead>
                <tr>
                  <th scope="col">Check</th>
                  <th scope="col">Evidence class</th>
                  <th scope="col">Place and years</th>
                  <th scope="col">Outcome measured</th>
                  <th scope="col" className="num-col">Model, low / mid / high</th>
                  <th scope="col" className="num-col">Actual</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {l.entries.map((e) => (
                  <tr key={e.id}>
                    <th scope="row">{e.title}</th>
                    <td>{classes[e.evidence_class] ?? e.evidence_class.replace(/_/g, ' ')}</td>
                    <td>
                      {e.place}, {e.years}
                    </td>
                    <td>
                      {e.outcome} <span className="small muted">({e.unit})</span>
                    </td>
                    <td className="num-col">
                      <Range e={e} />
                    </td>
                    <td className="num-col">{e.actual_text ?? (typeof e.actual === 'number' ? fmtCount(e.actual) : 'not yet')}</td>
                    <td>
                      <Tag tone={RESULT[e.result].tone} size="sm">
                        {RESULT[e.result].text}
                      </Tag>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3>What each check shows, and what it does not</h3>
          {l.entries.map((e) => (
            <details key={e.id} className="ledger-detail">
              <summary>{e.title}</summary>
              <p>{e.result_text}</p>
              <p>
                <strong>Independence:</strong> {e.independence}
              </p>
              <p>
                <strong>Supports:</strong> {e.supports}
              </p>
              <p>
                <strong>Does not support:</strong> {e.does_not_support}
              </p>
              <p>
                <strong>Next check:</strong> {e.next_check}
              </p>
              {e.frozen && (
                <p className="small">
                  <strong>Frozen:</strong> protocol{' '}
                  {e.frozen.protocol.startsWith('validation/') ? <a href={doc(e.frozen.protocol)}>{e.frozen.protocol}</a> : e.frozen.protocol}, SHA-256{' '}
                  <code>{e.frozen.sha256.slice(0, 16)}…</code>
                  {e.frozen.commit ? `, recorded in commit ${e.frozen.commit.slice(0, 7)}` : ''}.
                </p>
              )}
              <p className="small">
                <strong>Source:</strong>{' '}
                <a href={e.source.url} target="_blank" rel="noreferrer">
                  {e.source.title}
                </a>
                {e.credit ? `. ${e.credit}` : ''}
              </p>
            </details>
          ))}
        </>
      )}
    </section>
  );
}

export function ValidationPage() {
  const { view } = useView();
  const { index } = useShared();
  const st = view.state ?? 'NH';
  const name = index.states.find((s) => s.state === st)?.name ?? st;
  return (
    <>
      <h1>Validation</h1>
      <p className="lead">How the baseline rule did on 35 years of permits, where it failed, and the checks of the reforms.</p>
      <StateResults state={st}>
        {(r) => (
          <>
            <Backtest r={r} />
            <SwingBand r={r} name={name} />
          </>
        )}
      </StateResults>
      {!view.state && <p className="small muted">Showing New Hampshire's swing range; choose a state at the top for its own.</p>}
      <Ledger />
    </>
  );
}

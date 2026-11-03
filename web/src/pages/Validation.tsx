import { useShared, useView } from '../app/context.tsx';
import { StateResults } from '../components/StateResults.tsx';
import { Num } from '../components/Num.tsx';
import { Term } from '../components/Term.tsx';
import { doc } from '../content/site.ts';
import { fmtCount, fmtShare, joinWords } from '../lib/format.ts';
import type { Results } from '../types/results.ts';

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
    <section aria-labelledby="alt-h" className="card note-card">
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

function Ledger() {
  const { registers } = useShared();
  const l = registers.validation_ledger;
  return (
    <section aria-labelledby="ledger-h">
      <h2 id="ledger-h">
        The <Term term="validation-ledger">validation ledger</Term>: the model against real reforms
      </h2>
      {l.entries.length === 0 ? (
        <p>
          No entries yet. The ledger will list frozen checks of the scenarios against places that passed a reform, with each
          prediction written down before the outcome was looked at, and every hit and miss.
        </p>
      ) : (
        <pre>{JSON.stringify(l.entries, null, 1)}</pre>
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

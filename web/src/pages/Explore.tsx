import { useMemo } from 'react';
import { useShared, useView } from '../app/context.tsx';
import { ScenarioCard } from '../components/ScenarioCard.tsx';
import { StateResults } from '../components/StateResults.tsx';
import { CaseControl } from '../components/Controls.tsx';
import { Num } from '../components/Num.tsx';
import { Term } from '../components/Term.tsx';
import { ChartTable } from '../components/Figure.tsx';
import { RangeChart } from '../components/charts.tsx';
import { ExactBadge, PlainTag, StatusBadge } from '../components/Badge.tsx';
import { Button } from '../components/ds/Button.tsx';
import { Checkbox } from '../components/ds/Checkbox.tsx';
import { StatCallout } from '../components/ds/StatCallout.tsx';
import { fmtCount, fmtShare } from '../lib/format.ts';
import { SHORT, stateName } from '../lib/names.ts';
import { rankIncrements, registerLookup, scenarioView, type ScenarioView } from '../lib/viewmodel.ts';
import { countyTable, saveFile, toCSV, viewTable } from '../lib/downloads.ts';
import { SCENARIOS, type Results, type ScenarioName } from '../types/results.ts';

function Landing() {
  const { index } = useShared();
  const { href } = useView();
  return (
    <>
      <h1>How would five state reforms change home building?</h1>
      <p className="lead">
        Permit Horizon estimates, for every state, how many more building permits five benchmark reforms would bring over
        2026-2030 compared with no change: accessory dwelling units, missing-middle housing, transit-oriented density, no
        parking minimums, and development fees cut in half. Every number comes with its unit, its range and the
        assumptions behind it.
      </p>
      <p>Choose a state at the top of the page, or pick one below.</p>
      <div className="table-wrap">
        <table className="data-table">
          <caption>
            Every state at the register default, middle estimates over 2026-2030 (all in <Term term="outcome-permits">permits</Term>)
          </caption>
          <thead>
            <tr>
              <th scope="col">State</th>
              <th scope="col" className="num-col">
                <Term term="baseline">Baseline</Term>, permits
              </th>
              <th scope="col" className="num-col">
                <Term term="combined">All five together</Term> (illustration), permits added
              </th>
              <th scope="col" className="num-col">Share of the baseline</th>
            </tr>
          </thead>
          <tbody>
            {index.states.map((s) => (
              <tr key={s.state}>
                <th scope="row">
                  <a href={href({ page: 'explore', state: s.state })}>{s.name}</a>
                </th>
                <td className="num-col">{fmtCount(s.baseline.mid)}</td>
                <td className="num-col">{s.combined ? fmtCount(s.combined.mid) : 'n/a'}</td>
                <td className="num-col muted">{s.combined ? fmtShare(s.combined.mid / s.baseline.mid) : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small muted">
        Shares read high in states that build slowly for their size, because the denominator is recent building. Compare
        states by permits first.
      </p>
    </>
  );
}

function BaselineCard({ r, name }: { r: Results; name: string }) {
  const { href } = useView();
  const b = r.baseline;
  const years = `${b.forecast_years[0]}-${b.forecast_years[b.forecast_years.length - 1]}`;
  return (
    <section aria-labelledby="baseline-h" className="baseline-block">
      <h2 id="baseline-h" className="sr-only">
        Baseline
      </h2>
      <div className="stat-grid">
        <StatCallout
          tone="navy"
          value={fmtCount(b.state.mid)}
          label={
            <>
              permits over {years} if nothing changes (the <Term term="baseline">baseline</Term>)
            </>
          }
          source={
            <>
              <Term term="band">Range from history</Term>: {fmtCount(b.state.low)} to {fmtCount(b.state.high)} permits.
            </>
          }
        />
        <CrossCheckPanel r={r} />
      </div>
      <p>{b.band_rule.reading}</p>
      <p className="small">{b.band_rule.reading_history}</p>
      <p className="small muted">
        {b.method} {name}'s own 20-year swing range is on the <a href={href({ page: 'validation' })}>Validation</a> page.
      </p>
    </section>
  );
}

function CrossCheckPanel({ r }: { r: Results }) {
  const p = r.cross_check.housing_units_pep;
  if (!p.available || !p.state) return null;
  return (
    <StatCallout
      tone="sand"
      value={`+${fmtCount(p.state.net_change)}`}
      label={
        <>
          homes added to the stock, April 2020 to July {p.end_year} (<Term term="pep">Census housing-unit estimates</Term>;{' '}
          {fmtShare(p.state.change_share)} of the 2020 stock)
        </>
      }
      source={<>Shown beside the forecast, never added to it. {p.caveat}</>}
    />
  );
}

function CompareTable({ r, views }: { r: Results; views: ScenarioView[] }) {
  const { order, flips } = rankIncrements(views.map((v) => ({ name: v.name, increment: v.increment })));
  const byName = new Map(views.map((v) => [v.name, v]));
  const anyAdjusted = views.some((v) => v.adjusted.exactness !== 'unchanged');
  const caseDefault = views.every((v) => v.caseKey === 'register_default');
  const combined = r.combined;
  return (
    <section aria-labelledby="compare-h">
      <h2 id="compare-h">Compare the reforms</h2>
      <p className="small muted">
        Ranked by the middle <Term term="increment">increment over current law</Term>. Every increment is in permits, so they
        can be ranked; benchmarks are in different units and are not ranked. Ranges are{' '}
        <Term term="assumption-set">assumption sets</Term>, not probabilities.
      </p>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Rank</th>
              <th scope="col">Reform</th>
              <th scope="col" className="num-col">Low, permits</th>
              <th scope="col" className="num-col">Middle, permits</th>
              <th scope="col" className="num-col">High, permits</th>
              {anyAdjusted && <th scope="col" className="num-col">With your assumptions, permits</th>}
              <th scope="col">Status</th>
              <th scope="col">Benchmark (own unit, not ranked)</th>
            </tr>
          </thead>
          <tbody>
            {order.map((name, i) => {
              const v = byName.get(name)!;
              return (
                <tr key={name}>
                  <td>{i + 1}</td>
                  <th scope="row">{SHORT[name]}</th>
                  <td className="num-col">{fmtCount(v.increment.low)}</td>
                  <td className="num-col">{fmtCount(v.increment.mid)}</td>
                  <td className="num-col">{fmtCount(v.increment.high)}</td>
                  {anyAdjusted && (
                    <td className="num-col">
                      {v.adjusted.exactness === 'unchanged' ? '' : v.adjusted.value === null ? 'command line' : fmtCount(v.adjusted.value)}{' '}
                      {v.adjusted.exactness !== 'unchanged' && <ExactBadge exactness={v.adjusted.exactness} />}
                    </td>
                  )}
                  <td>
                    <StatusBadge status={v.status} />
                  </td>
                  <td>
                    <Num value={v.benchmark.mid} outcome={v.benchmark.outcome} linked={false} />
                  </td>
                </tr>
              );
            })}
            {flips.length > 0 && (
              <tr className="warning-row">
                <td colSpan={anyAdjusted ? 8 : 7}>
                  <strong>Order changes between assumption sets:</strong>{' '}
                  {flips
                    .map((f) => `${SHORT[f.above]} ranks above ${SHORT[f.below]} at the middle but below it at the ${f.level} end`)
                    .join('; ')}
                  .
                </td>
              </tr>
            )}
            {combined && (
              <tr className="illustration-row">
                <td>–</td>
                <th scope="row">
                  <Term term="combined">{combined.label}</Term>
                </th>
                <td className="num-col">{fmtCount(combined.increment.estimate.low)}</td>
                <td className="num-col">{fmtCount(combined.increment.estimate.mid)}</td>
                <td className="num-col">{fmtCount(combined.increment.estimate.high)}</td>
                {anyAdjusted && <td className="num-col muted">not applied</td>}
                <td>
                  <PlainTag tone="lime">Illustration</PlainTag>
                </td>
                <td className="small">
                  Not ranked. {fmtCount(combined.overlap_removed.mid)} permits less than the sum of the five (
                  {fmtCount(combined.sum_of_parts.mid)}) at the middle, because overlaps are removed.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {combined && (
        <details className="details">
          <summary>Why the package is less than the sum, and its limits</summary>
          <ul>
            {combined.rules.map((t) => (
              <li key={t}>{t}</li>
            ))}
            {combined.limits.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
          {!caseDefault && <p className="small">The package is shown at the register default; the selected case is not applied to it.</p>}
        </details>
      )}
      <ChartTable
        title="Increment over current law by reform, permits over 2026-2030 (bars: middle; lines: low to high)"
        chart={
          <RangeChart
            rows={order.map((n) => ({ key: n, label: SHORT[n], ...byName.get(n)!.increment }))}
            unit="permits"
            ariaLabel={`Increment over current law by reform in permits: ${order
              .map((n) => `${SHORT[n]} ${fmtCount(byName.get(n)!.increment.mid)}`)
              .join(', ')}`}
          />
        }
        table={
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Reform</th>
                <th scope="col" className="num-col">Low</th>
                <th scope="col" className="num-col">Middle</th>
                <th scope="col" className="num-col">High</th>
                <th scope="col">Unit</th>
              </tr>
            </thead>
            <tbody>
              {order.map((n) => (
                <tr key={n}>
                  <th scope="row">{SHORT[n]}</th>
                  <td className="num-col">{fmtCount(byName.get(n)!.increment.low)}</td>
                  <td className="num-col">{fmtCount(byName.get(n)!.increment.mid)}</td>
                  <td className="num-col">{fmtCount(byName.get(n)!.increment.high)}</td>
                  <td>permits</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </section>
  );
}

function Downloads({ r, views }: { r: Results; views: ScenarioView[] }) {
  const { view, href } = useView();
  const st = r.meta.state;
  return (
    <section aria-labelledby="dl-h" className="no-print">
      <h2 id="dl-h">Downloads and sharing</h2>
      <ul className="button-list">
        <li>
          <Button variant="outline" size="sm" onClick={() => {
            const t = viewTable(r, views, view.settings);
            saveFile(`permit-horizon-${st}-view.csv`, toCSV(t.header, t.rows), 'text/csv');
          }}>
            This view (CSV)
          </Button>
        </li>
        <li>
          <Button variant="outline" size="sm" onClick={() => {
            const out = {
              state: st, build_id: r.meta.build_id, link: window.location.href, case: views[0]?.caseKey,
              your_assumptions: view.settings,
              baseline: r.baseline.state,
              scenarios: Object.fromEntries(views.map((v) => [v.name, {
                benchmark: { ...v.benchmark }, increment: v.increment, total: v.total, outcome: 'permits', status: v.status,
                with_your_assumptions: v.adjusted.exactness === 'unchanged' ? null : { mid: v.adjusted.value, how: v.adjusted.exactness },
              }])),
              combined: r.combined?.increment.estimate ?? null,
              no_llm: r.no_llm,
            };
            saveFile(`permit-horizon-${st}-view.json`, `${JSON.stringify(out, null, 1)}\n`, 'application/json');
          }}>
            This view (JSON)
          </Button>
        </li>
        <li>
          <Button variant="outline" size="sm" onClick={() => {
            const t = countyTable(r);
            saveFile(`permit-horizon-${st}-counties.csv`, toCSV(t.header, t.rows), 'text/csv');
          }}>
            County table (CSV, with outcome and caveats columns)
          </Button>
        </li>
        <li>
          <Button variant="primary" size="sm" href={href({ page: 'brief' })}>
            Printable one-page brief
          </Button>
        </li>
      </ul>
      <p className="small muted">
        The address bar holds this view (state, case, reforms shown and your assumptions), so copying the link shares it.
      </p>
    </section>
  );
}

function ShowFilter() {
  const { view, update } = useView();
  const toggle = (n: ScenarioName) => {
    const on = view.show.includes(n);
    const next = on ? view.show.filter((x) => x !== n) : SCENARIOS.filter((x) => x === n || view.show.includes(x));
    if (next.length) update({ show: next });
  };
  return (
    <fieldset className="show-filter">
      <legend className="ds-field__label">Reforms to show and compare</legend>
      {SCENARIOS.map((n) => (
        <Checkbox key={n} label={SHORT[n]} checked={view.show.includes(n)} onChange={() => toggle(n)} />
      ))}
    </fieldset>
  );
}

function ExploreState({ r }: { r: Results }) {
  const { registers, index } = useShared();
  const { view, update, href } = useView();
  const name = stateName(index, r.meta.state);
  const reg = useMemo(() => registerLookup(registers.assumptions), [registers]);
  const views = view.show.map((n) => scenarioView(r, n, reg, view.settings, view.caseSel));
  const nChanged = Object.keys(view.settings).length;
  return (
    <>
      <h1>{name}: building permits over 2026-2030</h1>
      <p className="lead">{r.baseline.narrative[0]}</p>
      <BaselineCard r={r} name={name} />
      <section aria-labelledby="reforms-h">
        <h2 id="reforms-h">Five reforms, three layers each</h2>
        <p className="small muted">
          Each reform shows the <Term term="benchmark">benchmark</Term> in the source's own unit, the{' '}
          <Term term="increment">increment over current law</Term> in permits, and the <Term term="total">total</Term>.
          Numbers with different units are never added.
        </p>
        <div className="controls-row no-print">
          <CaseControl />
          <ShowFilter />
        </div>
        {nChanged > 0 && (
          <p className="note">
            You changed {nChanged} assumption{nChanged > 1 ? 's' : ''} (on the{' '}
            <a href={href({ page: 'data' })}>Assumptions and data</a> or Scenario detail pages); cards show the result under
            "With your assumptions".{' '}
            <Button variant="ghost" size="sm" onClick={() => update({ settings: {} })}>
              Reset to the register
            </Button>
          </p>
        )}
        <div className="card-grid">
          {views.map((v) => (
            <ScenarioCard key={v.name} v={v} state={r.meta.state} stateName={name} />
          ))}
        </div>
      </section>
      <CompareTable r={r} views={views} />
      <Downloads r={r} views={views} />
    </>
  );
}

export function ExplorePage() {
  const { view } = useView();
  if (!view.state) return <Landing />;
  return <StateResults state={view.state}>{(r) => <ExploreState r={r} />}</StateResults>;
}


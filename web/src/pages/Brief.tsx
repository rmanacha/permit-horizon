// The printable one-page brief (Explore > Downloads): estimate, assumptions, sources, build id, date.
import { useMemo } from 'react';
import { useShared, useView } from '../app/context.tsx';
import { NeedState, StateResults } from '../components/StateResults.tsx';
import { cliCommand } from '../engine/rescale.ts';
import { fmtCount, fmtShare, outcomeLabel, statusLabel } from '../lib/format.ts';
import { SHORT } from '../lib/names.ts';
import { registerLookup, scenarioView } from '../lib/viewmodel.ts';
import { SITE_URL } from '../content/site.ts';
import { Button } from '../components/ds/Button.tsx';
import type { Results } from '../types/results.ts';

function BriefBody({ r }: { r: Results }) {
  const { registers, index, meta } = useShared();
  const { view, href } = useView();
  const reg = useMemo(() => registerLookup(registers.assumptions), [registers]);
  const name = index.states.find((s) => s.state === r.meta.state)?.name ?? r.meta.state;
  const views = view.show.map((n) => scenarioView(r, n, reg, view.settings, view.caseSel));
  const b = r.baseline;
  const changed = Object.keys(view.settings);
  const caseLabel = views[0]?.caseLabel ?? '';
  return (
    <article className="brief">
      <p className="no-print">
        <Button variant="primary" onClick={() => window.print()}>
          Print or save as PDF
        </Button>{' '}
        <a href={href({ page: 'explore' })}>Back to Explore</a>
      </p>
      <header>
        <h1>
          {name}: five housing reforms and building permits, {b.forecast_years[0]}-{b.forecast_years[b.forecast_years.length - 1]}
        </h1>
        <p className="small">
          Permit Horizon brief. Build <code>{r.meta.build_id}</code>, results run {r.meta.run_date}, bundle exported {meta.export_date}.
          Case: {caseLabel}.{changed.length > 0 && ` Changed assumptions: ${changed.join(', ')}.`}
        </p>
      </header>
      <h2>If nothing changes</h2>
      <p>
        <strong>{fmtCount(b.state.mid)} permits</strong> over five years (range {fmtCount(b.state.low)} to {fmtCount(b.state.high)} permits).{' '}
        {b.band_rule.reading}
      </p>
      <h2>What each reform adds over current law</h2>
      <table className="data-table brief-table">
        <thead>
          <tr>
            <th scope="col">Reform</th>
            <th scope="col" className="num-col">Low, permits</th>
            <th scope="col" className="num-col">Middle, permits</th>
            <th scope="col" className="num-col">High, permits</th>
            <th scope="col">Newly affected; status</th>
            <th scope="col">Benchmark, in its own unit</th>
          </tr>
        </thead>
        <tbody>
          {views.map((v) => (
            <tr key={v.name}>
              <th scope="row">{SHORT[v.name]}</th>
              <td className="num-col">{fmtCount(v.increment.low)}</td>
              <td className="num-col">
                {fmtCount(v.increment.mid)}
                {v.adjusted.exactness !== 'unchanged' && v.adjusted.value !== null && (
                  <span className="small"> (your assumptions: {fmtCount(v.adjusted.value)}, {v.adjusted.exactness})</span>
                )}
              </td>
              <td className="num-col">{fmtCount(v.increment.high)}</td>
              <td className="small">
                {fmtShare(v.share)}; {statusLabel(v.status)}
              </td>
              <td className="small">
                {fmtCount(v.benchmark.mid)} {outcomeLabel(v.benchmark.outcome)}
              </td>
            </tr>
          ))}
          {r.combined && (
            <tr className="illustration-row">
              <th scope="row">{r.combined.label}</th>
              <td className="num-col">{fmtCount(r.combined.increment.estimate.low)}</td>
              <td className="num-col">{fmtCount(r.combined.increment.estimate.mid)}</td>
              <td className="num-col">{fmtCount(r.combined.increment.estimate.high)}</td>
              <td className="small" colSpan={2}>
                Register default; overlaps removed, so less than the sum. Not a forecast of a package.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <p className="small">
        Low, middle and high are assumption sets, not probabilities. Increments are all in permits and can be compared; benchmarks are
        in different units and are not added.
      </p>
      <h2>Key assumptions</h2>
      <ul className="small">
        {views.map((v) => (
          <li key={v.name}>
            <strong>{SHORT[v.name]}:</strong> {v.lawNote}
            {v.mover && ` Moves most: ${v.mover.label} (${fmtCount(v.mover.at_low)} to ${fmtCount(v.mover.at_high)} permits).`}
          </li>
        ))}
        {changed.length > 0 && (
          <li>
            Exact run of your assumptions: <code>{cliCommand(r.meta.state, view.settings)}</code>
          </li>
        )}
      </ul>
      <h2>What this cannot tell you</h2>
      <p className="small">
        Which places will build; prices, rents or affordability; how likely each number is. {b.band_rule.reading_history}
      </p>
      <h2>Sources</h2>
      <p className="small">
        {Object.entries(r.meta.vintages)
          .filter(([k]) => k !== 'aclf')
          .map(([k, v]) => `${k}: ${v}`)
          .join('. ')}
        . Every assumption, source and locator: {SITE_URL} (Assumptions and data). {r.no_llm}
      </p>
    </article>
  );
}

export function BriefPage() {
  const { view } = useView();
  if (!view.state) return <NeedState what="a one-page brief" />;
  return <StateResults state={view.state}>{(r) => <BriefBody r={r} />}</StateResults>;
}

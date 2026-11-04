import { useMemo, type ReactElement } from 'react';
import { useShared, useView } from '../app/context.tsx';
import { NeedState, StateResults } from '../components/StateResults.tsx';
import { Num, RangeText } from '../components/Num.tsx';
import { Term } from '../components/Term.tsx';
import { PlainTag, ReviewBadge, StatusBadge } from '../components/Badge.tsx';
import { Button } from '../components/ds/Button.tsx';
import { Card } from '../components/ds/Card.tsx';
import { Tabs, tabId } from '../components/ds/Tabs.tsx';
import { AdjustedResult } from '../components/AdjustedResult.tsx';
import { LevelControl } from '../components/Controls.tsx';
import { ChartTable } from '../components/Figure.tsx';
import { TornadoChart, YearChart } from '../components/charts.tsx';
import { GradeLine, SourceList } from '../components/Sources.tsx';
import { acceptsValue, isMultiplicative, relevantIds } from '../engine/rescale.ts';
import { fmtCount, fmtNumber, fmtShare, outcomeLabel } from '../lib/format.ts';
import { SCENARIO_TERM, SHORT, stateName } from '../lib/names.ts';
import { DELAYS, SHARES, caseKey, type CaseSel } from '../lib/route.ts';
import { humanReviewText, registerLookup, scenarioView } from '../lib/viewmodel.ts';
import { SCENARIOS, type Results, type Scenario, type ScenarioName } from '../types/results.ts';

function ReformTabs() {
  const { view, update } = useView();
  return (
    <Tabs
      aria-label="Reforms"
      idPrefix="reform"
      tabs={SCENARIOS.map((n) => ({ value: n, label: SHORT[n] }))}
      value={view.scenario}
      onChange={(v) => update({ scenario: v as ScenarioName })}
    />
  );
}

function routeText(s: Scenario, id: string): string {
  if (isMultiplicative(s, id)) {
    const scoped = s.components.linear_counties?.[id];
    return scoped ? 'Multiplies the result in the counties it applies to: exact in the browser, any value.' : 'Multiplies the result: exact in the browser, any value.';
  }
  if (s.grid?.params.includes(id)) return 'Precomputed for every low, middle and high combination: exact at those levels, interpolated between them.';
  return 'Moves the result in a way that is not a simple multiple: low and high are exact (precomputed one at a time); other values need the command line.';
}

function Chain({ r, s }: { r: Results; s: Scenario }) {
  const { registers } = useShared();
  const byId = useMemo(() => new Map(registers.assumptions.map((e) => [e.id, e])), [registers]);
  const order = [...s.tornado.map((b) => b.id), ...relevantIds(s).filter((id) => !s.tornado.some((b) => b.id === id))];
  const exposure = s.factors.exposure;
  return (
    <section aria-labelledby="chain-h">
      <h2 id="chain-h">How the estimate is built</h2>
      <p>
        <code className="formula">{s.formula}</code>
      </p>
      {Array.isArray(exposure) && (
        <p>
          <strong>Exposure:</strong> {fmtCount(exposure.reduce((a, b) => a + b, 0))} {s.factors.exposure_label} across{' '}
          {exposure.filter((x) => x > 0).length} of {exposure.length} counties.
        </p>
      )}
      <p>
        <strong>Years:</strong> {r.baseline.horizon_years} ({r.baseline.forecast_years[0]}-
        {r.baseline.forecast_years[r.baseline.forecast_years.length - 1]}).{' '}
        <strong>Newly affected share at the register default:</strong> {fmtShare(s.increment.newly_affected_share)}.
      </p>
      <p className="small muted">
        Choose low, middle or high for any assumption below, largest effect first. The published low and high{' '}
        <Term term="assumption-set">assumption sets</Term> move only the ones marked "band". The result under "With your
        assumptions" says how it was computed; your choices apply on every page and are kept in the link.
      </p>
      <ol className="chain">
        {order.map((id) => {
          const e = byId.get(id);
          if (!e) return null;
          const band = s.band_ids.includes(id);
          return (
            <li key={id} className="chain-item">
              <h3 className="chain-title">
                {e.label} {band && <PlainTag tone="sky">band</PlainTag>}
              </h3>
              <p className="small">{e.description}</p>
              <LevelControl entry={e} accepts={acceptsValue(s, id)} />
              <p className="small muted">{routeText(s, id)}</p>
              <SourceList sources={e.sources} />
              <GradeLine e={e} />
              <details className="details">
                <summary>Arithmetic and rationale</summary>
                <p>{e.citation}</p>
                <p>{e.rationale}</p>
                {e.transferability && <p>Transferability: {e.transferability}</p>}
              </details>
            </li>
          );
        })}
      </ol>
      <p className="small muted">
        The conversion to permits: {s.increment.conversion.text}
      </p>
    </section>
  );
}

function Cases({ s }: { s: Scenario }) {
  const { view, update } = useView();
  const key = caseKey(view.caseSel);
  const sel = s.cases[key] ?? s.cases.register_default;
  const pick = (c: CaseSel) => update({ caseSel: c });
  const cell = (share: 25 | 50 | 100, delay: 0 | 1 | 2) => {
    const k = `eligible_${share}_delay_${delay}`;
    const on = key === k;
    return (
      <td key={k} className="num-col">
        <button type="button" className={on ? 'cell-button cell-on' : 'cell-button'} aria-pressed={on} onClick={() => pick({ kind: 'eligible', share, delay })}>
          {fmtCount(s.cases[k].estimate_permits.mid)}
        </button>
      </td>
    );
  };
  return (
    <section aria-labelledby="cases-h">
      <h2 id="cases-h">Cases: how much is new, and when it starts</h2>
      <p className="small muted">
        Middle increments in permits. The <Term term="register-default">register default</Term> takes the{' '}
        <Term term="newly-affected-share">newly affected share</Term> from current law; the others are{' '}
        <Term term="user-case">user cases</Term>. Choosing one applies it on every page.
      </p>
      <div className="table-wrap">
        <table className="data-table cases-table">
          <caption>Middle increment, permits over 2026-2030, by share newly affected and delay</caption>
          <thead>
            <tr>
              <th scope="col">Newly affected</th>
              {DELAYS.map((d) => (
                <th key={d} scope="col" className="num-col">
                  {d === 0 ? 'No delay' : `${d}-year delay`}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SHARES.map((sh) => (
              <tr key={sh}>
                <th scope="row">{sh}%</th>
                {DELAYS.map((d) => cell(sh, d))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="button-list">
        <li>
          <Button variant="outline" size="sm" aria-pressed={key === 'register_default'} onClick={() => pick({ kind: 'register_default' })}>
            Register default: {fmtCount(s.cases.register_default.estimate_permits.mid)} permits
          </Button>
        </li>
        <li>
          <Button variant="outline" size="sm" aria-pressed={key === 'after_horizon'} onClick={() => pick({ kind: 'after_horizon' })}>
            Starts after the five years: 0 permits
          </Button>
        </li>
        <li>
          <Button variant="outline" size="sm" aria-pressed={key === 'no_change'} onClick={() => pick({ kind: 'no_change' })}>
            No change to current policy: 0 permits
          </Button>
        </li>
      </ul>
      <Card tone="sand" eyebrow="Selected case" title={sel.label} titleAs="h3">
        <p>
          <StatusBadge status={sel.status} />
        </p>
        <p>
          <Num value={sel.estimate_permits.mid} outcome="permits" /> (<RangeText v={sel.estimate_permits} outcome="permits" />); in
          the source's unit <Num value={sel.estimate.mid} outcome={sel.outcome} linked={false} />.
        </p>
        <p className="small">What this case assumes:</p>
        <ul className="small">
          {sel.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </Card>
    </section>
  );
}

function Joint({ s }: { s: Scenario }) {
  return (
    <section aria-labelledby="joint-h">
      <h2 id="joint-h">
        <Term term="joint-case">Joint favorable and unfavorable cases</Term>
      </h2>
      <div className="two-col">
        {(['favorable', 'unfavorable'] as const).map((d) => {
          const j = s.joint[d];
          return (
            <Card key={d} eyebrow={d === 'favorable' ? 'Joint favorable' : 'Joint unfavorable'} title={`Every assumption at its ${d === 'favorable' ? 'most' : 'least'} favorable end`} titleAs="h3">
              <p className="headline-number">
                <Num value={j.value} outcome="permits" />
              </p>
              <p className="small">{j.reading}</p>
              <details className="details">
                <summary>The settings</summary>
                <ul>
                  {j.settings.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </details>
            </Card>
          );
        })}
      </div>
    </section>
  );
}

function Tornado({ s }: { s: Scenario }) {
  if (!s.tornado.length) return null;
  const note = (id: string) =>
    id === 'adu_permits_per_completion' ? 'unit conversion: more permits per ADU, not more homes' : undefined;
  return (
    <section aria-labelledby="tornado-h">
      <h2 id="tornado-h">
        Which assumption matters most (<Term term="tornado">tornado</Term>)
      </h2>
      <ChartTable
        title="Middle increment, permits over 2026-2030, with one assumption at a time at its low or high end"
        chart={
          <TornadoChart
            rows={s.tornado.map((b) => ({ key: b.id, label: b.label, atLow: b.at_low, atHigh: b.at_high, base: b.base, lowText: b.low_text, highText: b.high_text, note: note(b.id) }))}
            unit="permits"
            ariaLabel={`Tornado: ${s.tornado.map((b) => `${b.label} ${fmtCount(b.at_low)} to ${fmtCount(b.at_high)} permits`).join('; ')}`}
          />
        }
        table={
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Assumption</th>
                <th scope="col">Low value</th>
                <th scope="col" className="num-col">At low, permits</th>
                <th scope="col">High value</th>
                <th scope="col" className="num-col">At high, permits</th>
                <th scope="col" className="num-col">Swing, permits</th>
              </tr>
            </thead>
            <tbody>
              {s.tornado.map((b) => (
                <tr key={b.id}>
                  <th scope="row">
                    {b.label}
                    {note(b.id) && <span className="small muted"> ({note(b.id)})</span>}
                  </th>
                  <td>{b.low_text}</td>
                  <td className="num-col">{fmtCount(b.at_low)}</td>
                  <td>{b.high_text}</td>
                  <td className="num-col">{fmtCount(b.at_high)}</td>
                  <td className="num-col">{fmtCount(b.swing)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
    </section>
  );
}

function CurrentLaw({ state, name, s }: { state: string; name: ScenarioName; s: Scenario }) {
  const { registers } = useShared();
  const law = registers.current_law[state]?.scenarios?.[name];
  const review = humanReviewText(s.increment.current_law.human_review);
  return (
    <section aria-labelledby="law-h">
      <h2 id="law-h">
        What the law already allows (<Term term="current-law">current-law register</Term>)
      </h2>
      {!law ? (
        <p>{registers.current_law_default}</p>
      ) : (
        <Card eyebrow="Statute on file" title={law.record.law} titleAs="h3">
          <p>{review && <ReviewBadge text={review} />}</p>
          <p>{law.record.summary}</p>
          <blockquote className="quote-block">
            “{law.record.quote}” (<a href={law.record.url} target="_blank" rel="noreferrer">statute</a>, accessed {law.record.accessed})
          </blockquote>
          <p className="small">In effect: {law.record.in_effect}</p>
          <div className="table-wrap">
            <table className="data-table">
              <caption>Benchmark features compared with this state's law</caption>
              <thead>
                <tr>
                  <th scope="col">Benchmark requirement</th>
                  <th scope="col">What the law says</th>
                  <th scope="col">Status</th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {law.features.map((f) => (
                  <tr key={f.id}>
                    <td>{f.challenge_requirement}</td>
                    <td>
                      {f.observed_position}
                      {f.limitations?.length ? <span className="small muted"> Limits: {f.limitations.join(' ')}</span> : null}
                    </td>
                    <td>{f.status.replace(/_/g, ' ')}</td>
                    <td>
                      <SourceList sources={f.sources} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            <Term term="current-strength">Current strength</Term> {fmtNumber(law.current_strength)}, so{' '}
            {fmtShare(1 - law.current_strength)} is newly affected. {law.strength_rationale}
          </p>
        </Card>
      )}
    </section>
  );
}

function num(x: unknown): number | null {
  return typeof x === 'number' ? x : null;
}

function Diagnostics({ r, s, name }: { r: Results; s: Scenario; name: ScenarioName }) {
  const d = s.diagnostics as Record<string, Record<string, unknown>>;
  const geo = s.factors.geography_check;
  const names = new Map(s.increment.by_county.map((c) => [c.fips, c.name]));
  const items: ReactElement[] = [];
  if ((name === 'parking' || name === 'fees') && geo) {
    items.push(
      <div key="geo">
        <h3>
          <Term term="geography-check">Geography check</Term>: builder response by county
        </h3>
        <p>
          The headline uses the measured builder response, {fmtNumber(num(s.factors.response) ?? 0)}% more homes per 1% cost cut,
          everywhere. Beside it, a composite built from how easily each metro's housing supply grows. The composite is a check, not
          the headline: it applies elasticities measured on the whole housing stock over decades to five years of new building
          (stock versus flow), and it cannot reach the measured low end of zero.
        </p>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">County</th>
                <th scope="col" className="num-col">Composite, % per 1%</th>
                <th scope="col" className="num-col">Measured (headline), % per 1%</th>
              </tr>
            </thead>
            <tbody>
              {geo.composite_per_county.map((v, i) => (
                <tr key={s.components.by_county[i]?.fips ?? i}>
                  <th scope="row">{names.get(s.components.by_county[i]?.fips) ?? s.components.by_county[i]?.fips}</th>
                  <td className="num-col">{fmtNumber(v, 2)}</td>
                  <td className="num-col">{fmtNumber(num(s.factors.response) ?? 0, 2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>,
    );
  }
  if (name === 'missing_middle') {
    items.push(
      <ul key="mm">
        {Object.entries(d).map(([k, v]) => (
          <li key={k}>
            {k}:{' '}
            {num(v.five_year_units) !== null
              ? `rate ${fmtNumber(num(v.rate) ?? 0)} per lot a year gives ${fmtCount(num(v.five_year_units))} permitted units over five years`
              : `${fmtCount(num(v.exposure))} detached homes, ${fmtCount(num(v.five_year_benchmark))} net permits over five years`}
          </li>
        ))}
      </ul>,
    );
  }
  if (name === 'tod') {
    const b = d.boundary_rate_case;
    items.push(
      <ul key="tod">
        <li>{fmtCount(num(d.homes_within_half_mile as unknown))} homes within half a mile of a major stop; {fmtCount(num(d.homes_within_quarter_mile as unknown))} within a quarter mile.</li>
        {b && (
          <li>
            Local boundary rate {fmtNumber(num(b.rate) ?? 0)}: {fmtCount(num(b.five_year_stock_change))} homes added to the stock over five
            years. {String(b.note ?? '')}
          </li>
        )}
      </ul>,
    );
  }
  if (name === 'fees') {
    const a = d.actual_fee_variant as { fee_cut?: number; permits?: { low: number; mid: number; high: number }; reading?: string } | undefined;
    const st = d.stock_route as { homes?: number; flow_route_mid?: number; ratio_to_flow?: number; reading?: string } | undefined;
    items.push(
      <ul key="fees">
        {a?.permits && (
          <li>
            Half of a typical actual fee (a ${fmtCount(a.fee_cut ?? 0)} cut): {fmtCount(a.permits.mid)} permits (range {fmtCount(a.permits.low)} to{' '}
            {fmtCount(a.permits.high)}). {a.reading}
          </li>
        )}
        {st && (
          <li>
            Stock route: {fmtCount(st.homes ?? 0)} homes, {fmtNumber(st.ratio_to_flow ?? 0, 2)} times the headline flow route. {st.reading}
          </li>
        )}
      </ul>,
    );
  }
  if (!items.length) return null;
  return (
    <section aria-labelledby="diag-h">
      <h2 id="diag-h">Diagnostics (outside every range)</h2>
      <p className="small muted">Shown for transparency; none of these enters the estimate for {r.meta.state}.</p>
      {items}
    </section>
  );
}

function ScenarioBody({ r, name }: { r: Results; name: ScenarioName }) {
  const { registers, index } = useShared();
  const { view } = useView();
  const reg = useMemo(() => registerLookup(registers.assumptions), [registers]);
  const s = r.scenarios[name];
  const v = scenarioView(r, name, reg, view.settings, view.caseSel);
  const stateLabel = stateName(index, r.meta.state);
  const cs = s.cases[v.caseKey] ?? s.cases.register_default;
  const byYear = v.caseKey === 'register_default' ? s.increment.by_year : cs.by_year;
  const conv = s.increment.conversion.factor;
  const years = s.increment.years;
  const yearsPermits =
    v.caseKey === 'register_default'
      ? byYear
      : { low: byYear.low.map((x) => x * conv.low), mid: byYear.mid.map((x) => x * conv.mid), high: byYear.high.map((x) => x * conv.high) };
  return (
    <>
      <h1>
        {stateLabel}: <Term term={SCENARIO_TERM[name]}>{s.label}</Term>
      </h1>
      <ul className="narrative">
        {s.narrative.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
      <section className="ds-card ds-card--white layers-card" aria-labelledby="layers-h">
        <div className="ds-card__content">
        <div className="ds-eyebrow">{cs.label}</div>
        <h2 id="layers-h" className="ds-card__title">Three layers</h2>
        <dl className="layers">
          <div className="layer">
            <dt>
              <Term term="benchmark">Benchmark</Term> ({outcomeLabel(s.benchmark.outcome)})
            </dt>
            <dd>
              <Num value={s.benchmark.mid} outcome={s.benchmark.outcome} /> (<RangeText v={s.benchmark} outcome={s.benchmark.outcome} />).{' '}
              <span className="small">{s.benchmark.interpretation}</span>
            </dd>
          </div>
          <div className="layer layer-main">
            <dt>
              <Term term="increment">Increment over current law</Term> <StatusBadge status={v.status} />
            </dt>
            <dd>
              <span className="headline-number">
                <Num value={v.increment.mid} outcome="permits" />
              </span>{' '}
              (<RangeText v={v.increment} outcome="permits" />)
              {name === 'adu' && (
                <span className="small">
                  {' '}
                  About <Num value={v.homes.mid} outcome="completed_homes" linked={false} /> (
                  <Term term="completed-homes-equivalent">completed-homes equivalent</Term>).
                </span>
              )}
            </dd>
          </div>
          <div className="layer">
            <dt>
              <Term term="total">Total</Term>
            </dt>
            <dd>
              <Num value={v.total.mid} outcome="permits" /> (<RangeText v={v.total} outcome="permits" />). {s.total.pairing_rule}
            </dd>
          </div>
        </dl>
        <AdjustedResult a={v.adjusted} state={r.meta.state} settings={view.settings} />
        </div>
      </section>
      <ChartTable
        title={`Increment by year, permits (${cs.label})`}
        chart={<YearChart years={years} low={yearsPermits.low} mid={yearsPermits.mid} high={yearsPermits.high} unit="permits" ariaLabel={`Increment by year in permits: ${years.map((y, i) => `${y} ${fmtCount(yearsPermits.mid[i])}`).join(', ')}`} />}
        table={
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Year</th>
                <th scope="col" className="num-col">Low, permits</th>
                <th scope="col" className="num-col">Middle, permits</th>
                <th scope="col" className="num-col">High, permits</th>
              </tr>
            </thead>
            <tbody>
              {years.map((y, i) => (
                <tr key={y}>
                  <th scope="row">{y}</th>
                  <td className="num-col">{fmtCount(yearsPermits.low[i])}</td>
                  <td className="num-col">{fmtCount(yearsPermits.mid[i])}</td>
                  <td className="num-col">{fmtCount(yearsPermits.high[i])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
      />
      <Chain r={r} s={s} />
      <Cases s={s} />
      <Joint s={s} />
      <Tornado s={s} />
      <CurrentLaw state={r.meta.state} name={name} s={s} />
      <Diagnostics r={r} s={s} name={name} />
      <section aria-labelledby="limits-h">
        <h2 id="limits-h">This reform's limits</h2>
        <ul>
          {s.limits.map((t) => (
            <li key={t}>{t}</li>
          ))}
          {s.notes.map((t) => (
            <li key={t}>{t}</li>
          ))}
        </ul>
      </section>
    </>
  );
}

export function ScenarioPage() {
  const { view } = useView();
  if (!view.state) return <NeedState what="each reform in detail" />;
  return (
    <>
      <ReformTabs />
      <div role="tabpanel" aria-labelledby={tabId('reform', view.scenario)}>
        <StateResults state={view.state}>{(r) => <ScenarioBody r={r} name={view.scenario} />}</StateResults>
      </div>
    </>
  );
}

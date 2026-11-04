// One reform for one state, in three layers, each number with its outcome label.
import { useView } from '../app/context.tsx';
import { fmtCount, fmtShare } from '../lib/format.ts';
import { SCENARIO_TERM, SHORT } from '../lib/names.ts';
import { Card } from './ds/Card.tsx';
import { lawLead, type ScenarioView } from '../lib/viewmodel.ts';
import { AdjustedResult } from './AdjustedResult.tsx';
import { ReviewBadge, StatusBadge } from './Badge.tsx';
import { Num, RangeText } from './Num.tsx';
import { Term } from './Term.tsx';

export function ScenarioCard({ v, state, stateName }: { v: ScenarioView; state: string; stateName: string }) {
  const { view, href } = useView();
  const delayText = v.delay === 0 ? 'starting at once' : `after a ${v.delay}-year delay`;
  const isAfter = v.caseKey === 'after_horizon';
  return (
    <Card
      className="scenario-card"
      labelId={`card-${v.name}`}
      eyebrow={SHORT[v.name]}
      title={<Term term={SCENARIO_TERM[v.name]}>{v.label}</Term>}
    >
      <dl className="layers">
        <div className="layer">
          <dt>
            <Term term="benchmark">Benchmark</Term>: what the source policy produced, moved to {stateName}
          </dt>
          <dd>
            <Num value={v.benchmark.mid} outcome={v.benchmark.outcome} />{' '}
            <span className="muted">
              (<RangeText v={v.benchmark} outcome={v.benchmark.outcome} />)
            </span>
          </dd>
        </div>
        <div className="layer layer-main">
          <dt>
            <Term term="increment">Increment over current law</Term> <StatusBadge status={v.status} />
          </dt>
          <dd>
            {v.zeroNote && v.increment.high === 0 ? (
              <p className="zero-note">{v.zeroNote}</p>
            ) : (
              <>
                <span className="headline-number">
                  <Num value={v.increment.mid} outcome="permits" />
                </span>{' '}
                <span className="muted">
                  (<RangeText v={v.increment} outcome="permits" />)
                </span>
                {v.name === 'adu' && (
                  <p className="small">
                    About <Num value={v.homes.mid} outcome="completed_homes" linked={false} /> (
                    <Term term="completed-homes-equivalent">completed-homes equivalent</Term>; range {fmtCount(v.homes.low)} to{' '}
                    {fmtCount(v.homes.high)}).
                  </p>
                )}
                <p className="small muted">
                  {fmtShare(v.shareOfBaseline)} of the baseline's middle estimate.{' '}
                  {isAfter
                    ? 'Assumes the reform starts after the five years.'
                    : v.caseKey === 'no_change'
                      ? 'Assumes no change to current policy.'
                      : <>Assumes <Term term="newly-affected-share">{fmtShare(v.share)} newly affected</Term>, {delayText}.</>}
                </p>
              </>
            )}
          </dd>
        </div>
        <div className="layer">
          <dt>
            <Term term="total">Total</Term> (baseline plus increment)
          </dt>
          <dd>
            <Num value={v.total.mid} outcome="permits" />{' '}
            <span className="muted">
              (<RangeText v={v.total} outcome="permits" />)
            </span>
          </dd>
        </div>
      </dl>
      <p className="law-note">
        <strong>
          <Term term="current-law">Current law</Term>:
        </strong>{' '}
        {lawLead(v.lawSource, v.lawStrength)}
        {v.lawNote}{' '}
        {v.humanReview && <ReviewBadge text={v.humanReview} />}
      </p>
      {v.mover && !(v.zeroNote && v.increment.high === 0) && (
        <p className="mover">
          <strong>
            The assumption that moves this result most (<Term term="tornado">tornado</Term>):
          </strong>{' '}
          {v.mover.label}. From {v.mover.low_text} to {v.mover.high_text}, the increment runs {fmtCount(v.mover.at_low)} to{' '}
          {fmtCount(v.mover.at_high)} permits.
        </p>
      )}
      <AdjustedResult a={v.adjusted} state={state} settings={view.settings} compact />
      <p className="card-link">
        <a href={href({ page: 'scenario', scenario: v.name })}>How this is computed, cases, the tornado and current law</a>
      </p>
    </Card>
  );
}

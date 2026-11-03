import { useShared, useView } from '../app/context.tsx';
import { StateResults } from '../components/StateResults.tsx';
import { Term } from '../components/Term.tsx';
import { GLOSSARY } from '../content/glossary.ts';
import limits from '../content/limits.json';
import { doc } from '../content/site.ts';
import { SHORT } from '../lib/names.ts';
import { SCENARIOS, type Results } from '../types/results.ts';

function Formulas({ r }: { r: Results }) {
  return (
    <section aria-labelledby="f-h">
      <h2 id="f-h">How each estimate is computed</h2>
      <p className="small muted">One line per estimate; the formulas are the same for every state, only the inputs differ.</p>
      <dl className="formula-list">
        <div>
          <dt>
            <Term term="baseline">Baseline</Term>
          </dt>
          <dd>
            <code className="formula">{r.baseline.method}</code>
          </dd>
        </div>
        {SCENARIOS.map((n) => (
          <div key={n}>
            <dt>{r.scenarios[n].label}</dt>
            <dd>
              <code className="formula">{r.scenarios[n].formula}</code>
              <p className="small">{r.scenarios[n].increment.conversion.text}</p>
            </dd>
          </div>
        ))}
      </dl>
      <p>
        Every scenario has three layers: the <Term term="benchmark">benchmark</Term> in the source's unit, the{' '}
        <Term term="increment">increment over current law</Term> in permits, and the <Term term="total">total</Term>. Low and high are{' '}
        <Term term="assumption-set">assumption sets</Term>; the <Term term="tornado">tornado</Term> moves one assumption at a time; the{' '}
        <Term term="joint-case">joint cases</Term> move all of them. Full methods: <a href={doc('docs/MODEL_AND_ASSUMPTIONS.md')}>model and assumptions overview</a>.
      </p>
    </section>
  );
}

function Rescale() {
  return (
    <section aria-labelledby="rescale-h">
      <h2 id="rescale-h">How this page changes an estimate without running the model</h2>
      <p>
        The model runs in Python ahead of time; this page only reads its results. When you change an assumption, the page
        recomputes the middle increment from numbers the model exported, in one of four ways, and says which:
      </p>
      <ol>
        <li>
          <strong>
            <Term term="exact-rescale">Exact</Term>, for assumptions that multiply the result
          </strong>{' '}
          (a conversion factor, a share, a cost per space, the builder response, the fee): each county's number is multiplied by the
          new value over the old one, the same arithmetic as the model. A test checks it against the model for New Hampshire, Utah and
          a demo state to one part in a billion.
        </li>
        <li>
          <strong>Exact, from a precomputed grid</strong>, for the parking and fee assumptions at low, middle or high in any
          combination: the model ran every combination in advance. A value between two levels is{' '}
          <Term term="interpolated">interpolated</Term> and labeled so.
        </li>
        <li>
          <strong>Exact, from the tornado</strong>, for any other single assumption at its low or high end: the model ran each one at
          a time in advance.
        </li>
        <li>
          <strong>Not computed in the browser</strong> for anything else. The page shows the command that runs it exactly, for
          example <code>uv run hre run --state UT --set builder_response_override=1.2</code>, from a copy of the repository (see About).
        </li>
      </ol>
    </section>
  );
}

function Limits({ r }: { r: Results }) {
  const { registers } = useShared();
  const lawStates = Object.keys(registers.current_law).sort();
  return (
    <section aria-labelledby="lim-h">
      <h2 id="lim-h">What this tool cannot tell you</h2>
      <ul className="limits-list">
        {limits.limits.map((l) => (
          <li key={l.title}>
            <strong>{l.title}.</strong> {l.text}
          </li>
        ))}
        {r.combined?.limits.map((t) => <li key={t}>{t}</li>)}
      </ul>
      <p className="small">
        States with a <Term term="current-law">current-law</Term> file in this version: {lawStates.join(', ') || 'none'}. Every other
        state and reform is treated as having no statewide law. Each reform's own limits are on its Scenario detail page.
      </p>
    </section>
  );
}

function Glossary() {
  const sections = [...new Set(GLOSSARY.map((t) => t.section))];
  return (
    <section aria-labelledby="g-h">
      <h2 id="g-h">Glossary</h2>
      {sections.map((sec) => (
        <div key={sec}>
          <h3>{sec}</h3>
          <dl className="glossary">
            {GLOSSARY.filter((t) => t.section === sec).map((t) => (
              <div key={t.id} id={`term-${t.id}`}>
                <dt>{t.term}</dt>
                <dd>{t.definition}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </section>
  );
}

export function MethodsPage() {
  const { view } = useView();
  const { meta } = useShared();
  return (
    <>
      <h1>Methods and limits</h1>
      <p className="note">
        <Term term="templates">{meta.no_llm}</Term>
      </p>
      <StateResults state={view.state ?? 'NH'}>
        {(r) => (
          <>
            <Formulas r={r} />
            <Rescale />
            <Limits r={r} />
          </>
        )}
      </StateResults>
      <Glossary />
      <p className="small muted">
        Reform names used on this site: {SCENARIOS.map((n) => SHORT[n]).join(', ')}.
      </p>
    </>
  );
}

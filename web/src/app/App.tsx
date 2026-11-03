import { useEffect } from 'react';
import { ViewProvider, SharedProvider, useShared, useView } from './context.tsx';
import type { Page } from '../lib/route.ts';
import { ExplorePage } from '../pages/Explore.tsx';
import { ScenarioPage } from '../pages/Scenario.tsx';
import { DataPage } from '../pages/Data.tsx';
import { MethodsPage } from '../pages/Methods.tsx';
import { ValidationPage } from '../pages/Validation.tsx';
import { AboutPage } from '../pages/About.tsx';
import { BriefPage } from '../pages/Brief.tsx';

const NAV: Array<{ page: Page; label: string }> = [
  { page: 'explore', label: 'Explore' },
  { page: 'scenario', label: 'Scenario detail' },
  { page: 'data', label: 'Assumptions and data' },
  { page: 'methods', label: 'Methods and limits' },
  { page: 'validation', label: 'Validation' },
  { page: 'about', label: 'About' },
];

const TITLES: Record<Page, string> = {
  explore: 'Explore',
  scenario: 'Scenario detail',
  data: 'Assumptions and data',
  methods: 'Methods and limits',
  validation: 'Validation',
  about: 'About',
  brief: 'One-page brief',
};

function StatePicker() {
  const { index } = useShared();
  const { view, update } = useView();
  return (
    <label className="state-picker">
      <span>State</span>
      <select
        value={view.state ?? ''}
        onChange={(e) => update({ state: e.target.value || null }, { push: true })}
      >
        <option value="">Choose a state…</option>
        {index.states.map((s) => (
          <option key={s.state} value={s.state}>
            {s.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function Shell() {
  const { view, href } = useView();
  const { index, meta } = useShared();
  const stateName = index.states.find((s) => s.state === view.state)?.name;
  useEffect(() => {
    document.title = `${TITLES[view.page]}${stateName ? `: ${stateName}` : ''} · Permit Horizon`;
  }, [view.page, stateName]);
  const page = (() => {
    switch (view.page) {
      case 'explore':
        return <ExplorePage />;
      case 'scenario':
        return <ScenarioPage />;
      case 'data':
        return <DataPage />;
      case 'methods':
        return <MethodsPage />;
      case 'validation':
        return <ValidationPage />;
      case 'about':
        return <AboutPage />;
      case 'brief':
        return <BriefPage />;
    }
  })();
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header no-print">
        <div className="site-header-inner">
          <div>
            <p className="site-title">
              <a href={href({ page: 'explore' })}>Permit Horizon</a>
            </p>
            <p className="site-tagline">A statewide housing reform estimator: building permits, 2026-2030</p>
          </div>
          <StatePicker />
          <nav className="site-nav" aria-label="Pages">
            <ul>
              {NAV.map((n) => (
                <li key={n.page}>
                  <a href={href({ page: n.page })} aria-current={view.page === n.page ? 'page' : undefined}>
                    {n.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        {page}
      </main>
      <footer className="site-footer no-print">
        <div className="site-footer-inner">
          <p>{meta.no_llm}</p>
          <p>
            Results bundle exported {meta.export_date} from commit <code>{meta.git_shas.map((s) => s.slice(0, 7)).join(', ')}</code>,
            results schema {meta.results_schema_version}, {meta.jurisdictions} jurisdictions. Open source under
            Apache-2.0.
          </p>
        </div>
      </footer>
    </>
  );
}

export function App() {
  return (
    <ViewProvider>
      <SharedProvider>
        <Shell />
      </SharedProvider>
    </ViewProvider>
  );
}

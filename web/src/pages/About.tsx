import { useShared, useView } from '../app/context.tsx';
import { StateResults } from '../components/StateResults.tsx';
import { CREDITS, DOCS, REPO_URL, SITE_URL, TEAM, TEAM_NOTE, doc } from '../content/site.ts';
import { Term } from '../components/Term.tsx';

export function AboutPage() {
  const { meta } = useShared();
  const { view } = useView();
  return (
    <>
      <h1>About Permit Horizon</h1>
      <p className="lead">
        A statewide housing reform estimator built for the Housing Data and Technology Innovation Challenge, for state legislators
        and their staff. It estimates how five benchmark reforms change building permits over 2026-2030 against a no-change baseline,
        for every state and DC, with the assumptions, sources and limits behind every number.
      </p>
      <h2>Team</h2>
      <ul>
        {TEAM.map((t) => (
          <li key={t.name}>
            {t.name}, {t.role}, {t.org}
          </li>
        ))}
      </ul>
      <p className="small">{TEAM_NOTE}</p>
      {CREDITS.map((c) => (
        <p key={c} className="small">
          {c}
        </p>
      ))}
      <h2>This build</h2>
      <ul>
        <li>
          Results bundle exported {meta.export_date} from commit <code>{meta.git_shas.join(', ')}</code> (
          <a href={`${REPO_URL}/commit/${meta.git_shas[0]}`}>view on GitHub</a>); {meta.jurisdictions} jurisdictions; results schema{' '}
          {meta.results_schema_version}; input schema {meta.input_schema_versions.join(', ')}.
        </li>
        <li>
          Register fingerprint <code>{meta.parameters_sha256.slice(0, 16)}</code>.
        </li>
      </ul>
      {view.state && (
        <StateResults state={view.state}>
          {(r) => (
            <p>
              {view.state}: <Term term="build-id">build id</Term> <code>{r.meta.build_id}</code>, run {r.meta.run_date}.
            </p>
          )}
        </StateResults>
      )}
      <div className="table-wrap">
        <table className="data-table">
          <caption>
            Data <Term term="vintage">vintages</Term> in this build
          </caption>
          <tbody>
            {Object.entries(meta.vintages).map(([k, v]) => (
              <tr key={k}>
                <th scope="row">
                  <code>{k}</code>
                </th>
                <td>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2>Run it yourself</h2>
      <p>From a copy of the repository, with <code>make</code>, <code>uv</code> and Node 22.18 or newer:</p>
      <pre>{`make setup   # the exact Python environment from uv.lock
make run     # build this website and serve it at http://localhost:8080
make test    # the automated tests (offline)`}</pre>
      <p>
        Without Node: <code>docker compose up</code> serves the same site at http://localhost:8080. Any assumption value the page does
        not compute runs exactly with <code>uv run hre run --state UT --set builder_response_override=1.2</code>. The public copy of
        this site: <a href={SITE_URL}>{SITE_URL}</a>.
      </p>
      <h2>Documents</h2>
      <ul>
        {DOCS.map((d) => (
          <li key={d.path}>
            <a href={doc(d.path)}>{d.label}</a>
          </li>
        ))}
        <li>
          <a href={REPO_URL}>Source code on GitHub</a>
        </li>
      </ul>
      <h2>Licence, AI use and privacy</h2>
      <p>
        The code is open source under Apache-2.0; each dataset keeps its own terms (Assumptions and data page). AI coding assistants
        helped write the code, and every function has tests; the <a href={doc('docs/DISCLOSURES.md')}>disclosures</a> list the tools. {meta.no_llm}
      </p>
      <p>This site is static: it sends nothing anywhere, sets no cookies and has no tracking. Downloads are built in your browser.</p>
    </>
  );
}

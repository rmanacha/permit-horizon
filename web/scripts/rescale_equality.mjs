// Equality test (Phase 4 step 6): the page's TypeScript rescale (src/engine/rescale.ts) against
// the engine itself. For each state it runs `hre run` once at the register default, applies
// three sets of multiplicative changes in TypeScript, then runs `hre run --set/--level` with the
// same changes and compares every scenario's middle increment to a relative 1e-9. A fourth set
// checks the lookup routes (tornado bar, grid cell), whose bundle values carry 4 decimals.
//
//   node scripts/rescale_equality.mjs            # NH, UT and the demo state ZZ
//   node scripts/rescale_equality.mjs AZ CT      # any states with data/processed/{ST}.json
//
// Real states need data/processed/{ST}.json (make data STATE=XX); without it a state is skipped
// with a message. ZZ is built from the committed fixtures, so CI always runs it.
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { adjust, cliCommand } from '../src/engine/rescale.ts';

const REPO = fileURLToPath(new URL('../../', import.meta.url));
const BUNDLE = join(REPO, 'web', 'public', 'results');
const states = process.argv.slice(2).length ? process.argv.slice(2) : ['NH', 'UT', 'ZZ'];
const register = Object.fromEntries(
  JSON.parse(readFileSync(join(BUNDLE, 'registers.json'), 'utf8')).assumptions.map((a) => [a.id, a]),
);

const EXACT_SETS = [
  {
    name: 'levels: ADU permits per completion, parking density factor and code penalty at their low ends',
    settings: {
      adu_permits_per_completion: { level: 'low' },
      parking_low_density_factor: { level: 'low' },
      mm_code_penalty: { level: 'low' },
    },
  },
  {
    name: 'typed values: fee cut 30%, TOD rate 0.0005, $60,000 a parking space, 75% single-family-only',
    settings: {
      fee_cut_share: { value: 0.3 },
      tod_rate_per_home: { value: 0.0005 },
      parking_cost_per_space: { value: 60000 },
      mm_sf_only_share: { value: 0.75 },
    },
  },
  {
    name: 'levels: builder response and ADU permits per completion at their high ends, fee $40,000',
    settings: {
      builder_response_override: { level: 'high' },
      adu_permits_per_completion: { level: 'high' },
      total_fee_per_unit: { value: 40000 },
    },
  },
];
const LOOKUP_SET = {
  name: 'lookups: ADU ramp high (tornado bar), parking share still built low (grid cell)',
  settings: { ramp_adu: { level: 'high' }, parking_built_share: { level: 'low' } },
};

function hre(st, out, settings = {}) {
  const args = ['run', 'hre', 'run', '--state', st, '--out', out, '--quiet'];
  if (st === 'ZZ') args.push('--data-dir', 'data/sample');
  for (const [id, ch] of Object.entries(settings)) {
    args.push(...('level' in ch ? ['--level', `${id}=${ch.level}`] : ['--set', `${id}=${ch.value}`]));
  }
  execFileSync('uv', args, { cwd: REPO, stdio: ['ignore', 'ignore', 'inherit'] });
  return JSON.parse(readFileSync(out, 'utf8'));
}

const rel = (a, b) => Math.abs(a - b) / Math.max(1e-12, Math.abs(b));
const tmp = mkdtempSync(join(tmpdir(), 'rescale-equality-'));
let failures = 0;
let compared = 0;
const ran = [];

try {
  for (const st of states) {
    if (st !== 'ZZ' && !existsSync(join(REPO, 'data', 'processed', `${st}.json`))) {
      console.log(`${st}: skipped (no data/processed/${st}.json here; run 'make data STATE=${st}')`);
      continue;
    }
    ran.push(st);
    const base = hre(st, join(tmp, `${st}.base.json`));
    if (existsSync(join(BUNDLE, `${st}.json`))) {
      const pub = JSON.parse(readFileSync(join(BUNDLE, `${st}.json`), 'utf8'));
      let worst = 0;
      for (const [name, s] of Object.entries(base.scenarios)) {
        worst = Math.max(worst, rel(pub.scenarios[name].components.increment_mid_permits, s.components.increment_mid_permits));
      }
      const ok = worst <= 1e-9;
      if (!ok) failures += 1;
      console.log(`${st}: the committed bundle's components equal a fresh run (worst relative difference ${worst.toExponential(1)}) ${ok ? 'ok' : 'FAIL'}`);
    }
    for (const set of [...EXACT_SETS, LOOKUP_SET]) {
      const exact = set !== LOOKUP_SET;
      const run = hre(st, join(tmp, `${st}.set.json`), set.settings);
      const rows = [];
      for (const [name, s] of Object.entries(base.scenarios)) {
        const a = adjust(s, register, set.settings);
        if (a.exactness === 'unchanged') continue;
        const want = run.scenarios[name].components.increment_mid_permits;
        const d = a.value === null ? Infinity : rel(a.value, want);
        const tol = exact ? 1e-9 : 1e-3;
        const ok = d <= tol || (a.value !== null && Math.abs(a.value - want) <= (exact ? 1e-9 : 5e-4));
        compared += 1;
        if (!ok || (exact && a.route !== 'multiplicative')) failures += 1;
        rows.push(`    ${name.padEnd(15)} page ${String(a.value?.toFixed(6)).padStart(14)}  engine ${want.toFixed(6).padStart(14)}  ` +
          `rel diff ${d.toExponential(1).padStart(8)}  ${a.route}${ok ? '' : '  FAIL'}`);
      }
      console.log(`${st}: ${set.name}\n    ${cliCommand(st, set.settings)}`);
      console.log(rows.join('\n'));
    }
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}

console.log(`\n${compared} comparisons in ${ran.join(', ') || 'no state'}: ${failures ? `${failures} FAILED` : 'all equal (multiplicative 1e-9, lookups 1e-3)'}`);
process.exit(failures || !ran.length ? 1 : 0);

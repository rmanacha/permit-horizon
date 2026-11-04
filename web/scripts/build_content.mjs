// Site text that is not a model result lives in Markdown under docs/ (readable on GitHub) and is
// turned into JSON the site imports:
//   docs/GLOSSARY.md        -> web/src/content/glossary.json   lines "- **Term** (`id`): definition"
//   docs/methods/limits.md  -> web/src/content/limits.json     lines "- **Title**: sentence"
//   web/src/content/tour.md -> web/src/content/tour.json       stops "## Title (`target`, page)" and their text
// `npm run content` writes the JSON; scripts/content.test.mjs fails when the JSON is out of date.
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const REPO = fileURLToPath(new URL('../../', import.meta.url));

export function parseGlossary(md) {
  const terms = [];
  let section = '';
  for (const line of md.split('\n')) {
    const h = /^## (.+)$/.exec(line);
    if (h) section = h[1].trim();
    const m = /^- \*\*(.+?)\*\* \(`([a-z0-9-]+)`\): (.+)$/.exec(line);
    if (m) terms.push({ id: m[2], term: m[1], definition: m[3].trim(), section });
    else if (/^- \*\*/.test(line)) throw new Error(`glossary line not in the "- **Term** (\`id\`): text" form: ${line}`);
  }
  const ids = new Set();
  for (const t of terms) {
    if (ids.has(t.id)) throw new Error(`duplicate glossary id ${t.id}`);
    ids.add(t.id);
  }
  return terms;
}

export function parseLimits(md) {
  const out = [];
  for (const line of md.split('\n')) {
    const m = /^- \*\*(.+?)\*\*: (.+)$/.exec(line);
    if (m) out.push({ title: m[1], text: m[2].trim() });
  }
  return out;
}

/** The tour's stops: a heading names the stop, its target element and its page; the lines under it are its text. */
export function parseTour(md) {
  const stops = [];
  for (const line of md.split('\n')) {
    const h = /^## (.+?) \(`([a-z-]+)`, ([a-z]+)\)$/.exec(line);
    if (h) stops.push({ title: h[1], target: h[2], page: h[3], text: '' });
    else if (/^## /.test(line)) throw new Error(`tour heading not in the "## Title (\`target\`, page)" form: ${line}`);
    else if (stops.length && line.trim()) stops[stops.length - 1].text += `${stops[stops.length - 1].text ? ' ' : ''}${line.trim()}`;
  }
  return stops;
}

export function render() {
  const glossary = parseGlossary(readFileSync(`${REPO}docs/GLOSSARY.md`, 'utf8'));
  const limits = parseLimits(readFileSync(`${REPO}docs/methods/limits.md`, 'utf8'));
  const tour = parseTour(readFileSync(`${REPO}web/src/content/tour.md`, 'utf8'));
  return {
    'web/src/content/glossary.json': `${JSON.stringify({ source: 'docs/GLOSSARY.md', terms: glossary }, null, 1)}\n`,
    'web/src/content/limits.json': `${JSON.stringify({ source: 'docs/methods/limits.md', limits }, null, 1)}\n`,
    'web/src/content/tour.json': `${JSON.stringify({ source: 'web/src/content/tour.md', stops: tour }, null, 1)}\n`,
  };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  for (const [path, text] of Object.entries(render())) {
    writeFileSync(`${REPO}${path}`, text);
    console.log(`wrote ${path}`);
  }
}

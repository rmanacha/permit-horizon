// The site tour: five stops on New Hampshire, each one element outlined and two or three sentences
// beside it. Its place is `tour=N` in the address bar (the share link #/explore?st=NH&tour=1 opens
// it); nothing is stored in the browser. The text comes from content/tour.md through tour.json.
import { useEffect, useRef, type ReactNode } from 'react';
import { useView } from '../app/context.tsx';
import tour from '../content/tour.json';
import { buildHash, DEFAULT_VIEW, type Page } from '../lib/route.ts';
import { Button } from './ds/Button.tsx';

const STOPS = tour.stops;
const START = buildHash({ ...DEFAULT_VIEW, state: 'NH', tour: 1 });

/** A Markdown link in a stop's text becomes a link; it carries no tour=, so following it closes the tour. */
function withLinks(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(/\[([^\]]+)\]\(([^)]+)\)/g)) {
    out.push(text.slice(last, m.index), <a key={m.index} href={m[2]}>{m[1]}</a>);
    last = m.index + m[0].length;
  }
  out.push(text.slice(last));
  return out;
}

export function TourStart() {
  return (
    <p className="tour-start no-print">
      <Button variant="brand" size="sm" href={START}>
        Take the tour
      </Button>
      <span className="small muted">Five stops on New Hampshire, about three minutes.</span>
    </p>
  );
}

export function Tour() {
  const { view, update } = useView();
  const n = view.tour;
  const stop = STOPS[n - 1];
  const panel = useRef<HTMLDivElement>(null);
  const close = () => {
    update({ tour: 0 });
    document.getElementById('main')?.focus({ preventScroll: true });
  };

  // Outline the stop's element and scroll to it, once it is on the page (a state's results load after the page does).
  useEffect(() => {
    if (!stop) return;
    let el: Element | null = null;
    const find = () => {
      const found = document.querySelector(`[data-tour="${stop.target}"]`);
      if (!found || found === el) return;
      el = found;
      el.classList.add('tour-target');
      el.scrollIntoView({ block: 'start' });
      watcher.disconnect();
    };
    const watcher = new MutationObserver(find);
    watcher.observe(document.body, { childList: true, subtree: true });
    find();
    return () => {
      watcher.disconnect();
      el?.classList.remove('tour-target');
    };
  }, [stop]);

  // Each stop takes focus, so screen readers read its title and text.
  useEffect(() => {
    if (stop) panel.current?.focus({ preventScroll: true });
  }, [stop]);

  // Escape closes the tour (registered each render, so `close` always sees the current view).
  useEffect(() => {
    if (!stop) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  });

  if (!stop) return null;
  const next = STOPS[n];
  return (
    <div className="tour-panel" role="dialog" aria-labelledby="tour-h" aria-describedby="tour-p" ref={panel} tabIndex={-1}>
      <p className="ds-eyebrow">
        Tour: stop {n} of {STOPS.length}
      </p>
      <h2 id="tour-h" className="tour-title">
        {stop.title}
      </h2>
      <p id="tour-p" className="tour-text">
        {withLinks(stop.text)}
      </p>
      <p className="button-list">
        {next && (
          <Button size="sm" onClick={() => update({ tour: n + 1, page: next.page as Page })}>
            Next
          </Button>
        )}
        <Button variant={next ? 'outline' : 'primary'} size="sm" onClick={close}>
          Done
        </Button>
        <span className="small muted">Esc closes.</span>
      </p>
    </div>
  );
}

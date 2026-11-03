// Community Solutions design system: Tabs (uppercase condensed labels, 4px sky rule under the
// active tab). className replaces style. Keyboard: Left/Right/Home/End move between tabs; the
// caller marks the content with role="tabpanel" and aria-labelledby={tabId(value)}.
import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react';

export interface TabItem {
  value: string;
  label: ReactNode;
}

export interface TabsProps {
  tabs: (string | TabItem)[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  /** dark = on navy/sky grounds */
  tone?: 'light' | 'dark';
  className?: string;
  'aria-label'?: string;
  idPrefix?: string;
}

export function tabId(prefix: string, value: string): string {
  return `${prefix}-tab-${value}`;
}

export function Tabs({ tabs, value, defaultValue, onChange, tone = 'light', className, idPrefix = 'tabs', ...aria }: TabsProps) {
  const items = tabs.map((t) => (typeof t === 'string' ? { value: t, label: t } : t));
  const [own, setOwn] = useState(defaultValue ?? items[0]?.value);
  const cur = value ?? own;
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const pick = (v: string) => {
    setOwn(v);
    onChange?.(v);
  };
  const onKey = (e: KeyboardEvent, i: number) => {
    const n = items.length;
    const next = e.key === 'ArrowRight' ? (i + 1) % n : e.key === 'ArrowLeft' ? (i - 1 + n) % n : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : -1;
    if (next < 0) return;
    e.preventDefault();
    refs.current[next]?.focus();
    pick(items[next].value);
  };
  return (
    <div role="tablist" className={['ds-tabs', `ds-tabs--${tone}`, className ?? ''].filter(Boolean).join(' ')} {...aria}>
      {items.map((t, i) => {
        const on = t.value === cur;
        return (
          <button
            key={t.value}
            ref={(el) => {
              refs.current[i] = el;
            }}
            id={tabId(idPrefix, t.value)}
            type="button"
            role="tab"
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            className={on ? 'ds-tab ds-tab--on' : 'ds-tab'}
            onClick={() => pick(t.value)}
            onKeyDown={(e) => onKey(e, i)}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

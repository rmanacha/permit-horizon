// Community Solutions design system: Checkbox and Radio (2px navy box, navy fill with a
// sunshine check). className replaces style; aria-label passes through.
import { useState, type ChangeEvent, type ReactNode } from 'react';

export interface CheckboxProps {
  label?: ReactNode;
  checked?: boolean;
  defaultChecked?: boolean;
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void;
  disabled?: boolean;
  /** Render as radio (prefer the Radio export) */
  radio?: boolean;
  name?: string;
  value?: string;
  className?: string;
  'aria-label'?: string;
}

export function Checkbox({ label, checked, defaultChecked = false, onChange, disabled = false, radio = false, name, value, className, ...aria }: CheckboxProps) {
  const [own, setOwn] = useState(defaultChecked);
  const on = checked ?? own;
  return (
    <label className={['ds-check', radio ? 'ds-check--radio' : '', disabled ? 'ds-check--disabled' : '', className ?? ''].filter(Boolean).join(' ')}>
      <input
        type={radio ? 'radio' : 'checkbox'}
        name={name}
        value={value}
        checked={on}
        disabled={disabled}
        onChange={(e) => {
          setOwn(e.target.checked);
          onChange?.(e);
        }}
        {...aria}
      />
      <span className={on ? 'ds-check__box ds-check__box--on' : 'ds-check__box'} aria-hidden="true">
        {on && !radio && (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        )}
        {on && radio && <span className="ds-check__dot" />}
      </span>
      {label && <span className="ds-check__label">{label}</span>}
    </label>
  );
}

export function Radio(props: Omit<CheckboxProps, 'radio'>) {
  return <Checkbox {...props} radio />;
}

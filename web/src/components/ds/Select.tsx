// Community Solutions design system: Select (uppercase condensed label, 2px navy border, 4px
// radius, chevron). className replaces style; id passes through.
import type { ChangeEvent } from 'react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps {
  label?: string;
  options?: (string | SelectOption)[];
  value?: string;
  defaultValue?: string;
  onChange?: (e: ChangeEvent<HTMLSelectElement>) => void;
  helper?: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Select({ label, options = [], value, defaultValue, onChange, helper, placeholder, disabled = false, className, id }: SelectProps) {
  return (
    <label className={['ds-field', className ?? ''].filter(Boolean).join(' ')}>
      {label && <span className="ds-field__label">{label}</span>}
      <span className="ds-select">
        <select id={id} value={value} defaultValue={defaultValue} onChange={onChange} disabled={disabled}>
          {placeholder && <option value="">{placeholder}</option>}
          {options.map((o) =>
            typeof o === 'string' ? (
              <option key={o} value={o}>
                {o}
              </option>
            ) : (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ),
          )}
        </select>
        <svg className="ds-select__chevron" aria-hidden="true" width="14" height="14" viewBox="0 0 24 24" fill="none" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </span>
      {helper && <span className="ds-field__helper">{helper}</span>}
    </label>
  );
}

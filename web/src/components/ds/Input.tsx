// Community Solutions design system: Input (uppercase condensed label, 2px navy border, 4px
// radius). className replaces style; step and inputMode pass through for number fields.
import { useId, type ChangeEvent } from 'react';

export interface InputProps {
  label?: string;
  helper?: string;
  /** Error message; turns the border coral-red */
  error?: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  type?: string;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  id?: string;
  className?: string;
  step?: string;
  inputMode?: 'decimal' | 'numeric' | 'text';
}

export function Input({ label, helper, error, placeholder, value, defaultValue, onChange, type = 'text', disabled = false, multiline = false, rows = 4, id, className, step, inputMode }: InputProps) {
  const auto = useId();
  const iid = id ?? auto;
  const cls = ['ds-input', error ? 'ds-input--error' : ''].filter(Boolean).join(' ');
  return (
    <label htmlFor={iid} className={['ds-field', className ?? ''].filter(Boolean).join(' ')}>
      {label && <span className="ds-field__label">{label}</span>}
      {multiline ? (
        <textarea id={iid} className={cls} rows={rows} placeholder={placeholder} value={value} defaultValue={defaultValue} onChange={onChange} disabled={disabled} aria-invalid={!!error || undefined} />
      ) : (
        <input id={iid} className={cls} type={type} step={step} inputMode={inputMode} placeholder={placeholder} value={value} defaultValue={defaultValue} onChange={onChange} disabled={disabled} aria-invalid={!!error || undefined} />
      )}
      {(error || helper) && <span className={error ? 'ds-field__helper ds-field__helper--error' : 'ds-field__helper'}>{error ?? helper}</span>}
    </label>
  );
}

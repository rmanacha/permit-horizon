// Community Solutions design system: Button (pill, Asap Condensed Bold uppercase). Props as
// declared in scripts/ds-reference/index.d.ts, with className in place of style; type, title,
// aria-pressed and aria-label pass through for forms and toggles.
import type { MouseEvent, ReactNode } from 'react';

export interface ButtonProps {
  /** primary = navy; brand = sky; highlight = sunshine; outline; inverse (on dark); ghost */
  variant?: 'primary' | 'brand' | 'highlight' | 'outline' | 'inverse' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
  fullWidth?: boolean;
  /** Renders as <a> when set */
  href?: string;
  onClick?: (e: MouseEvent) => void;
  children?: ReactNode;
  className?: string;
  type?: 'button' | 'submit';
  title?: string;
  'aria-pressed'?: boolean;
  'aria-label'?: string;
}

export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  iconLeft,
  iconRight,
  fullWidth = false,
  href,
  onClick,
  children,
  className,
  type = 'button',
  ...aria
}: ButtonProps) {
  const cls = ['ds-button', `ds-button--${variant}`, `ds-button--${size}`, fullWidth ? 'ds-button--full' : '', className ?? '']
    .filter(Boolean)
    .join(' ');
  if (href) {
    return (
      <a className={cls} href={href} onClick={onClick} aria-disabled={disabled || undefined} {...aria}>
        {iconLeft}
        {children}
        {iconRight}
      </a>
    );
  }
  return (
    <button className={cls} type={type} disabled={disabled} onClick={onClick} {...aria}>
      {iconLeft}
      {children}
      {iconRight}
    </button>
  );
}

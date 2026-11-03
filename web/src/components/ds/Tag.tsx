// Community Solutions design system: Tag (pill label, uppercase). className replaces style.
import type { ReactNode } from 'react';

export interface TagProps {
  tone?: 'sky' | 'navy' | 'sunshine' | 'coral' | 'lime' | 'sand' | 'outline';
  size?: 'sm' | 'md';
  children?: ReactNode;
  className?: string;
}

export function Tag({ tone = 'sky', size = 'md', children, className }: TagProps) {
  return <span className={['ds-tag', `ds-tag--${tone}`, `ds-tag--${size}`, className ?? ''].filter(Boolean).join(' ')}>{children}</span>;
}

// Community Solutions design system: Card (flat, square; white with a 1px rule, or a solid
// ground). className replaces style; titleAs and labelId make the title a real heading.
import type { ReactNode } from 'react';

export interface CardProps {
  image?: string;
  imageAlt?: string;
  eyebrow?: string;
  title?: ReactNode;
  body?: ReactNode;
  footer?: ReactNode;
  /** Ground color */
  tone?: 'white' | 'sand' | 'navy' | 'sky';
  /** Adds paper shadow + masking-tape strip (Human Touch collage feel) */
  taped?: boolean;
  href?: string;
  className?: string;
  titleAs?: 'h2' | 'h3' | 'h4' | 'div';
  labelId?: string;
  children?: ReactNode;
}

export function Card({ image, imageAlt = '', eyebrow, title, body, footer, tone = 'white', taped = false, href, className, titleAs = 'h3', labelId, children }: CardProps) {
  const cls = ['ds-card', `ds-card--${tone}`, taped ? 'ds-card--taped' : '', href ? 'ds-card--link' : '', className ?? ''].filter(Boolean).join(' ');
  const Title = titleAs;
  const inner = (
    <>
      {image && (
        <div className="ds-card__media">
          <img src={image} alt={imageAlt} />
        </div>
      )}
      <div className="ds-card__content">
        {eyebrow && <div className="ds-eyebrow ds-card__eyebrow">{eyebrow}</div>}
        {title && (
          <Title className="ds-card__title" id={labelId}>
            {title}
          </Title>
        )}
        {body && <div className="ds-card__body">{body}</div>}
        {children}
        {footer && <div className="ds-card__footer">{footer}</div>}
      </div>
    </>
  );
  if (href) {
    return (
      <a className={cls} href={href}>
        {inner}
      </a>
    );
  }
  return (
    <section className={cls} aria-labelledby={labelId}>
      {inner}
    </section>
  );
}

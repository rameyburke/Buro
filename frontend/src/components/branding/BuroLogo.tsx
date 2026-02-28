import React from 'react';

export type BuroLogoVariant = 'mark' | 'icon';

type Props = {
  variant?: BuroLogoVariant;
  size?: number;
  title?: string;
  className?: string;
};

export function BuroLogo({
  variant = 'mark',
  size = 26,
  title = 'Buro',
  className,
}: Props) {
  const titleId = React.useId();
  const decorative = variant === 'mark';

  const icon = (
    <svg
      className={className ? `buro-mark ${className}` : 'buro-mark'}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden={decorative ? true : undefined}
      role={decorative ? undefined : 'img'}
      aria-labelledby={decorative ? undefined : titleId}
      focusable="false"
    >
      {!decorative && <title id={titleId}>{title}</title>}
      <rect
        className="buro-mark-badge"
        x="3.5"
        y="3.5"
        width="41"
        height="41"
        rx="12"
      />
      <g
        fill="none"
        stroke="currentColor"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* Ears */}
        <path d="M18.2 21.8C15.8 18.7 14.8 15.4 14.8 12.6c0-1.3 1.4-2 2.5-1.2 2.4 1.7 3.9 3.7 4.8 5.7" />
        <path d="M29.8 21.8c2.4-3.1 3.4-6.4 3.4-9.2 0-1.3-1.4-2-2.5-1.2-2.4 1.7-3.9 3.7-4.8 5.7" />

        {/* Head */}
        <path d="M19 22.4c-1.8 1.8-3 4.4-3 7.3C16 35 19.9 38 24 38s8-3 8-8.3c0-2.9-1.2-5.5-3-7.3" />

        {/* Muzzle */}
        <path d="M20.5 28.7c1.3-1 2.4-1.4 3.5-1.4s2.2.4 3.5 1.4" />
        <path d="M20.3 31.2c1.2 2.5 2.6 3.8 3.7 3.8s2.5-1.3 3.7-3.8" />

        {/* Eyes */}
        <circle cx="20.6" cy="26.4" r="0.9" fill="currentColor" stroke="none" />
        <circle cx="27.4" cy="26.4" r="0.9" fill="currentColor" stroke="none" />

        {/* Strap hint */}
        <path d="M16.5 29.7c1.5 1.3 4.2 2.1 7.5 2.1s6-.8 7.5-2.1" opacity="0.35" />
      </g>
    </svg>
  );

  if (variant === 'icon') {
    return icon;
  }

  return (
    <span className="buro-logo">
      {icon}
      <span className="buro-wordmark">Buro</span>
    </span>
  );
}

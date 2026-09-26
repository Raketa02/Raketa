'use client';

import type { ReactNode } from 'react';

import styles from './ButtonLink.module.css';

/** The error page's one button: drawn as an outlined {@link ButtonLink}, but it stays here. */
export function RetryButton({ onRetry, children }: { onRetry: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onRetry} className={`${styles.button} ${styles.outline}`}>
      {children}
    </button>
  );
}

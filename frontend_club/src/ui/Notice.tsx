import type { ReactNode } from 'react';

import styles from './Notice.module.css';

/**
 * A sentence the page says about what just happened. **`error`** is announced at once
 * (`role="alert"`); the others politely (`role="status"`).
 */
export function Notice({
  tone,
  children,
}: {
  tone: 'success' | 'error' | 'info';
  children: ReactNode;
}) {
  return (
    <div
      className={`${styles.notice} ${styles[tone]}`}
      role={tone === 'error' ? 'alert' : 'status'}
    >
      {children}
    </div>
  );
}

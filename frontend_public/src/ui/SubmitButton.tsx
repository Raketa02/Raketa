import type { ReactNode } from 'react';

import styles from './SubmitButton.module.css';

/**
 * **A form's one button**, coral and the card's full width, as the club website's primary button
 * is (club mock 1). Everything else on this site that looks like a button leaves it, and is a
 * `ButtonLink`.
 */
export function SubmitButton({ pending, children }: { pending: boolean; children: ReactNode }) {
  return (
    <button type="submit" disabled={pending} className={styles.button}>
      {children}
    </button>
  );
}

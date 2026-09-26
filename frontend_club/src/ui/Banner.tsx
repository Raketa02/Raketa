import type { ReactNode } from 'react';

import styles from './Banner.module.css';

/**
 * **The dark banner** (club mock 4): what just happened, in small capitals by its style; who or
 * what it happened to; a line on what comes next; and the button that puts it away. Announced
 * politely (`role="status"`).
 */
export function Banner({
  kicker,
  title,
  lead,
  action,
}: {
  kicker: string;
  title: ReactNode;
  lead: string;
  action: ReactNode;
}) {
  return (
    <div className={styles.banner} role="status">
      <div className={styles.words}>
        <p className={styles.kicker}>{kicker}</p>
        <p className={styles.title}>{title}</p>
        <p className={styles.lead}>{lead}</p>
      </div>
      <div className={styles.action}>{action}</div>
    </div>
  );
}

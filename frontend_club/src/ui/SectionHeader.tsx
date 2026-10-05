import type { ReactNode } from 'react';

import styles from './SectionHeader.module.css';

/**
 * **A card's head**: its title, a muted line on what it is for, and at most one action at the
 * right. The title's `id` names the card it heads.
 */
export function SectionHeader({
  id,
  title,
  lead,
  aside,
}: {
  id: string;
  title: string;
  lead?: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <header className={styles.header}>
      <div className={styles.words}>
        <h2 id={id} className={styles.title}>
          {title}
        </h2>
        {lead === undefined ? null : <p className={styles.lead}>{lead}</p>}
      </div>
      {aside === undefined ? null : <div className={styles.aside}>{aside}</div>}
    </header>
  );
}

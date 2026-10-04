import type { ReactNode } from 'react';

import styles from './PageHeader.module.css';

/**
 * **A signed-in page's head** (club mock 2): a muted caption over a heavy title, with the page's
 * one action at the right.
 */
export function PageHeader({
  caption,
  title,
  aside,
}: {
  caption?: string;
  title: string;
  aside?: ReactNode;
}) {
  return (
    <header className={styles.header}>
      <div className={styles.words}>
        {caption === undefined ? null : <p className={styles.caption}>{caption}</p>}
        <h1 className={styles.title}>{title}</h1>
      </div>
      {aside === undefined ? null : <div className={styles.aside}>{aside}</div>}
    </header>
  );
}

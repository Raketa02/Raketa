import type { ReactNode } from 'react';

import styles from './Frame.module.css';

/** **The signed-in frame** (club mock 2): the top bar, then the page on paper beneath it. */
export function Frame({ bar, children }: { bar: ReactNode; children: ReactNode }) {
  return (
    <>
      {bar}
      <main className={styles.main}>{children}</main>
    </>
  );
}

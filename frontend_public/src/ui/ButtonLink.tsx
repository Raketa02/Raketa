import type { ReactNode } from 'react';

import styles from './ButtonLink.module.css';

type Tone = 'store' | 'outline';

/**
 * **A link drawn as a button.** Every button on this site leaves it (for a store, or for the
 * app), so it is a plain `<a>`, never Next's `Link`. **`store`** is filled with ink, as the stores'
 * own badges are; **`outline`** is the club website's outlined button. Neither is coral: the
 * square is the page's one coral mark.
 */
export function ButtonLink({
  href,
  tone,
  children,
}: {
  href: string;
  tone: Tone;
  children: ReactNode;
}) {
  return (
    <a href={href} className={`${styles.button} ${styles[tone]}`}>
      {children}
    </a>
  );
}

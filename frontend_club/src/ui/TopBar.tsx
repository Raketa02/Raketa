import Link from 'next/link';
import type { ReactNode } from 'react';

import { NavLinks, type NavItem } from './NavLinks';
import styles from './TopBar.module.css';
import { Wordmark } from './Wordmark';

/**
 * **The signed-in frame's bar** (club mock 2): the wordmark, the pages, the club it is signed in
 * as (*Ogrody 33 · Grzegórzki, Kraków*) and the way out. The club's line opens its details.
 */
export function TopBar({
  home,
  label,
  items,
  club,
  signOut,
}: {
  home: string;
  /** What a screen reader calls the list of pages. */
  label: string;
  items: readonly NavItem[];
  club: {
    readonly name: string;
    readonly place: string;
    readonly href: string;
    /** What the club's line opens, said on hover. */
    readonly title: string;
  };
  signOut: ReactNode;
}) {
  return (
    <header className={styles.bar}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <Wordmark href={home} />
        </div>
        <nav aria-label={label} className={styles.pages}>
          <NavLinks items={items} />
        </nav>
        <div className={styles.account}>
          <Link href={club.href} className={styles.club} title={club.title}>
            <strong className={styles.clubName}>{club.name}</strong>
            <span className={styles.place}>
              <span aria-hidden="true"> · </span>
              {club.place}
            </span>
          </Link>
          <div className={styles.signOut}>{signOut}</div>
        </div>
      </div>
    </header>
  );
}

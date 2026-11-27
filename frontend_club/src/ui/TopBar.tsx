import type { ReactNode } from 'react';

import { MenuButton } from './MenuButton';
import { NavLinks, type NavItem } from './NavLinks';
import styles from './TopBar.module.css';
import { Wordmark } from './Wordmark';

/**
 * **The signed-in frame's bar** (club mock 2, the screens B1): the wordmark, the pages, the club
 * it is signed in as (*Ogrody 33 · Grzegórzki, Kraków*) and the way out. The club's line opens
 * the pages about the club itself.
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
    /** The pages the club's line opens: its details and its Rakieta settings. */
    readonly pages: readonly NavItem[];
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
          <div className={styles.clubArea}>
            <MenuButton
              className={styles.club}
              name={club.name}
              items={club.pages}
              label={
                <span>
                  <strong className={styles.clubName}>{club.name}</strong>
                  <span className={styles.place}>
                    <span aria-hidden="true"> · </span>
                    {club.place}
                  </span>
                </span>
              }
            />
          </div>
          <div className={styles.signOut}>{signOut}</div>
        </div>
      </div>
    </header>
  );
}

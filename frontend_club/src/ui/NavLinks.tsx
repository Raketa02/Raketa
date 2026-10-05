'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import styles from './TopBar.module.css';

export interface NavItem {
  readonly href: string;
  readonly label: string;
  /**
   * A count drawn on a coral badge after the name, while something there waits for the desk,
   * and what it counts as a screen reader reads it: *2*, *2 waiting for your answer*.
   */
  readonly badge?: { readonly count: number; readonly label: string };
}

/**
 * The top bar's pages, with the one being shown set on its pill (club mock 2), and a coral
 * badge on a page while something there waits for the desk (the screens B1).
 */
export function NavLinks({ items }: { items: readonly NavItem[] }) {
  const pathname = usePathname();
  return (
    <ul className={styles.nav}>
      {items.map((item) => {
        const current = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              className={styles.navLink}
              aria-current={current ? 'page' : undefined}
              aria-label={
                item.badge === undefined ? undefined : `${item.label}, ${item.badge.label}`
              }
            >
              {item.label}
              {item.badge === undefined ? null : (
                <span className={styles.badge} aria-hidden="true">
                  {item.badge.count}
                </span>
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

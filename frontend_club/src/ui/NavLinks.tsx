'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import styles from './TopBar.module.css';

export interface NavItem {
  readonly href: string;
  readonly label: string;
}

/** The top bar's pages, with the one being shown set on its pill (club mock 2). */
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
            >
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

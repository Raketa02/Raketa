import Link from 'next/link';

import styles from './Segments.module.css';

export interface Segment {
  readonly href: string;
  readonly label: string;
  /** How many it shows, drawn after its name. */
  readonly count: number;
  /** The one being shown. */
  readonly current: boolean;
}

/**
 * **One view of a list among several**, each with how many it holds: links drawn as a row of
 * pills under a name, the one being shown set in ink.
 */
export function Segments({ label, items }: { label: string; items: readonly Segment[] }) {
  return (
    <nav aria-label={label}>
      <ul className={styles.segments}>
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={styles.segment}
              aria-current={item.current ? 'true' : undefined}
            >
              {item.label} <span className={styles.count}>{item.count}</span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

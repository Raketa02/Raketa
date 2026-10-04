import Link from 'next/link';
import type { ReactNode } from 'react';

import styles from './TextLink.module.css';

/** An in-site link set in running text, such as *Forgot password?* under Sign in. */
export function TextLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className={styles.link}>
      {children}
    </Link>
  );
}

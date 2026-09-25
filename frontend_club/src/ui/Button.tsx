import Link from 'next/link';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

import styles from './Button.module.css';

type Tone = 'primary' | 'secondary' | 'danger' | 'quiet';

function classes(tone: Tone, full: boolean): string {
  return [styles.button, styles[tone], full ? styles.full : ''].filter(Boolean).join(' ');
}

/**
 * A button. **`primary`** is the coral one a page has at most one of; **`secondary`** is
 * outlined (club mock 2's *Reset password*); **`danger`** is outlined with red words (*Remove*);
 * **`quiet`** is words alone, for *Sign out*.
 */
export function Button({
  tone = 'primary',
  full = false,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { tone?: Tone; full?: boolean }) {
  return <button {...rest} className={classes(tone, full)} />;
}

/** A link drawn as a button. */
export function ButtonLink({
  href,
  tone = 'secondary',
  children,
}: {
  href: string;
  tone?: Tone;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={classes(tone, false)}>
      {children}
    </Link>
  );
}

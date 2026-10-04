import Link from 'next/link';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

import styles from './Button.module.css';

type Tone = 'primary' | 'outline' | 'secondary' | 'ink' | 'danger' | 'quiet' | 'inverse';

function classes(tone: Tone, full: boolean): string {
  return [styles.button, styles[tone], full ? styles.full : ''].filter(Boolean).join(' ');
}

/**
 * A button. **`primary`** is the coral one a page has at most one of; **`outline`** is its
 * outlined twin, for the way back beside it (club mock 3's *Cancel*); **`secondary`** is an
 * outlined pill (club mock 2's *Reset password*); **`ink`** is that pill filled dark, for the
 * answer a row leads with (club mock 20's *Approve*); **`danger`** is the outlined pill with red
 * words (*Remove*); **`quiet`** is words alone, for *Sign out*; **`inverse`** sits on the dark
 * banner (club mock 4's *Done*).
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

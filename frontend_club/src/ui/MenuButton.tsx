'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useId, useRef, useState, type ReactNode } from 'react';

import styles from './MenuButton.module.css';
import type { NavItem } from './NavLinks';

/**
 * **A button that opens a short list of pages** (the screens B1: the club's name opening
 * *Details* and *Rakieta settings*). A disclosure, not an application menu: the button says
 * whether it is open, Tab walks the links, and the page being shown is marked. It closes with
 * Escape (back on its button), with a click or a focus anywhere else, and when a page opens.
 */
export function MenuButton({
  label,
  name,
  items,
  className,
}: {
  /** What the button shows. */
  label: ReactNode;
  /** What a screen reader calls the list it opens. */
  name: string;
  items: readonly NavItem[];
  className?: string;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [shownAt, setShownAt] = useState(pathname);
  const root = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const listId = useId();

  // A page opened: adjust during render, as React recommends over an effect.
  if (shownAt !== pathname) {
    setShownAt(pathname);
    setOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    const away = (event: PointerEvent) => {
      if (event.target instanceof Node && !root.current?.contains(event.target)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      setOpen(false);
      button.current?.focus();
    };
    document.addEventListener('pointerdown', away);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('pointerdown', away);
      document.removeEventListener('keydown', escape);
    };
  }, [open]);

  return (
    <div
      ref={root}
      className={styles.menu}
      onBlur={(event) => {
        if (!(event.relatedTarget instanceof Node && root.current?.contains(event.relatedTarget))) {
          setOpen(false);
        }
      }}
    >
      <button
        ref={button}
        type="button"
        className={`${styles.button} ${className ?? ''}`}
        aria-expanded={open}
        aria-controls={listId}
        onClick={() => setOpen(!open)}
      >
        {label}
      </button>
      <ul id={listId} className={styles.list} aria-label={name} hidden={!open}>
        {items.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={styles.link}
              aria-current={pathname === item.href ? 'page' : undefined}
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

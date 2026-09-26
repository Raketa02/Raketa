'use client';

import { useEffect, useId, useRef, type ReactNode } from 'react';

import styles from './Dialog.module.css';

/**
 * **A question the page asks before it acts**: a native modal `<dialog>`, named by its title, so
 * the page behind it is inert, Escape closes it and focus goes back to the button that opened
 * it. Its owner says whether it is open; `onClose` is how it hears the dialog was dismissed.
 */
export function Dialog({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (dialog === null) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={ref} className={styles.dialog} aria-labelledby={titleId} onClose={onClose}>
      <h2 id={titleId} className={styles.title}>
        {title}
      </h2>
      {children}
    </dialog>
  );
}

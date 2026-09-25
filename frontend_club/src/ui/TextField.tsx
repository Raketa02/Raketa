import { useId, type InputHTMLAttributes } from 'react';

import styles from './Field.module.css';

/**
 * **A labelled box** (club mock 1): the label over it, set in capitals by its style and never
 * by the copy, a hint under it, and the refusal under that, tied to the box so a screen reader
 * reads it with the field.
 */
export function TextField({
  label,
  hint,
  error,
  mono = false,
  ...input
}: Omit<InputHTMLAttributes<HTMLInputElement>, 'id' | 'className'> & {
  label: string;
  hint?: string;
  error?: string | null;
  mono?: boolean;
}) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = [hint === undefined ? null : hintId, error ? errorId : null]
    .filter(Boolean)
    .join(' ');
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <input
        {...input}
        id={id}
        className={mono ? `${styles.input} ${styles.mono}` : styles.input}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy || undefined}
      />
      {hint === undefined ? null : (
        <p id={hintId} className={styles.hint}>
          {hint}
        </p>
      )}
      {error ? (
        <p id={errorId} className={styles.error}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

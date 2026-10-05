import { useId, type SelectHTMLAttributes } from 'react';

import styles from './Field.module.css';

export interface SelectOption {
  readonly value: string;
  readonly label: string;
}

/** **A labelled list to choose from**, drawn as a box is (see {@link TextField}). */
export function SelectField({
  label,
  options,
  error,
  ...select
}: Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id' | 'className' | 'children'> & {
  label: string;
  options: readonly SelectOption[];
  error?: string | null;
}) {
  const id = useId();
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <select
        {...select}
        id={id}
        className={styles.input}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? (
        <p id={`${id}-error`} className={styles.error}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

import { useId, type ReactNode } from 'react';

import fieldStyles from './Field.module.css';
import styles from './Toggle.module.css';

/**
 * **A setting that is on or off**: a real checkbox announced as a switch, drawn as one, with its
 * label beside it and a line under the label on what it does, read as its description. What it
 * reveals while on comes as `children`, under it.
 */
export function Toggle({
  label,
  hint,
  name,
  checked,
  onChange,
  children,
}: {
  label: string;
  hint?: ReactNode;
  name: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  children?: ReactNode;
}) {
  const id = useId();
  return (
    <div className={styles.setting}>
      <div className={styles.row}>
        <input
          id={id}
          type="checkbox"
          role="switch"
          name={name}
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          aria-describedby={hint === undefined ? undefined : `${id}-hint`}
          className={styles.input}
        />
        <div className={styles.words}>
          <label htmlFor={id} className={styles.label}>
            {label}
          </label>
          {hint === undefined ? null : (
            <p id={`${id}-hint`} className={fieldStyles.hint}>
              {hint}
            </p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

import { useId } from 'react';

import fieldStyles from './Field.module.css';
import styles from './Chips.module.css';

export interface ChipOption<V extends string> {
  readonly value: V;
  readonly label: string;
}

/**
 * **A row of chips, several of which may be on**: real checkboxes under a legend, so the form
 * posts them and a keyboard ticks them, drawn as pills.
 */
export function Chips<V extends string>({
  legend,
  name,
  options,
  selected,
  onToggle,
  error,
}: {
  legend: string;
  name: string;
  options: readonly ChipOption<V>[];
  selected: readonly V[];
  onToggle: (value: V) => void;
  error?: string | null;
}) {
  const errorId = `${useId()}-error`;
  return (
    <fieldset
      className={fieldStyles.group}
      aria-describedby={error ? errorId : undefined}
      aria-invalid={error ? true : undefined}
    >
      <legend className={fieldStyles.legend}>{legend}</legend>
      <div className={styles.chips}>
        {options.map((option) => (
          <label key={option.value} className={styles.chip}>
            <input
              type="checkbox"
              name={name}
              value={option.value}
              checked={selected.includes(option.value)}
              onChange={() => onToggle(option.value)}
              className={styles.box}
            />
            <span className={styles.face}>{option.label}</span>
          </label>
        ))}
      </div>
      {error ? (
        <p id={errorId} className={fieldStyles.error}>
          {error}
        </p>
      ) : null}
    </fieldset>
  );
}

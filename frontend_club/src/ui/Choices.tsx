import { useId } from 'react';

import styles from './Chips.module.css';
import type { ChipOption } from './Chips';
import fieldStyles from './Field.module.css';

/**
 * **A row of chips, one of which is on**: real radio buttons under a legend, so the form posts
 * the one chosen and the arrow keys move between them, drawn as {@link Chips} draws its pills.
 * `value` is `null` while none is chosen.
 */
export function Choices<V extends string>({
  legend,
  name,
  options,
  value,
  onChange,
  error,
}: {
  legend: string;
  name: string;
  options: readonly ChipOption<V>[];
  value: V | null;
  onChange: (value: V) => void;
  error?: string | null;
}) {
  const id = useId();
  const legendId = `${id}-legend`;
  const errorId = `${id}-error`;
  return (
    <fieldset className={fieldStyles.group}>
      <legend id={legendId} className={fieldStyles.legend}>
        {legend}
      </legend>
      <div
        role="radiogroup"
        aria-labelledby={legendId}
        aria-describedby={error ? errorId : undefined}
        aria-invalid={error ? true : undefined}
        className={styles.chips}
      >
        {options.map((option) => (
          <label key={option.value} className={styles.chip}>
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
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

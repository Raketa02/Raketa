import { useId, type ReactNode } from 'react';

import fieldStyles from './Field.module.css';
import styles from './RadioCards.module.css';

export interface RadioCard<V extends string> {
  readonly value: V;
  readonly title: string;
  /** What choosing it means, in a line or two: read as the radio's description. */
  readonly explain: string;
}

/**
 * **A choice that needs explaining**: one radio per card, its title the radio's name and its
 * lines the radio's description, under a legend. The chosen card is drawn in ink. `value` is
 * `null` while none is chosen; `note` is a line under the cards that holds for every choice.
 */
export function RadioCards<V extends string>({
  legend,
  name,
  options,
  value,
  onChange,
  note,
  error,
}: {
  legend: string;
  name: string;
  options: readonly RadioCard<V>[];
  value: V | null;
  onChange: (value: V) => void;
  note?: ReactNode;
  error?: string | null;
}) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <fieldset className={fieldStyles.group}>
      <legend id={`${id}-legend`} className={fieldStyles.legend}>
        {legend}
      </legend>
      <div
        role="radiogroup"
        aria-labelledby={`${id}-legend`}
        aria-describedby={error ? errorId : undefined}
        aria-invalid={error ? true : undefined}
        className={styles.group}
      >
        <div className={styles.cards}>
          {options.map((option) => (
            <label key={option.value} className={styles.card}>
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                onChange={() => onChange(option.value)}
                aria-labelledby={`${id}-${option.value}-title`}
                aria-describedby={`${id}-${option.value}-explain`}
                className={styles.radio}
              />
              <span id={`${id}-${option.value}-title`} className={styles.title}>
                {option.title}
              </span>
              <span id={`${id}-${option.value}-explain`} className={styles.explain}>
                {option.explain}
              </span>
            </label>
          ))}
        </div>
        {note === undefined ? null : <p className={fieldStyles.hint}>{note}</p>}
        {error ? (
          <p id={errorId} className={fieldStyles.error}>
            {error}
          </p>
        ) : null}
      </div>
    </fieldset>
  );
}

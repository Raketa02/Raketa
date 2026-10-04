import styles from './Bar.module.css';

/**
 * **A green bar filled to `value` of `max`** (club mock 15's *From WhatsApp*, now *From original group*), and full past it.
 * A native `<progress>`, so its fill needs no inline width. It only draws: the figure beside it
 * says the same in words, so a screen reader is not told twice.
 */
export function Bar({ value, max }: { value: number; max: number }) {
  return (
    <progress className={styles.bar} value={Math.min(value, max)} max={max} aria-hidden="true" />
  );
}

import styles from './CodeBox.module.css';
import labelStyles from './Label.module.css';

/** **A code set out for typing somewhere else**, large and in mono, under its label. */
export function CodeBox({ label, code }: { label: string; code: string }) {
  return (
    <div className={styles.box}>
      <p className={labelStyles.label}>{label}</p>
      <p className={styles.code}>{code}</p>
    </div>
  );
}

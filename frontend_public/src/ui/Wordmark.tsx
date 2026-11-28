import styles from './Wordmark.module.css';

/**
 * The coral square and **Rakieta**, the club website's wordmark (club mock 1) with the site's own
 * name. The brand is Rakieta (ADR-0211). Not a link: this site has no page of its own to go to.
 */
export function Wordmark({ name }: { name: string }) {
  return (
    <span className={styles.wordmark}>
      <span className={styles.mark} aria-hidden="true" />
      <span className={styles.name}>{name}</span>
    </span>
  );
}

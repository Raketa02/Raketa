import { invitedYou } from '../copy';
import type { LinkOwner } from '../mappers';

import styles from './OwnerCard.module.css';

/**
 * **Who invited you** (the friends screens §11): their face and *Tomek invited you to play on
 * Raketa*, laid out as the group page lays out a group's tile and name. The face is a box rounded
 * as the app rounds one, and somebody with no photograph has none: the app's stand-in, a poster,
 * is drawn from an id the public read rightly withholds, and a face carries no initials
 * (ADR-0167 §3).
 *
 * **The face is hidden from assistive technology**, as the app hides one: it has no action, and
 * the name is in the heading beside it. It is this site's own picture, `face`, never the
 * backend's link to the photograph.
 */
export function OwnerCard({ owner, face }: { owner: LinkOwner; face: string }) {
  return (
    <header className={styles.owner}>
      {owner.hasFace ? (
        // A plain <img>: next/image would hand the face to Next's optimizer, which keeps a copy.
        // eslint-disable-next-line @next/next/no-img-element
        <img className={styles.face} src={face} alt="" />
      ) : null}
      <h1 className={styles.invited}>{invitedYou(owner.nickname)}</h1>
    </header>
  );
}

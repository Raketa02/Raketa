import { Button } from '@/ui/Button';
import { Notice } from '@/ui/Notice';

import type { CheckInState } from '../actions';
import { CHECK_IN_COPY, checkedInGame, checkedInPlayer, checkInRefusal } from '../copy';

import styles from './CheckIn.module.css';

/**
 * **The last code's answer**, whichever way it came (the screens B6): the game and the player
 * checked in, *19:00 · Court 2 · Padel* over *Piotr S. — checked in ✓*, or why nobody was. A scan
 * the server could not be asked about can be sent again: the camera asks about a code once.
 */
export function CheckInAnswer({
  state,
  checking,
  onTryAgain,
}: {
  state: CheckInState;
  checking: boolean;
  onTryAgain: () => void;
}) {
  if (checking) return <p className={styles.line}>{CHECK_IN_COPY.checking}</p>;
  if (state.checkedIn !== null) {
    return (
      <div className={styles.checkedIn} role="status">
        <p className={styles.game}>{checkedInGame(state.checkedIn)}</p>
        <p className={styles.player}>{checkedInPlayer(state.checkedIn)}</p>
      </div>
    );
  }
  if (state.refusal === null) return null;
  return (
    <div className={styles.refused}>
      <Notice tone="error">{checkInRefusal(state.refusal)}</Notice>
      {state.refusal.mayTryAgain && state.via === 'camera' ? (
        <Button type="button" tone="secondary" onClick={onTryAgain}>
          {CHECK_IN_COPY.retry}
        </Button>
      ) : null}
    </div>
  );
}

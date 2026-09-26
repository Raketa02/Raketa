import type { Hue, LinkedGroup } from '../mappers';

import styles from './Monogram.module.css';

/** Each key's fill, over all eight: a ninth fails to compile until it has one. */
const FILLS: Readonly<Record<Hue, string | undefined>> = {
  0: styles.hue0,
  1: styles.hue1,
  2: styles.hue2,
  3: styles.hue3,
  4: styles.hue4,
  5: styles.hue5,
  6: styles.hue6,
  7: styles.hue7,
};

/**
 * **A group's tile**: two letters on a fill that never changes for that group. The letters and
 * the key are the backend's (ADR-0183 §5), so this page draws the tile the app draws.
 *
 * **Hidden from assistive technology**, as the app hides it: the tile is a picture of the name,
 * and the name is always drawn beside it.
 */
export function Monogram({ monogram }: { monogram: LinkedGroup['monogram'] }) {
  return (
    <span className={`${styles.tile} ${FILLS[monogram.hue]}`} aria-hidden="true">
      {monogram.letters}
    </span>
  );
}

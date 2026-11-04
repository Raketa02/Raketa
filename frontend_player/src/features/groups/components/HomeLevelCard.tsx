/**
 * **Home's *Get your level*** — the door where play begins, on Home, for a member of a group who
 * holds no rating ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §7, [#731](https://github.com/Raketa02/Raketa/issues/731)): *Get your level — your groups can't
 * deal you games until you have one.*
 *
 * A player who joins a group and never opens it would otherwise never learn why nothing happens:
 * she is dealt no game, so nothing tells her anything. **The card is onboarding's door**
 * (`LevelDoor`), begun from Home — it opens *Which sports do you play?* over every sport, the last
 * *Your rating* says *Back to Home*, and with a run left halfway it offers *Carry on* and never to
 * start again. **Whether it is drawn is this feature's rule** (`useHomeAsksForALevel`): it knows the
 * groups, and it already reads the ratings for every group's chip. Nothing is drawn until that is
 * answered, and once she holds any rating — a pass from here, or from a group — it is gone: a
 * completion marks the ratings stale.
 */

import { FROM_HOME, LevelDoor } from '@/features/onboarding/types';

import { useHomeAsksForALevel } from '../hooks/useHomeAsksForALevel';

export function HomeLevelCard() {
  return useHomeAsksForALevel() === true ? <LevelDoor from={FROM_HOME} /> : null;
}

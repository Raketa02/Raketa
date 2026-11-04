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
 * start again. **Whether it is drawn is this feature's rule** (`homeAsksForALevel`): it knows the
 * groups, and it already reads the ratings for every group's chip.
 *
 * **The ratings are read first, and the groups only for a player rated in nothing** — a rated
 * player, the common Home, costs one read, which the chip on every group's page shares. **Nothing is
 * drawn until both have answered**, and nothing on a failed read: the card is a nudge, never a wall,
 * and a Home that cannot say whether to nudge says nothing. Once she holds any rating — a pass from
 * here, or from a group — it is gone: a completion marks the ratings stale.
 */

import { FROM_HOME, LevelDoor, useSkillRatings } from '@/features/onboarding/types';

import { homeAsksForALevel } from '../domain/groupPage';
import { useMyGroups } from '../hooks/useGroups';

export function HomeLevelCard() {
  const ratings = useSkillRatings();
  const rated = ratings.data?.map((rating) => rating.sport);
  const groups = useMyGroups({ enabled: rated?.length === 0 });

  if (rated === undefined || groups.data === undefined) return null;
  if (!homeAsksForALevel(groups.data.length, rated)) return null;

  return <LevelDoor from={FROM_HOME} />;
}

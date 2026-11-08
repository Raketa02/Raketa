/**
 * Turn ***Show me in General*** on or off ([ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md)
 * §7; the You spec §3.14; [#778](https://github.com/Raketa02/Raketa/issues/778)).
 *
 * What it means — off, the player's row leaves everybody else's General and strangers can no longer
 * reach them through the ranking — is the server's rule and the row's sentence; nothing here
 * re-decides it. **It answers with what the profile now holds**, which is the value sent, for the
 * gender write's reason: the route answers `204` and keeps exactly the value it was given.
 */

import { setRankingVisibility } from '../api/playerProfileApi';
import { toWireRankingVisibility } from '../mappers/playerProfileMappers';

export function changeShowMeInGeneral(showMeInGeneral: boolean): Promise<boolean> {
  return setRankingVisibility({ visibility: toWireRankingVisibility(showMeInGeneral) }).then(
    () => showMeInGeneral,
  );
}

/**
 * Turn ***Show me to new people*** on or off
 * ([ADR-0204](../../../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
 * §2; the Home rows screens §9.1; [#799](https://github.com/Rakieta02/Rakieta/issues/799)).
 *
 * What it means — off, anybody who shares no group, game or friendship with the player reads their
 * record as not available and can't send them a request — is the server's rule and the row's
 * sentence; nothing here re-decides it. **It answers with what the profile now holds**, which is the
 * value sent, for the gender write's reason: the route answers `204` and keeps exactly the value it
 * was given.
 */

import { setShowMeToNewPeople } from '../api/playerProfileApi';

export function changeShowMeToNewPeople(on: boolean): Promise<boolean> {
  return setShowMeToNewPeople({ on }).then(() => on);
}

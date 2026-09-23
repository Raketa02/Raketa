/**
 * Make this the player's intro, or withdraw it — the You tab's *Save* and *Remove intro*
 * (ADR-0179 §6).
 *
 * It takes **the line the screen would keep**: trimmed by `introStanding`, and one the two
 * shape rules admit, because the screen shuts *Save* on the other two before anything is
 * sent. `undefined` withdraws, and crosses as `null` — the wire's shape for a value whose
 * absence is an act. Whitespace never reaches here: a blank box is *withdraw*, said with the
 * control that says so, and never a save of nothing.
 *
 * **It answers with what the profile now holds**, which is the line sent — the route answers
 * `204` on purpose, and what the server keeps of an admitted line is exactly the trimmed line
 * it was sent, the same trim the screen applied. The fence's third reason,
 * `contains_contact`, is the server's pattern and arrives as the rejection.
 */

import { changeIntro as putIntro } from '../api/playerProfileApi';

export function changeIntro(line: string | undefined): Promise<string | undefined> {
  return putIntro({ intro: line ?? null }).then(() => line);
}

/**
 * Change who the player is willing to be matched with — the You tab's *Save* under *Who we
 * should match you with* (ADR-0179 §2, §8).
 *
 * The preference is **mutual** ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)):
 * a narrowed one hides this player from the excluded side entirely, and the screen that sends
 * it has said so at the moment of the press. Nothing here re-decides that — the rule is
 * `gender.reachOf`'s, the sentence `genderPresentation`'s, and the write is a write.
 *
 * **It answers with what the profile now holds**, which is the preference sent, for the gender
 * write's reason: the route answers `204` and keeps exactly the value it was given.
 */

import { changeGenderPreference as putGenderPreference } from '../api/playerProfileApi';
import type { GenderPreference } from '../domain/gender';
import { toWireGenderPreference } from '../mappers/playerProfileMappers';

export function changeGenderPreference(preference: GenderPreference): Promise<GenderPreference> {
  return putGenderPreference({ genderPreference: toWireGenderPreference(preference) }).then(
    () => preference,
  );
}

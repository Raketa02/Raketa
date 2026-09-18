/**
 * Correct the player's answer to the gender question — the You tab's *Save* under *About you*
 * (ADR-0179 §2, §8).
 *
 * **It answers with what the profile now holds**, which is the answer sent: the route answers
 * `204` on purpose — the owner's own read is the one shape a gender value crosses on, and the
 * write does not become a second — and the aggregate keeps exactly the value it was given,
 * or nothing on an unchanged one. So the value sent is the value held, and the cache may say
 * so without a re-read.
 */

import { changeGender as putGender } from '../api/playerProfileApi';
import type { Gender } from '../domain/gender';
import { toWireGender } from '../mappers/playerProfileMappers';

export function changeGender(gender: Gender): Promise<Gender> {
  return putGender({ gender: toWireGender(gender) }).then(() => gender);
}

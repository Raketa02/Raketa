/**
 * Make these the player's Social tags — the You tab's *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §8).
 *
 * **The tags as the profile now holds them come back**, in the vocabulary's order whatever
 * order the picker pressed them in, and that is what a caller may draw — the week's rule on
 * the fact beside it. A served id this build has no words for is dropped on the way back
 * in, as the read drops it.
 *
 * Nothing here checks the floor or the ceiling: the picker already did, with the served
 * bounds, and the server re-checks the same two. A control is not a validation.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import { changeSocialTags as putSocialTags } from '../api/playerProfileApi';
import { toSocialTagIds } from '../mappers/playerProfileMappers';

export function changeSocialTags(
  socialTagIds: readonly SocialTagId[],
): Promise<readonly SocialTagId[]> {
  return putSocialTags({ socialTagIds }).then((response) => toSocialTagIds(response.social_tags));
}

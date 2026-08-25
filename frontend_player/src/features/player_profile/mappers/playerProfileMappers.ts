/**
 * The wire boundary for the Player profile: transport shapes in, domain objects out.
 *
 * Two things this file is responsible for beyond renaming fields.
 *
 * 1. **The served vocabulary and the vocabulary this build can draw meet here and nowhere
 *    else.** A tag id is copy on the client and nothing else, so an id with no label is a
 *    chip with no words on it and a group with no heading is a section that reads as
 *    something failing to load. Both are dropped rather than guessed at — the same answer
 *    `toSport` gives a sport a phone has not updated for.
 * 2. **Nothing is sorted.** Group order and tag order within a group are both part of the
 *    contract; the picker renders what it is given. Filtering preserves order, which is
 *    the whole of what this file does to the list.
 *
 * The dropping is kept honest by the types: a nineteenth tag arrives through `pnpm gen:api`
 * as a new member of the generated union, and this file stops compiling rather than letting
 * the tag disappear from the picker of the next build anybody ships.
 *
 * **The boundary runs both ways.** `toCommitRequest` is the outbound half: the part's six
 * answers, in the app's own words, becoming the one body that ends it. It takes a value that
 * cannot hold a missing answer (`domain/profileCommit`), so the mapping is a renaming and
 * nothing else — no default, no omission, no field decided here.
 */

import type { components } from '@/generated/schema';

import type { ProfileOptions } from '../domain/ProfileOptions';
import type { DayPart } from '../domain/ProfileDraft';
import type { ProfileCommit } from '../domain/profileCommit';
import {
  SOCIAL_TAG_GROUP_IDS,
  SOCIAL_TAG_IDS,
  type SocialTagGroupId,
  type SocialTagId,
} from '../domain/SocialTag';

type PlayerProfileOptionsResponse = components['schemas']['PlayerProfileOptionsResponse'];
type PhotoResponse = components['schemas']['PhotoResponse'];
type WireSocialTag = components['schemas']['SocialTag'];
type WireSocialTagGroup = components['schemas']['SocialTagGroup'];
type CommitPlayerProfileRequest = components['schemas']['CommitPlayerProfileRequest'];
type WireDayPart = components['schemas']['DayPart'];

/**
 * One spelling, not two.
 *
 * Unlike a sport — which the app renames on the way in — a tag id is **sent back**: it is
 * what the commit carries and what a profile is persisted with. A second spelling would
 * have to be translated back at the other boundary, and the two tables would be one release
 * away from disagreeing. So the whole of the mapping is a membership test.
 *
 * **Both halves of it matter and they answer different questions.** The parameter types are
 * the compile-time half: a nineteenth tag arrives through `pnpm gen:api` as a new member of
 * the generated union, and `return served` stops compiling until the domain list and the
 * label table have been given it. The sets are the runtime half, for the phone that has not
 * been updated in eight months and is being served an id its build has never heard of.
 */
const KNOWN_TAG_IDS = new Set<SocialTagId>(SOCIAL_TAG_IDS);
const KNOWN_GROUP_IDS = new Set<SocialTagGroupId>(SOCIAL_TAG_GROUP_IDS);

/** `undefined` for a tag this build has no words for — see the note above. */
function toSocialTagId(served: WireSocialTag): SocialTagId | undefined {
  return KNOWN_TAG_IDS.has(served) ? served : undefined;
}

function toSocialTagGroupId(served: WireSocialTagGroup): SocialTagGroupId | undefined {
  return KNOWN_GROUP_IDS.has(served) ? served : undefined;
}

export function toProfileOptions(response: PlayerProfileOptionsResponse): ProfileOptions {
  return {
    socialTagGroups: response.social_tag_groups.flatMap((served) => {
      const group = toSocialTagGroupId(served.group);
      if (group === undefined) return [];

      const tagIds = served.tags.flatMap((tag) => toSocialTagId(tag.id) ?? []);
      // A heading over no chips is worse than the group's absence: it is a section a
      // player cannot answer, and it reads as something that failed to load.
      return tagIds.length === 0 ? [] : [{ group, tagIds }];
    }),
    socialTagSelection: {
      minimum: response.social_tag_selection.minimum_tags,
      maximum: response.social_tag_selection.maximum_tags,
    },
    // The unit stays on every one of these, where the tag counts above lose theirs: inside
    // the app a `minimum` beside a list of eighteen can only be a count, and a `minimum`
    // beside a distance is one refactor away from being read as metres.
    searchRadius: {
      minimumKm: response.search_radius.minimum_km,
      maximumKm: response.search_radius.maximum_km,
      stepKm: response.search_radius.step_km,
      defaultKm: response.search_radius.default_km,
    },
  };
}

/**
 * The permanent id out of an upload's answer, and nothing else out of it.
 *
 * `PhotoResponse` carries a signed URL and an expiry beside the id, and both stop at this
 * boundary on purpose: **the URL is not an identifier and must not be stored as one.** The
 * tile is already drawing the device's own copy, so the client has no use for a second,
 * expiring address for the same picture — and a mapper that carried one would be an
 * invitation to keep it.
 */
export function toUploadedPhotoId(response: PhotoResponse): string {
  return response.photo_id;
}

/**
 * The three parts of a day, in the two spellings that exist.
 *
 * The app's are lower case because they are values in its own code; the wire's are the
 * backend's enum. A table rather than `part.toUpperCase()`, for the reason the tag ids are
 * a membership test rather than a cast: a fourth part added to either side then stops this
 * file compiling instead of producing a string the other end has never heard of.
 */
const WIRE_DAY_PART: Readonly<Record<DayPart, WireDayPart>> = {
  morning: 'MORNING',
  afternoon: 'AFTERNOON',
  evening: 'EVENING',
};

/**
 * Everything the second part collected, as the one body that ends it.
 *
 * It takes a `ProfileCommit` and not a draft, which is the whole of what keeps a partial
 * commit off the wire: the three answers that may legitimately be absent while a player is
 * walking the part have already been proved present by `readyToCommit`, so there is nothing
 * here to default, skip or guess at.
 *
 * **Order is carried, never imposed.** The photo ids are the order the player arranged —
 * the first one leads — and the tag ids and the ticked cells go as they are held. Nothing
 * is sorted and nothing is deduplicated: the picker cannot produce a repeat, and the commit
 * collapses repeated cells itself.
 *
 * **The opt-in travels with the words it was given against.** `copy_version` is the client's
 * identifier for the exact wording shown; the sentences themselves stay here and are never
 * sent. An answer with no wording beside it is not a value this app can build, so there is
 * nothing to check for at this boundary.
 */
export function toCommitRequest(commit: ProfileCommit): CommitPlayerProfileRequest {
  return {
    social_tag_ids: [...commit.socialTagIds],
    photo_ids: [...commit.photoIds],
    availability: commit.availability.map((slot) => ({
      day: slot.day,
      part: WIRE_DAY_PART[slot.part],
    })),
    location: { latitude: commit.location.latitude, longitude: commit.location.longitude },
    search_radius_km: commit.searchRadiusKm,
    proposals_opt_in: {
      accepted: commit.proposalsOptIn.accepted,
      copy_version: commit.proposalsOptIn.copyVersion,
    },
  };
}

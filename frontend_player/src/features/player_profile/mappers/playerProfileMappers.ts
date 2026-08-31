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
import { toSport } from '@/features/onboarding/types';
import { PLAY_INTENTS, type PlayIntent } from '@/shared/vocabulary/playIntent';
import type { Sport } from '@/shared/vocabulary/sport';
import {
  SOCIAL_TAG_GROUP_IDS,
  SOCIAL_TAG_IDS,
  type SocialTagGroupId,
  type SocialTagId,
} from '@/shared/vocabulary/socialTags';
import { WEEKDAYS, type DayPart, type WeekCell, type Weekday } from '@/shared/vocabulary/week';

import type { Gender, GenderPreference } from '../domain/gender';
import type { PlayerProfileSurface, PlayIntentDeclarations } from '../domain/PlayerProfileSurface';
import type { PhotoReview, UploadedPhoto } from '../domain/photoCollection';
import type { ProfileOptions } from '../domain/ProfileOptions';
import type { ProfileCommit } from '../domain/profileCommit';

type PlayerProfileOptionsResponse = components['schemas']['PlayerProfileOptionsResponse'];
type PhotoResponse = components['schemas']['PhotoResponse'];
type WireSocialTag = components['schemas']['SocialTag'];
type WireSocialTagGroup = components['schemas']['SocialTagGroup'];
type CommitPlayerProfileRequest = components['schemas']['CommitPlayerProfileRequest'];
type WireDayPart = components['schemas']['DayPart'];
type WireGender = components['schemas']['Gender'];
type WireGenderPreference = components['schemas']['GenderPreference'];
type WirePhotoReview = components['schemas']['PhotoReviewDecision'];
type AvailabilitySlotResource = components['schemas']['AvailabilitySlotResource'];
type PlayerProfileReadResponse = components['schemas']['PlayerProfileReadResponse'];
type WirePlayIntent = components['schemas']['PlayIntent'];

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
 * The two spellings of a verdict, which are the same word and still get a table.
 *
 * The reason is the day parts', not the tag ids': `PhotoReview` is an enum the app speaks
 * in its own words rather than an id it stores and sends back, so a third value on either
 * side stops this file compiling instead of producing a string the row has no sentence for.
 */
const APP_PHOTO_REVIEW: Readonly<Record<WirePhotoReview, PhotoReview>> = {
  allowed: 'allowed',
  flagged: 'flagged',
};

/**
 * What the check concluded, or `allowed` where it said nothing this build understands.
 *
 * Two absences fold into the same answer and both are deliberate. The field is **optional
 * on the wire** — `GET /photos/{id}` carries no verdict at all, and so does any response
 * from a backend older than the one that added it — and a value outside the table is a
 * decision minted after this build shipped, which is the phone that has not been updated in
 * eight months. Neither is a reason to warn: a warning the app cannot phrase is a warning
 * it must not invent, and `null` is explicitly not `allowed` on the wire precisely so that
 * this decision is made here rather than assumed there.
 *
 * The same answer `toSocialTagId` gives a tag with no label, arrived at the same way — the
 * difference is only that a chip with no words can be dropped and a photograph cannot.
 */
function toPhotoReview(served: PhotoResponse['review']): PhotoReview {
  return served == null ? 'allowed' : (APP_PHOTO_REVIEW[served] ?? 'allowed');
}

/**
 * The permanent id and the verdict out of an upload's answer, and nothing else out of it.
 *
 * `PhotoResponse` carries a signed URL and an expiry beside them, and both stop at this
 * boundary on purpose: **the URL is not an identifier and must not be stored as one.** The
 * tile is already drawing the device's own copy, so the client has no use for a second,
 * expiring address for the same picture — and a mapper that carried one would be an
 * invitation to keep it.
 *
 * The verdict does cross, because it is the one thing in that answer the player is told
 * about. What it was computed from does not cross the *wire* at all: the model, the prompt
 * set and the similarity vector stay on the stored object, so there is nothing here to
 * decide about them.
 */
export function toUploadedPhoto(response: PhotoResponse): UploadedPhoto {
  return { photoId: response.photo_id, review: toPhotoReview(response.review) };
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

/** The same table read the other way, inverted so the two cannot disagree about a part. */
const DAY_PART: Readonly<Record<WireDayPart, DayPart>> = {
  MORNING: 'morning',
  AFTERNOON: 'afternoon',
  EVENING: 'evening',
};

const WEEKDAY = new Set<number>(WEEKDAYS);

/**
 * A week as the wire spells it — **the whole grid, every time**, because the list *is* the
 * week and what is absent from it is unticked.
 *
 * Exported because Play sends one too: the search's `availability_override` is this same
 * twenty-one-cell week improvised for one search
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)), and a second table spelled in that
 * feature's `mappers/` would be the drift `week.ts` was promoted to stop, arriving one layer
 * lower. `sport.ts`'s rule is the shape: *the two spellings meet in `mappers/`, and only
 * there* — so this is the one place, and Play reaches it through this feature's public
 * surface.
 *
 * **Order is carried, never imposed.** Nothing here sorts and nothing deduplicates; the
 * write path collapses repeated cells itself.
 */
export function toWireSlots(week: readonly WeekCell[]): AvailabilitySlotResource[] {
  return week.map((cell) => ({ day: cell.day, part: WIRE_DAY_PART[cell.part] }));
}

/**
 * The inbound half. A cell naming a day outside 1-7 is **dropped**, not clamped.
 *
 * The wire types `day` as a bare integer, so seven is a promise rather than a compiler's
 * guarantee, and there is no honest eighth day to render — the answer `toSocialTagId` gives
 * a tag with no label, for the same reason.
 */
export function toWeekCells(slots: readonly AvailabilitySlotResource[]): readonly WeekCell[] {
  return slots.flatMap((slot) =>
    WEEKDAY.has(slot.day) ? [{ day: slot.day as Weekday, part: DAY_PART[slot.part] }] : [],
  );
}

/**
 * The declaration map: **only the sports that were answered for.**
 *
 * A sport this build has no identity for takes its own key out with it, which is the same
 * drop `toSports` makes — a declaration nothing can name is a declaration no chip can be
 * drawn for. An intent outside this build's three is dropped for the second half of the same
 * reason: `MODE_WITHOUT_A_DECLARATION` is a truthful opening for a sport the platform has an
 * answer for and this build cannot read, where guessing at a weight vector is not.
 */
const KNOWN_PLAY_INTENTS = new Set<PlayIntent>(PLAY_INTENTS);

function toPlayIntentDeclarations(
  served: Readonly<Record<string, WirePlayIntent>>,
): PlayIntentDeclarations {
  const declared: Partial<Record<Sport, PlayIntent>> = {};
  for (const [wireSport, intent] of Object.entries(served)) {
    const one = toPlayIntentDeclared({ sport: wireSport, intent });
    if (one === undefined) continue;
    declared[one.sport] = one.intent;
  }
  return declared;
}

/**
 * **One** declaration, as the profile now holds it — the `PUT`'s own answer.
 *
 * The same narrowing the map above makes, exported because the write path needs it for the
 * reason the read path does: what a client sends and what the profile ends up holding are two
 * facts, and a cache written from the first is a cache that cannot be corrected by the second.
 * `undefined` where either half is a code this build cannot read, which leaves the caller to
 * re-read rather than to record something it would then draw.
 */
export function toPlayIntentDeclared(response: {
  readonly sport: string;
  readonly intent: WirePlayIntent;
}): { readonly sport: Sport; readonly intent: PlayIntent } | undefined {
  const sport = toSport(response.sport);
  if (sport === undefined || !KNOWN_PLAY_INTENTS.has(response.intent)) return undefined;
  return { sport, intent: response.intent };
}

/**
 * The three facts the Play screens hold, out of the one read that carries them.
 *
 * Nothing is defaulted here. An empty `availability` is *a cleared week*, which is a legal
 * answer and not a missing one, and an absent sport in `play_intents` is *undeclared*, which
 * is the set difference the search screen's interstitial is opened on.
 */
export function toPlayerProfileSurface(response: PlayerProfileReadResponse): PlayerProfileSurface {
  return {
    week: toWeekCells(response.availability),
    searchRadiusKm: response.search_radius_km,
    playIntents: toPlayIntentDeclarations(response.play_intents),
  };
}

/**
 * The two gender vocabularies, in the two spellings that exist.
 *
 * Tables rather than `gender.toUpperCase()`, and the reason is the day parts' rather than
 * the tag ids': these are **enums the app speaks in its own words**, not ids it stores and
 * sends back, so a fourth value on either side stops this file compiling instead of
 * producing a string the other end has never heard of. `prefer-not-to-say` would not even
 * survive a cast, which is the shape of bug a table cannot have.
 *
 * **Neither comes back.** No response shape this app reads carries a gender value out
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)
 * §6), so these are one-directional by the contract and not by omission — there is nothing
 * to write an inbound half of.
 */
const WIRE_GENDER: Readonly<Record<Gender, WireGender>> = {
  woman: 'WOMAN',
  man: 'MAN',
  'prefer-not-to-say': 'PREFER_NOT_TO_SAY',
};

const WIRE_GENDER_PREFERENCE: Readonly<Record<GenderPreference, WireGenderPreference>> = {
  'women-only': 'WOMEN_ONLY',
  'men-only': 'MEN_ONLY',
  any: 'ANY',
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
    availability: toWireSlots(commit.availability),
    location: { latitude: commit.location.latitude, longitude: commit.location.longitude },
    search_radius_km: commit.searchRadiusKm,
    proposals_opt_in: {
      accepted: commit.proposalsOptIn.accepted,
      copy_version: commit.proposalsOptIn.copyVersion,
    },
    gender: WIRE_GENDER[commit.gender],
    // Sent always, including when it is `ANY`. The field has a default on the wire and the
    // app could omit it — it does not, because *what an unconstrained player sends* would
    // then be decided by whichever side was read last.
    gender_preference: WIRE_GENDER_PREFERENCE[commit.genderPreference],
  };
}

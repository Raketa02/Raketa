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
 * **The boundary runs both ways.** `toCommitRequest` is the outbound half: the part's
 * answers, in the app's own words, becoming the one body that ends it. It takes a value that
 * cannot hold a missing answer (`domain/profileCommit`), so the mapping is a renaming and
 * nothing else — no default, no omission, no field decided here. The intro is the one field
 * that may be absent, and its absence was decided by the commit rather than here: the body
 * carries it where the commit does and leaves it out where the commit did.
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
import {
  HOURS,
  WEEKDAYS,
  type Hour,
  type WeeklyHour,
  type Weekday,
} from '@/shared/vocabulary/week';

import type { Gender, GenderPreference } from '../domain/gender';
import type { PlayerProfileSurface, PlayIntentDeclarations } from '../domain/PlayerProfileSurface';
import type { PhotoReview, UploadedPhoto } from '../domain/photoCollection';
import type { ProfileOptions } from '../domain/ProfileOptions';
import type { LocationSource } from '../domain/ProfileDraft';
import type { ProfileCommit } from '../domain/profileCommit';

type PlayerProfileOptionsResponse = components['schemas']['PlayerProfileOptionsResponse'];
type PhotoResponse = components['schemas']['PhotoResponse'];
type WireSocialTag = components['schemas']['SocialTag'];
type WireSocialTagGroup = components['schemas']['SocialTagGroup'];
type CommitPlayerProfileRequest = components['schemas']['CommitPlayerProfileRequest'];
type WireGender = components['schemas']['Gender'];
type WireGenderPreference = components['schemas']['GenderPreference'];
type WirePhotoReview = components['schemas']['PhotoReviewDecision'];
type ProfilePhotoResource = components['schemas']['ProfilePhotoResource'];
type WeeklyHourResource = components['schemas']['WeeklyHourResource'];
type PlayerProfileReadResponse = components['schemas']['PlayerProfileReadResponse'];
type WirePlayIntent = components['schemas']['PlayIntent'];
type ChangeLocationRequest = components['schemas']['ChangeLocationRequest'];

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

/**
 * A served list of tags, the ones this build can name, **in the served order** — the
 * vocabulary's, on the profile read and on the tags write's answer alike.
 */
export function toSocialTagIds(served: readonly WireSocialTag[]): readonly SocialTagId[] {
  return served.flatMap((tag) => toSocialTagId(tag) ?? []);
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
  };
}

/**
 * The two spellings of a verdict, which are the same word and still get a table.
 *
 * The reason is the gender tables', not the tag ids': `PhotoReview` is an enum the app speaks
 * in its own words rather than an id it stores and sends back, so a third value on either
 * side stops this file compiling instead of producing a string the row has no sentence for.
 */
const APP_PHOTO_REVIEW: Readonly<Record<WirePhotoReview, PhotoReview>> = {
  allowed: 'allowed',
  flagged: 'flagged',
};

/**
 * What the check concluded, or **nothing** where it said nothing this build understands.
 *
 * Two absences fold into the same answer and both are deliberate. The field is **optional
 * on the wire** — `null` on the upload is *the reviewer could not be asked*, omitted on the
 * profile read is *nobody looked*, and a backend older than the one that added it says
 * nothing — and a value outside the table is a decision minted after this build shipped,
 * which is the phone that has not been updated in eight months. Neither is a reason to
 * warn, and neither is a reason to say the check passed: a warning the app cannot phrase is
 * a warning it must not invent, and `null` is explicitly not `allowed` on the wire
 * ([ADR-0138](../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md))
 * precisely so that this decision is made here rather than assumed there. So both are
 * carried as the absence of a verdict, which the row on You reads as *not checked as on
 * court* and the step reads as nothing to say.
 *
 * The same answer `toSocialTagId` gives a tag with no label, arrived at the same way — the
 * difference is only that a chip with no words can be dropped and a photograph cannot.
 */
function toPhotoReview(served: PhotoResponse['review']): PhotoReview | undefined {
  return served == null ? undefined : APP_PHOTO_REVIEW[served];
}

/** The pair as the workbench holds it: the id, and the verdict where there is one. */
function toHeldPhoto(photoId: string, served: PhotoResponse['review']): UploadedPhoto {
  const review = toPhotoReview(served);
  return { photoId, ...(review === undefined ? {} : { review }) };
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
  return toHeldPhoto(response.photo_id, response.review);
}

/**
 * The signed address of a photo the profile already holds — the one thing `toUploadedPhoto`
 * refuses to carry, wanted for the one reason it gives: a restored photo has **no device
 * copy**, so the address is what its tile draws (`heldPhotos`). The expiry stays behind and
 * the verdict is `null` on this route by design; nothing stores the address past the screen.
 */
export function toPhotoAddress(response: PhotoResponse): string {
  return response.url;
}

const WEEKDAY = new Set<number>(WEEKDAYS);
const HOUR = new Set<number>(HOURS);

/**
 * A week as the wire spells it — **the whole week, every time**, because the list *is* the
 * week and what is absent from it is unticked.
 *
 * One spelling on both sides: a day and the wall-clock hour its cell starts at, in two named
 * fields (`WeeklyHourResource`), so the outbound half is a copy rather than a translation.
 *
 * Exported because Play sends one too: the search's `availability_override` is this same week
 * improvised for one search ([#268](https://github.com/Raketa02/Raketa/issues/268)), and a
 * second table spelled in that feature's `mappers/` would be the drift `week.ts` was promoted
 * to stop, arriving one layer lower. `sport.ts`'s rule is the shape: *the two spellings meet in
 * `mappers/`, and only there* — so this is the one place, and Play reaches it through this
 * feature's public surface.
 *
 * **Order is carried, never imposed.** Nothing here sorts and nothing deduplicates; the
 * write path collapses repeated hours itself.
 */
export function toWireWeeklyHours(week: readonly WeeklyHour[]): WeeklyHourResource[] {
  return week.map((cell) => ({ day: cell.day, hour: cell.hour }));
}

/**
 * The inbound half. A cell naming a day outside 1-7, or an hour outside 7-22, is **dropped**,
 * not clamped.
 *
 * The wire types `day` and `hour` as bare integers, so seven days and sixteen hours are a
 * promise rather than a compiler's guarantee, and there is no honest eighth day or 23:00 row to
 * render — the answer `toSocialTagId` gives a tag with no label, for the same reason.
 */
export function toWeeklyHours(cells: readonly WeeklyHourResource[]): readonly WeeklyHour[] {
  return cells.flatMap((cell) =>
    WEEKDAY.has(cell.day) && HOUR.has(cell.hour)
      ? [{ day: cell.day as Weekday, hour: cell.hour as Hour }]
      : [],
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
 * The three facts the Play screens hold and the three the You tab edits, out of the one
 * read that carries them.
 *
 * Nothing is defaulted here. An empty `weekly_hours` is *a cleared week*, which is a legal
 * answer and not a missing one; an absent sport in `play_intents` is *undeclared*, which is
 * the set difference the search screen's interstitial is opened on; an empty `photos` is *a
 * profile holding none*, which the poster stands in for; and an omitted `intro` is *none was
 * written*, never `''`. A tag this build has no words for is dropped, as the options mapping
 * drops it, and the rest keep the served order — the vocabulary's. An omitted `gender` is *never
 * asked* — a profile committed before the question existed — and is carried as the absence it
 * is, never as `prefer-not-to-say`, which is an answer somebody gives; the screen pre-selects
 * nothing.
 */
export function toPlayerProfileSurface(response: PlayerProfileReadResponse): PlayerProfileSurface {
  return {
    week: toWeeklyHours(response.weekly_hours),
    playIntents: toPlayIntentDeclarations(response.play_intents),
    socialTagIds: toSocialTagIds(response.social_tags),
    photos: response.photos.map(toProfilePhotoHeld),
    ...(response.intro === undefined ? {} : { intro: response.intro }),
    ...(response.gender === undefined ? {} : { gender: GENDER[response.gender] }),
    genderPreference: GENDER_PREFERENCE[response.gender_preference],
  };
}

/** One of the profile's photos, off the read: omitted is *nobody looked*, as `toPhotoReview` reads it. */
function toProfilePhotoHeld(served: ProfilePhotoResource): UploadedPhoto {
  return toHeldPhoto(served.photo_id, served.review);
}

/**
 * The two gender vocabularies, in the two spellings that exist.
 *
 * Tables rather than `gender.toUpperCase()`, and not the tag ids' membership test: these are
 * **enums the app speaks in its own words**, not ids it stores and
 * sends back, so a fourth value on either side stops this file compiling instead of
 * producing a string the other end has never heard of. `prefer-not-to-say` would not even
 * survive a cast, which is the shape of bug a table cannot have.
 *
 * **Both come back, on exactly one shape.** No response that describes one player to another
 * carries a gender value out
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)
 * §6); the owner's own profile read does
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §4), so that *Who you play with* can open on the answer already given. So each table has
 * an inbound half, read the other way and inverted so the two cannot disagree about a value.
 */
const WIRE_GENDER: Readonly<Record<Gender, WireGender>> = {
  woman: 'WOMAN',
  man: 'MAN',
  'prefer-not-to-say': 'PREFER_NOT_TO_SAY',
};

const GENDER: Readonly<Record<WireGender, Gender>> = {
  WOMAN: 'woman',
  MAN: 'man',
  PREFER_NOT_TO_SAY: 'prefer-not-to-say',
};

const WIRE_GENDER_PREFERENCE: Readonly<Record<GenderPreference, WireGenderPreference>> = {
  'women-only': 'WOMEN_ONLY',
  'men-only': 'MEN_ONLY',
  any: 'ANY',
};

const GENDER_PREFERENCE: Readonly<Record<WireGenderPreference, GenderPreference>> = {
  WOMEN_ONLY: 'women-only',
  MEN_ONLY: 'men-only',
  ANY: 'any',
};

/** The outbound halves, for the two writes the You tab sends one value at a time. */
export function toWireGender(gender: Gender): WireGender {
  return WIRE_GENDER[gender];
}

export function toWireGenderPreference(preference: GenderPreference): WireGenderPreference {
  return WIRE_GENDER_PREFERENCE[preference];
}

/**
 * **Where the area comes from, as both writes carry it** — the commit's `location` and
 * `PUT /players/me/location` take the same union
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §10).
 *
 * A reading is its cell, the two numbers and nothing else; a picked club is its id alone — the
 * name and the district the step held for the screen stay on the phone. **Exactly one shape and
 * never a key from the other**: each side of the server's union forbids extra keys, so a reading
 * that carried a `club_id` would be a 422.
 */
export function toWireLocation(source: LocationSource): ChangeLocationRequest {
  return source.kind === 'reading'
    ? { latitude: source.area.latitude, longitude: source.area.longitude }
    : { club_id: source.club.id };
}

/**
 * Everything the second part collected, as the one body that ends it.
 *
 * It takes a `ProfileCommit` and not a draft, which is the whole of what keeps a partial
 * commit off the wire: the answers that may legitimately be absent while a player is walking
 * the part have already been proved present by `readyToCommit`, so there is nothing here to
 * default, skip or guess at.
 *
 * **Order is carried, never imposed.** The photo ids are the order the player arranged —
 * the first one leads — and the tag ids and the ticked cells go as they are held. Nothing
 * is sorted and nothing is deduplicated: the picker cannot produce a repeat, and the commit
 * collapses repeated cells itself.
 */
export function toCommitRequest(commit: ProfileCommit): CommitPlayerProfileRequest {
  return {
    social_tag_ids: [...commit.socialTagIds],
    // Present exactly when the commit holds one. Never `null` and never `''`: the wire
    // reads both as *no intro*, and a body that spelled the absence three ways would be a
    // body a later reader could tell apart by accident.
    ...(commit.intro === undefined ? {} : { intro: commit.intro }),
    photo_ids: [...commit.photoIds],
    weekly_hours: toWireWeeklyHours(commit.weeklyHours),
    location: toWireLocation(commit.location),
    gender: WIRE_GENDER[commit.gender],
    // Sent always, including when it is `ANY`. The field has a default on the wire and the
    // app could omit it — it does not, because *what an unconstrained player sends* would
    // then be decided by whichever side was read last.
    gender_preference: WIRE_GENDER_PREFERENCE[commit.genderPreference],
  };
}

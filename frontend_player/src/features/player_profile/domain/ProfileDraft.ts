/**
 * The **profile draft**: every answer the second part collects, held on the client until
 * the commit at the end of the part.
 *
 * **Nothing here is written to the server until the last step**, and then all of it is
 * written at once ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 * That is what makes back and forward free — moving between steps costs nothing because
 * nothing has been recorded anywhere — and it is also why leaving mid-part restarts at step
 * one: there is nothing on the server to come back to. The asymmetry with part one is
 * deliberate. Eight adaptive answers are expensive and event-sourced, so a run resumes; six
 * short steps are cheap, and buying resume for them would mean a server-owned draft with a
 * version token, a second aggregate built before a single player exists.
 *
 * ## The shape is the commit's, in the app's own words
 *
 * The fields are the answers `POST /players/me/profile` carries, spelled the way this app
 * speaks rather than the way the wire does. Mapping between the two is the mapper's job and
 * arrives with the commit; a draft shaped like the request body would put the wire boundary
 * in the store.
 *
 * ## Empty and absent are different, and the difference is the product's
 *
 * Photos, the weekly hours and the intro start **empty**, because empty is a real answer to all
 * three: a player may hold no photos, *a blank week means "no preference", never "leave me
 * out"*, and a player who skips the intro has no line rather than a missing one. The area and
 * the gender answer start **absent**, because they are questions that must actually be
 * answered. `undefined` there means *not asked yet*, and it is never quietly read as an
 * answer.
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { Gender, GenderPreference } from './gender';
import { DEFAULT_GENDER_PREFERENCE } from './gender';

/**
 * One **weekly hour**: a day, and the hour its cell starts at. In the draft's list it is a
 * **ticked** one.
 *
 * `@/shared/vocabulary/week`'s own, because Play reads the same week back as *overlap* and two
 * spellings of a day would drift. Re-exported so the draft's shapes are read from one file.
 */
export type { WeeklyHour };

/**
 * Where the player plays.
 *
 * What is sent and what is kept are not the same number: the platform rounds to roughly a
 * kilometre before recording anything, and the precise fix is never stored and never
 * shareable. The draft holds what the device gave, for exactly as long as the part lasts.
 */
export interface LocationArea {
  readonly latitude: number;
  readonly longitude: number;
}

export interface ProfileDraft {
  /**
   * Tag ids as the platform serves them. Ids are persisted forever; labels are copy.
   *
   * Narrowed to the vocabulary rather than left as strings, because a draft only ever holds
   * what the picker offered — and the picker offers only what this build can draw.
   */
  readonly socialTagIds: readonly SocialTagId[];
  /**
   * The line they wrote about themselves, **as typed** — untrimmed, and empty until they
   * write one or after they skip.
   *
   * Held verbatim rather than tidied, so walking back finds the box exactly as it was left.
   * What the commit carries is `introToSend`'s reading of it: trimmed, or nothing at all.
   */
  readonly intro: string;
  /** Uploaded photo ids, in the order the player arranged them — the first one leads. */
  readonly photoIds: readonly string[];
  /** The hours of the week that were ticked. Empty is an answer. */
  readonly weeklyHours: readonly WeeklyHour[];
  readonly location: LocationArea | undefined;
  /**
   * The player's own answer. Absent until the step asks, and **never read as
   * `prefer-not-to-say`** — that is an answer somebody chose, and this is the question not
   * having been put yet.
   */
  readonly gender: Gender | undefined;
  /**
   * Who they are willing to be matched with. **Never absent**, because `any` is what having
   * narrowed nothing already means — the one field here that starts at a value rather than
   * at a blank or an empty list.
   */
  readonly genderPreference: GenderPreference;
}

/** A part that has just been entered: nothing answered, and nothing claimed on anyone's behalf. */
export function emptyDraft(): ProfileDraft {
  return {
    socialTagIds: [],
    intro: '',
    photoIds: [],
    weeklyHours: [],
    location: undefined,
    gender: undefined,
    // Not `undefined`: unconstrained is a real answer and it is the one every player starts
    // from, so there is nothing here for a step to have failed to collect.
    genderPreference: DEFAULT_GENDER_PREFERENCE,
  };
}

/**
 * Record what one step answered, leaving every other answer where it was.
 *
 * A patch rather than six setters: each step owns exactly one field, and the one thing
 * this must guarantee is that writing that field never disturbs the others — which is the
 * promise the part makes when it says walking back to check something is free.
 */
export function recordAnswer(draft: ProfileDraft, answer: Partial<ProfileDraft>): ProfileDraft {
  return { ...draft, ...answer };
}

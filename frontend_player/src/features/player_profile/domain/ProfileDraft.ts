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
 * The fields are the six answers `POST /players/me/profile` carries, spelled the way this
 * app speaks rather than the way the wire does. Mapping between the two is the mapper's
 * job and arrives with the commit; a draft shaped like the request body would put the wire
 * boundary in the store.
 *
 * ## Empty and absent are different, and the difference is the product's
 *
 * Photos and availability start **empty**, because empty is a real answer to both: a player
 * may hold no photos, and *a blank week means "no preference", never "leave me out"*. The
 * other three start **absent**, because they are questions that must actually be answered —
 * and the opt-in most of all, which has no default in either direction. `undefined` there
 * means *not asked yet*, and it is never quietly read as no.
 */

/** Which part of a day one ticked cell of the availability grid belongs to. */
export type DayPart = 'morning' | 'afternoon' | 'evening';

/**
 * ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.
 *
 * A closed union rather than a `number`, for the same reason `DayPart` beside it is not a
 * string: seven is the whole of it, and a `day: 0` is a bug a type can refuse.
 */
export type Weekday = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/** One ticked cell: a day, and one of the three parts of it. */
export interface AvailabilitySlot {
  readonly day: Weekday;
  readonly part: DayPart;
}

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

/**
 * The **Proposals opt-in**: the answer to the proposals question, and the words it was
 * given against.
 *
 * The copy version travels with the answer because **consent gathered against one sentence
 * is not consent to a different one** — a consent record that cannot name its words cannot
 * evidence anything. The words themselves stay the client's and are never sent.
 */
export interface ProposalsOptIn {
  readonly accepted: boolean;
  readonly copyVersion: string;
}

export interface ProfileDraft {
  /** Tag ids as the platform serves them. Ids are persisted forever; labels are copy. */
  readonly socialTagIds: readonly string[];
  /** Uploaded photo ids, in the order the player arranged them — the first one leads. */
  readonly photoIds: readonly string[];
  /** The cells of the week that were ticked. Empty is an answer. */
  readonly availability: readonly AvailabilitySlot[];
  readonly location: LocationArea | undefined;
  /** Whole kilometres. Absent until the player has been shown the served bounds. */
  readonly searchRadiusKm: number | undefined;
  /** Absent means *not answered*, which is neither yes nor no. */
  readonly proposalsOptIn: ProposalsOptIn | undefined;
}

/** A part that has just been entered: nothing answered, and nothing claimed on anyone's behalf. */
export function emptyDraft(): ProfileDraft {
  return {
    socialTagIds: [],
    photoIds: [],
    availability: [],
    location: undefined,
    searchRadiusKm: undefined,
    proposalsOptIn: undefined,
  };
}

/**
 * Record what one step answered, leaving every other answer where it was.
 *
 * A patch rather than six setters: each step owns exactly one field, and the one thing this
 * must guarantee is that writing that field never disturbs the other five — which is the
 * promise the part makes when it says walking back to check something is free.
 */
export function recordAnswer(draft: ProfileDraft, answer: Partial<ProfileDraft>): ProfileDraft {
  return { ...draft, ...answer };
}

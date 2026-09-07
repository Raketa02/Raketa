/**
 * The end of the part: **every answer at once, or nothing at all.**
 *
 * The draft is six answers a player builds up over six screens, and three of its fields are
 * legitimately absent while they are doing it. A commit is the opposite kind of value —
 * it is what `POST /players/me/profile` carries, and every one of those three has to be
 * there. `ProfileCommit` is that value, and `readyToCommit` is the only way to build one.
 *
 * **A partial commit is unrepresentable rather than merely avoided.** Tags saved and consent
 * lost is the worst outcome this part has available to it, so the type that reaches the
 * mapper simply cannot hold a missing answer — nothing downstream has to remember to check,
 * and no future caller can assemble a body out of a half-answered draft.
 *
 * ## Three are the fields the draft spells `| undefined`, and the fourth is the week
 *
 * **Photos are the only genuinely empty answer left.** A player may hold none, and reading
 * an empty list as *unanswered* would block them on a question they have already answered
 * (`ProfileDraft` — *empty and absent are different*). The week used to be read the same
 * way and no longer is: ADR-0102 gave the grid a floor of one, because silence about when
 * somebody usually plays is never scored — so an empty week is a question still to be
 * answered rather than an answer of *no preference*. It is the one `MissingAnswer` that is
 * a rule rather than an `undefined`, which is exactly what `ANSWER_HELD` is for.
 *
 * The tag selection is still not among them, and its absence here is deliberate. That floor
 * and ceiling are **served** by `GET /player-profile/options`, so a rule that knows nothing
 * about them cannot enforce them; the picker refuses to continue below the floor with the
 * served number in hand, and the commit re-validates. **The reason does not transfer to the
 * week**: its minimum is not served — it is exactly one, fixed by the record — so this side
 * may know it. It is not written down here either, though: `weekStanding` already decides
 * whether a week is empty, the availability step already draws its control from that
 * answer, and a second spelling of the floor beside it would be the rule decided twice.
 *
 * ## What is missing is a list, not a boolean
 *
 * A screen that can only say *something is missing* has to send the player back through six
 * steps to find out which. The names below are what let the last step say the one true
 * sentence and offer the one control that fixes it.
 *
 * ## Where the part stands, and when the finish opens
 *
 * `commitStanding` folds the readiness above together with how the request itself is going,
 * and `mayFinish` reads the one rule off it. Both are here rather than in the hook that
 * wires them or the screen that draws them, because **when the finish opens is a rule** —
 * it is what stands between a player and a Player profile, and a rule living in a
 * `disabled={…}` expression is a rule with no test and no name.
 *
 * It also supersedes `proposalsOptIn.mayFinish`, which answered the same question when
 * consent was the only thing that could hold the finish shut. *An answer that has not been
 * given is not an answer* is not dropped — it is one of the three `readyToCommit` reports,
 * so the finish still opens on either answer and on neither absence.
 *
 * No renderer, no store, no wire type: the profile editor will assemble the same value out
 * of the same rules from a screen that looks nothing like the step that ends this part.
 */

import type { AppError } from '@/shared/errors';

import { weekStanding } from './availabilityWeek';
import { uploadsInFlight, type ProfilePhoto } from './photoCollection';
import type { Gender, GenderPreference } from './gender';
import type { AvailabilitySlot, LocationArea, ProfileDraft, ProposalsOptIn } from './ProfileDraft';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { SocialStep } from './socialSteps';

/**
 * Every answer the second part collects, with nothing left to be absent.
 *
 * The same six fields as `ProfileDraft` and three of them narrowed — which is the whole
 * difference between *what a player is part-way through saying* and *what is sent*.
 */
export interface ProfileCommit {
  readonly socialTagIds: readonly SocialTagId[];
  readonly photoIds: readonly string[];
  readonly availability: readonly AvailabilitySlot[];
  readonly location: LocationArea;
  readonly searchRadiusKm: number;
  readonly proposalsOptIn: ProposalsOptIn;
  /** Narrowed from the draft's `| undefined`: the commit requires an answer. */
  readonly gender: Gender;
  /**
   * Not narrowed, because the draft never holds it absent. It is carried explicitly rather
   * than defaulted at the wire, so *what an unconstrained player sends* is one value decided
   * in one place.
   */
  readonly genderPreference: GenderPreference;
}

/** An answer the commit needs and the draft has not got. Named for the step that asks it. */
export type MissingAnswer =
  'availability' | 'location' | 'search-radius' | 'gender' | 'proposals-opt-in';

export type CommitReadiness =
  /** Every answer is in. `commit` is the body, and it could not have been built without them. */
  | { readonly kind: 'ready'; readonly commit: ProfileCommit }
  /** What is still wanted, **in step order** — so a screen names the earliest one first. */
  | { readonly kind: 'incomplete'; readonly missing: readonly MissingAnswer[] };

/**
 * The five, in the order the steps ask for them, and how to tell whether a draft holds one.
 *
 * **One list and one order**, which is what the `missing` report is filtered out of — the
 * alternative was the four names written twice, kept in step by hand, and one edit away
 * from a screen sending a player back to the wrong step.
 *
 * Four of them are a field being present. The week is a **standing**, which is why this is
 * a table of predicates rather than a list of keys: an answer the draft can hold and still
 * be short of needs somewhere to say so. It asks `weekStanding` rather than counting the
 * list itself, so the floor is one function's answer — the same one the availability step's
 * control is drawn from, and the same one that would move if the floor ever did.
 */
const ANSWER_HELD: Readonly<Record<MissingAnswer, (draft: ProfileDraft) => boolean>> = {
  availability: (draft) => weekStanding(draft.availability).kind === 'ticked',
  location: (draft) => draft.location !== undefined,
  'search-radius': (draft) => draft.searchRadiusKm !== undefined,
  // The gender answer, and **not** the preference beside it: `any` is what having narrowed
  // nothing means, so the preference cannot be absent and has nothing to report here.
  gender: (draft) => draft.gender !== undefined,
  'proposals-opt-in': (draft) => draft.proposalsOptIn !== undefined,
};

const EVERY_ANSWER = Object.keys(ANSWER_HELD) as readonly MissingAnswer[];

/**
 * Whether this draft is a commit yet, and what it is short of if it is not.
 *
 * `undefined` — no part running — answers the same way as an empty draft rather than
 * throwing: *nothing has been answered* is the truthful reading of both, and the last step
 * is the only caller either way.
 */
export function readyToCommit(draft: ProfileDraft | undefined): CommitReadiness {
  if (draft === undefined) return { kind: 'incomplete', missing: EVERY_ANSWER };

  const missing = EVERY_ANSWER.filter((answer) => !ANSWER_HELD[answer](draft));
  const { location, searchRadiusKm, proposalsOptIn, gender } = draft;

  // **One guard, because it is one question.** The four narrowings say to the compiler what
  // the filter above just said to a screen — and they are what make `ProfileCommit`
  // constructible at all. The week has no narrowing to do, since `readonly
  // AvailabilitySlot[]` is already the commit's type, so it is carried by `missing` alone;
  // counting the list a second time here would be the floor decided twice.
  if (
    missing.length > 0 ||
    location === undefined ||
    searchRadiusKm === undefined ||
    proposalsOptIn === undefined ||
    gender === undefined
  ) {
    return { kind: 'incomplete', missing };
  }

  return {
    kind: 'ready',
    commit: {
      // Named one by one rather than spread: a seventh answer added to the draft should
      // have to be carried here deliberately, not arrive at the wire because a spread
      // picked it up.
      socialTagIds: draft.socialTagIds,
      photoIds: draft.photoIds,
      availability: draft.availability,
      location,
      searchRadiusKm,
      proposalsOptIn,
      gender,
      // Carried, never defaulted here: the draft holds `any` from the moment the part is
      // entered, so this is the player's answer whether or not they touched the control.
      genderPreference: draft.genderPreference,
    },
  };
}

/**
 * How the one request is going. The half of the part's standing a draft cannot answer.
 *
 * Four states rather than a pair of booleans, for the reason `ProposalsOptInStanding` is a
 * shape rather than `boolean | undefined`: *not sent yet*, *in flight*, *refused* and
 * *landed* are four different situations, and reading one of them should be a decision
 * rather than the first `if` that happens to match.
 */
export type CommitAttempt =
  | { readonly kind: 'idle' }
  | { readonly kind: 'sending' }
  | { readonly kind: 'failed'; readonly error: AppError }
  | { readonly kind: 'landed' };

/** Where the whole part stands — what the last step renders from, and nothing else. */
export type CommitStanding =
  /** An answer is still wanted. `missing` is in step order, so the earliest one leads. */
  | { readonly kind: 'incomplete'; readonly missing: readonly MissingAnswer[] }
  /**
   * Nothing is missing, but a photo has not finished going up.
   *
   * Not *incomplete*: there is nothing for the player to answer and nothing to go back to.
   * It resolves itself, which is why it is its own state — the last step waits rather than
   * asking, and the finish opens the moment the upload lands.
   */
  | { readonly kind: 'uploading'; readonly photos: number }
  /** Everything is answered and nothing has been sent. */
  | { readonly kind: 'ready'; readonly commit: ProfileCommit }
  /** In flight. */
  | { readonly kind: 'committing' }
  /**
   * It did not land.
   *
   * **It carries the body too**, and that is the whole of what makes a retry a retry: the
   * draft was never touched, so what goes out again is the same answers — and, with the
   * part's key beside them, the same request rather than a second one.
   */
  | { readonly kind: 'failed'; readonly error: AppError; readonly commit: ProfileCommit }
  /** The server has it. The part is over. */
  | { readonly kind: 'committed' };

/**
 * The part's standing: what has been answered, what is still arriving, and what the request
 * has done about it.
 *
 * **The attempt is read before the draft, and the order is the rule.** A commit that has
 * landed clears the draft it was built from, so asking the draft first would report a part
 * that has just succeeded as *incomplete* — and the last step would flash a demand for an
 * answer the player gave a moment ago. The same holds while one is in flight: a request
 * going out is not a part that is short of something.
 *
 * **A missing answer outranks an upload**, because only one of the two is the player's to
 * do anything about. Waiting for a photo while an area is also outstanding would hold the
 * screen quiet on the thing that resolves itself and say nothing about the thing that does
 * not.
 */
export function commitStanding(
  draft: ProfileDraft | undefined,
  photos: readonly ProfilePhoto[],
  attempt: CommitAttempt,
): CommitStanding {
  if (attempt.kind === 'landed') return { kind: 'committed' };
  if (attempt.kind === 'sending') return { kind: 'committing' };

  const readiness = readyToCommit(draft);

  if (attempt.kind === 'failed') {
    // A failure over a part that is no longer complete is a failure about answers the
    // player has since taken back. What is outstanding now is the truthful thing to say,
    // and there is no body to retry with anyway.
    return readiness.kind === 'ready'
      ? { kind: 'failed', error: attempt.error, commit: readiness.commit }
      : readiness;
  }

  if (readiness.kind === 'incomplete') return readiness;

  const arriving = uploadsInFlight(photos);
  return arriving === 0 ? readiness : { kind: 'uploading', photos: arriving };
}

/**
 * Whether the finish may be pressed.
 *
 * **Open on everything the part must carry having been answered, and on nothing else.** It
 * is deliberately blind to *which* answer the proposals question got: a gate that opened
 * only on yes would be the product withholding the rest of itself until it got the answer
 * it wanted, and a player who declines has finished that step as completely as one who
 * accepts.
 *
 * A commit in flight, one that failed and one that landed all leave it open — the first
 * because *busy* is the control's own state and not a closed door, the second because the
 * finish **is** the retry, and the third because nothing about succeeding un-answers a
 * question.
 *
 * **A photo still going up closes it**, and that is the one closed state the player is not
 * asked to do anything about: `photoIds` carries the pictures that arrived, so a commit sent
 * now would drop one the player watched upload. It opens itself when the upload lands.
 */
export function mayFinish(standing: CommitStanding): boolean {
  return standing.kind !== 'incomplete' && standing.kind !== 'uploading';
}

/**
 * The body a press would send, or `undefined` when a press sends nothing.
 *
 * **Two arms carry one, and that is the rule the retry rests on.** A part that is ready has
 * never been sent; a part that failed has been sent and did not land, and re-sending *the
 * same answers under the same key* is what makes the second attempt a replay of the first
 * rather than a second profile. Nothing else may send: a commit in flight would be a
 * duplicate, and one that landed is finished.
 *
 * Separate from `mayFinish` because the two answer different questions — *may the control be
 * pressed* is about what a player sees, and a control that is merely busy stays pressable-
 * looking while sending nothing.
 */
export function commitToSend(standing: CommitStanding): ProfileCommit | undefined {
  return standing.kind === 'ready' || standing.kind === 'failed' ? standing.commit : undefined;
}

/**
 * Which step asks for each answer the commit can be short of.
 *
 * The last step is where a missing answer is discovered — it is the only screen that tries
 * to commit — and it is almost never the screen that can fix one. So the fix is *go back to
 * the step that asked*, and where that is has to be a fact rather than a sentence a screen
 * guesses at.
 *
 * `proposals-opt-in` maps to the last step itself, which is not a special case: it really is
 * the step that asks it, and a player who has not answered it is standing on the control
 * that does.
 */
export const STEP_THAT_ASKS: Readonly<Record<MissingAnswer, SocialStep>> = {
  availability: 'availability',
  location: 'location',
  'search-radius': 'radius',
  gender: 'gender',
  'proposals-opt-in': 'opt-in',
};

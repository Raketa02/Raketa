/**
 * What the challenge screen says — **the sentences no other surface writes.**
 *
 * §13's fourteen standing sentences are `challengePresentation.ts`' and are read from here
 * unchanged: this screen states the standing exactly as the row above it does, which is what
 * stops a row and the screen behind it describing one challenge two ways. What is added here is
 * the copy the screen itself brought — the two answers, the identity row, the two absences, and
 * the one spoken name §24.3 specifies.
 *
 * ## The two answers name no state the act cannot produce
 *
 * `I'm in` replaces the design's *Accept — game on*. #324 and #329 redefined *Game on* as *the
 * plan is complete and the day is ahead*, and accepting arranges nothing and draws **Planning** —
 * so the phrase is false the moment it is tapped. `I'm in` is what the standing says back:
 * *You're in — everybody's in*, *You're in. {m} seats open…*. **The label and the confirmation
 * are one sentence in two persons**, which is why neither is written twice.
 *
 * `Not this time` is kept exactly as drawn, and it is #221's own words.
 *
 * ## `Score 91` is a segment, and the row is the repo's spellings joined
 *
 * The design's row is `Squash 2,44 · band 2,18–2,70 · 3,1 km · Score 91`, and three of its four
 * segments already have one spelling each in this app — `levelRow` and `metaLine`, which every
 * Play surface draws a Level and a distance through. Those win, because a second spelling of a
 * Level is how two screens start rounding the same number differently
 * ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
 * §5's *the card's field unchanged*). The sport moves to the screen's eyebrow, where the screen
 * states it once rather than once per seat.
 *
 * The fourth segment is this file's, and **it disappears rather than reading `Score 0`**: a
 * nought printed for somebody nothing was watched of is a claim where there is a gap, and most
 * people on this platform have no Player Score today
 * ([ADR-0140](../../../../../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
 * Drawn `Score 91` and **spoken** `Player Score 91 out of 100`, which is the split Play already
 * makes between a dense row and a listener who has no row: the denominator has one home, and
 * `Score` alone in a run of numbers is the one segment that could be mistaken for a Level.
 *
 * ## Two absences, and they may never collapse into one
 *
 * ADR-0143 §6: three answers, not two, because *an outage drawing the identical absence as an
 * unrated sport is indistinguishable from four erased accounts*. **The codes are the contract and
 * the client writes both sentences** (ADR-0106), so both are here and a test holds them apart.
 *
 * Neither says *you can still answer*. The buttons are on the screen under the sentence, and copy
 * explaining a control the reader can see is the app being anxious on their behalf — what the
 * rule buys is that the buttons are **drawn**, which is `challengeArm`'s job and not a sentence's.
 * And neither apologises: *being asked to play a sport you never declared for is how this feature
 * works rather than a corner of it.*
 */

import type { AtStake } from '@/features/play/types';
import { PLAYER_SCORE_BLOCK, levelRow, metaLine, stakeClauses } from '@/features/play/types';

import type { CourtPerson, PairingAbsence } from '../domain/challengeDetail';

/**
 * The invitee's yes. See the module note: the label is the standing sentence in the first
 * person, and there is no second spelling of it anywhere.
 */
export const IM_IN = "I'm in";

/** The invitee's no, kept exactly as drawn. */
export const NOT_THIS_TIME = 'Not this time';

/**
 * **No challenge of yours has this address** — the one answer for three states.
 *
 * A `404`, a route param that does not parse, and a record whose sport this build cannot name.
 * They are deliberately not told apart, because the server refuses to tell the first two apart
 * for a reason: separating *it does not exist* from *you are not on its court* would answer *is
 * this id real* about a stranger's evening.
 */
export const NO_CHALLENGE_HERE = 'No challenge of yours has this address.';

/** What a Player Score is out of, spelled rather than assumed — and spoken, never drawn. */
const PLAYER_SCORE_DENOMINATOR = 100;

/** The segment, and the one place `Score` is written short. See the module note. */
function scoreSegment(playerScore: number): string {
  return `Score ${playerScore}`;
}

export interface IdentityRowFacts {
  readonly person: CourtPerson;
  /** Whole kilometres. **Absent rather than zero** where the distance term stood down. */
  readonly distanceKm?: number;
}

/**
 * `2,71 · Established · likely 2,55–2,87 · 3 km · Score 91` — with any segment absent.
 *
 * **`myAreaCode` is not passed and cannot be**: no route serves a player their own area code, so
 * `metaLine`'s *In your area* clause is unavailable here exactly as it is on the deck
 * ([#279](https://github.com/Raketa02/Raketa/issues/279)). It renders the kilometres alone, which
 * is the absence rather than a claim.
 */
export function identityRow(facts: IdentityRowFacts): string {
  const { person, distanceKm } = facts;

  return [
    levelRow(person),
    ...(distanceKm === undefined
      ? []
      : [metaLine({ km: distanceKm, theirAreaCode: person.areaCode })]),
    ...(person.playerScore === undefined ? [] : [scoreSegment(person.playerScore)]),
  ].join(' · ');
}

/**
 * Whose gap the pairing was — **two codes, two sentences**, and neither is an apology.
 *
 * A `Record` keyed by the union would not do: one of the two quotes the sport and the other
 * cannot, because an outage is not about a sport.
 */
export function pairingAbsenceLine(absence: PairingAbsence, sportName: string): string {
  switch (absence) {
    case 'NOTHING_TO_COMPUTE':
      return `There's no match score here — you haven't set up ${sportName} on Raketa.`;
    case 'COULD_NOT_BE_READ':
      return "We couldn't work out the match score just now.";
  }
}

export interface ChallengeCardFacts {
  readonly person: CourtPerson;
  readonly fit: number;
  readonly distanceKm?: number;
  /** The lines `selectReasons` returned, in the order the card draws them. */
  readonly reasons: readonly string[];
  /** What the card draws of `concerns[]` — one, or none. */
  readonly concerns: readonly string[];
  /**
   * What's at stake — **two clauses or none, and never one.**
   *
   * Absent on a doubles court and in for fun, both decided by `stakeOnACard` before the label is
   * composed, so there is no seat count in this file.
   */
  readonly atStake?: AtStake;
}

/**
 * The card block's name — **one element, no action** (§24.3).
 *
 * It carries no action of its own and the two buttons are beneath it, so §20.1's cap lands on
 * this label rather than on what precedes an action: **roughly twenty words before the buttons**.
 * That is a real constraint and it is the reason this is not `candidateCardLabel`. A Play card's
 * label may run long because a listener who has heard enough interrupts and presses *Why 78?* —
 * here, interrupting costs them the two controls the whole screen is for.
 *
 * **It leads with the handle**, which is the fact the whole screen is about and the one §24.3
 * names: *a merged label that cannot state its subject inside the cap is evidence the seam is
 * wrong.* Then the Fit and the level row — the two figures — and then the argument.
 *
 * The reasons are **not** truncated to make the cap, and neither is anything else: **no fact the
 * card draws is silent**. The card's drawn terms are filtered out of its own reason lines, so a
 * fact drawn and not spoken is a fact a listener is never told at all — which is a worse failure
 * than a long label, and the one the drawn set exists to make impossible in both registers.
 *
 * What meets the cap is therefore what this card **does not draw**: no on-court mark, no balance
 * row, no social tag row, no run of form, no counted-games figure, and a Player Score that is one
 * clause and usually none. Against a competitive Play card that is five registers fewer. The
 * worst case here is still a three-reason label rather than twenty words, and *roughly* is the
 * word §24.3 uses.
 */
export function challengeCardLabel(facts: ChallengeCardFacts): string {
  return sentences([
    facts.person.nickname,
    `Match score ${facts.fit}`,
    levelRow(facts.person),
    ...(facts.distanceKm === undefined ? [] : [`${facts.distanceKm} km away`]),
    ...(facts.person.playerScore === undefined
      ? []
      : [`${PLAYER_SCORE_BLOCK} ${facts.person.playerScore} out of ${PLAYER_SCORE_DENOMINATOR}`]),
    ...(facts.atStake === undefined ? [] : stakeClauses(facts.atStake)),
    ...facts.reasons,
    ...facts.concerns,
  ]);
}

/**
 * Join clauses into one spoken name, dropping the ones that have nothing in them.
 *
 * A merged label is a **list of sentences**, and its two failure modes are a doubled separator
 * where a clause was empty and a trailing one where the last was dropped. Both are silent on
 * screen and audible to the one person the label exists for.
 */
function sentences(clauses: readonly string[]): string {
  const spoken = clauses.filter((clause) => clause !== '');
  return spoken.length === 0 ? '' : `${spoken.join('. ')}.`;
}

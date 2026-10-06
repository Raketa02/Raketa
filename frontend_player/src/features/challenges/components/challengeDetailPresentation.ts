/**
 * What the challenge screen says — **the sentences no other surface writes.**
 *
 * §13's seventeen standing sentences are `challengePresentation.ts`' and are read from here
 * unchanged: this screen states the standing exactly as the row above it does, which is what
 * stops a row and the screen behind it describing one challenge two ways. What is added here is
 * the copy the screen itself brought — the two answers, the fill, the removal and its sheet, the
 * identity row, the two absences, and the one spoken name §24.3 specifies.
 *
 * The split against `challengePresentation.ts` is the one §22 states: that file is the **shared**
 * deck — §13, §14 and §21, read by the inbox row as well as by this screen — and this one is the
 * surface's, holding what no other surface says. `SH.propose`'s strings live there because the
 * court draws that sheet; the removal's live here because the two places that say them — this
 * screen's arm, and the organiser's row on the Chats list, which is a door to it — are both this
 * feature's, and the row says them through the same door the screen does.
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
import { PLAYER_SCORE_BLOCK, metaLine, stakeClauses } from '@/features/play/types';
import { levelRow } from '@/features/games/types';
import type { AppError } from '@/shared/errors';
import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import { formatDistanceKm } from '@/shared/formatting/ratingFormat';

import type { CourtPerson, PairingAbsence, SeatWord } from '../domain/challengeDetail';

import { challengeErrorMessage } from './challengeErrorMessage';
import { THIS_ONE_IS_OVER } from './leaveGamePresentation';

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

// ---------------------------------------------------------------------------
// A half-built court: grow · talk · end
// ---------------------------------------------------------------------------

/**
 * **The fill**, and it is the builder's own act under the challenge screen's own label
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7).
 *
 * §24.3 spells it `⚡ Fill the seats` with *"the ⚡ decorative and hidden, which is the tab bar's
 * own precedent."* **The bolt is not drawn**, and that is the precedent read whole rather than
 * half: [10.2](../../../../docs/design-system.md#102-the-tab-bar) is explicit that *"the ⚡ is
 * `zap` and never the character"* — `U+26A1` carries `Emoji_Presentation=Yes`, so a bare
 * `<Text>⚡</Text>` requests colour-emoji presentation and a `color` style has nothing to apply
 * to. What the bar draws instead is a Feather glyph, and `Button` has no slot for one; adding it
 * is a design-system change this ticket does not make. So the visible label and the spoken name
 * are the same words, and §24.3's *hidden* is discharged by there being no glyph to hide.
 */
export const FILL_THE_SEATS = 'Fill the seats';

/**
 * **The end, while nobody has joined** — *Remove the challenge*, the withdraw as
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4 leaves it: the organiser's, exactly while nobody besides them holds an accepted seat, and
 * nobody's once somebody has ([#428](https://github.com/Raketa02/Raketa/issues/428);
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.3).
 *
 * **The word is the record's** — *remove*, because what the act does to a court nobody has joined
 * is take a send back: nothing anybody agreed to is lost, and the people asked simply stop being
 * asked. Not *withdraw*, which named the same route while it ended courts people had joined and
 * whose words are retired with that reading; not *cancel* or *call off*, which belong to a game;
 * not *stand down*, which the root `CONTEXT.md` owns platform-wide.
 *
 * **One label on the revealed control, on the screen's button and on the sheet's act**, on `Send
 * the challenge`'s and `Leave the game`'s precedent: the act is named once, and what is under the
 * sheet is hidden while it is up, so the first press can only reach the door and the second can
 * only reach the act. The visible label is the whole sentence, so it is the accessible name too —
 * unlike *Withdraw*, which said one word and named what it withdrew to a listener.
 */
export const REMOVE_THE_CHALLENGE = 'Remove the challenge';

/** The removal while it is in flight, on the sheet's act — the list's sheet stays up. §22.3. */
export const REMOVING = 'Removing…';

/**
 * `SH.propose`'s shape, a second time — **the title names the moment rather than the act.**
 *
 * So the act is named exactly once, by {@link REMOVE_THE_CHALLENGE} on the act that carries it
 * out. Focus lands here on the way in and **not** on the first action, because that action is the
 * destructive one and landing focus there would make the worst outcome the cheapest to trigger
 * (§20.6).
 */
export const REMOVE_SHEET_TITLE = 'Before you remove it';

/**
 * **One line, and it is the one ADR-0165 §6 asks for: it is gone for the invitees too.** The
 * consequence the organiser cannot see from their own list — their row goes either way — and the
 * one that reaches other people: somebody deciding on this challenge finds nothing to answer.
 * Reworded on the QA walk ([#429](https://github.com/Raketa02/Raketa/issues/429) E1) so the
 * consequence hangs off the act — *if you remove it, this follows* — rather than being stated of a
 * challenge the sheet has not yet named.
 *
 * Not the withdraw's three. *Everybody who accepted loses this court* is false here by
 * construction, since nobody has; *the conversation goes with it* is true only on the court the
 * organiser is alone in again, and a sentence about a room the reader may never have seen is not
 * what the sheet is for; and *this cannot be undone* is kept off it because what a removal ends
 * is a send, and asking the same people again is a new challenge rather than an undo. **It says
 * nothing about the pair rule releasing**, on the withdraw's own line (§22.3).
 */
export const REMOVE_SHEET_BODY = [
  'If you remove this challenge, it will also disappear for everyone you invited.',
] as const;

/**
 * The sheet's dismissal, **named by what it does** — never just *Close*. The withdraw's own word,
 * because a challenge awaiting answers is exactly what *open* means here.
 */
export const REMOVE_SHEET_CLOSE_LABEL = 'Keep it open';

/**
 * **What the sheet says when the removal is refused** — the two codes a nobody-joined row can
 * meet, each a sentence, over `challengeErrorMessage`'s fallback for everything else
 * (`LEAVE_REFUSED`'s shape, one act over).
 *
 * `somebody_has_joined` is the one a stale row invites: somebody said yes between the read and
 * the press, and the court is nobody's to end for the others any more. `challenge_is_over` is the
 * departure's sentence, borrowed rather than respelled — it is the same fact about the same court,
 * whichever door met it. `court_has_been_a_game` is the third a stale row can meet
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §1): the line-up completed between the read and the press, and such a court is nobody's to end
 * — it ends by its players leaving or by its hour. The route documents two more, and neither
 * reaches this sheet from a row drawn by `mayRemove`: `withdraw_is_the_organisers` needs a reader
 * who is not the organiser, and `challenge_not_found` a seat the reader does not hold — so they
 * fall through to the feature's sentence rather than earning words nobody can reach.
 */
export const REMOVE_REFUSED: Readonly<Record<string, string>> = {
  somebody_has_joined: "Somebody's in now, so it's no longer yours to remove.",
  court_has_been_a_game: "This one became a game, so it's not yours to remove any more.",
  challenge_is_over: THIS_ONE_IS_OVER,
};

/**
 * The sentence a refused removal writes on the sheet: the deck's own where the code has one, and
 * the feature's sentence for every other write otherwise — `account_held`, a connection that was
 * not there, a code this build has never seen.
 */
export function removeRefusalMessage(error: AppError): string {
  const own = error.code === undefined ? undefined : REMOVE_REFUSED[error.code];
  return own ?? challengeErrorMessage(error);
}

// ---------------------------------------------------------------------------
// The ended court
// ---------------------------------------------------------------------------

/**
 * **The heading over the seats of an ended court** — the region a reader is reading, in the
 * `eyebrow` role ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7). *The court*, because that is the glossary's word for the seats and the people in them,
 * and the sentence above it has already said what happened to it.
 */
export const THE_COURT_HEADING = 'The court';

/**
 * **What each person on an ended court did, one word each** — keyed by the domain's code as a
 * `Record`, so a sixth thing a seat can have done fails to compile here rather than drawing a
 * seat with nothing after its name. *Left* is the departure's word and *was still deciding* is
 * the invitee's whom the last departure or the hour closed the court on (ADR-0175 §2) — one word
 * for each thing, the same word the row uses. *Called it off* went with the press (§1).
 */
export const SEAT_WORD: Readonly<Record<SeatWord, string>> = {
  in: 'in',
  left: 'left',
  'said-no': 'said no',
  'ran-out': 'day ran out',
  asked: 'was still deciding',
};

/**
 * `You · in` · `Javier Fabregat · left` · `Oscar Bertran · was still deciding` — one seat of the ended
 * court, drawn and spoken alike: a middot between a name and one word is a join the ear can take
 * as a pause, and the reader's own seat says *You* rather than their name back to them.
 */
export function seatDidLine(who: NamedPlayer, did: SeatWord): string {
  return `${playerName(who)} · ${SEAT_WORD[did]}`;
}

/** What a Player Score is out of, spelled rather than assumed — and spoken, never drawn. */
const PLAYER_SCORE_DENOMINATOR = 100;

/** The segment, and the one place `Score` is written short. See the module note. */
function scoreSegment(playerScore: number): string {
  return `Score ${playerScore}`;
}

export interface IdentityRowFacts {
  readonly person: CourtPerson;
  /**
   * Kilometres to one decimal, spot to spot — the same number every Play surface prints for the
   * same person (ADR-0174 §2). **Absent rather than zero** where the distance term stood down.
   */
  readonly distanceKm?: number;
}

/**
 * `2,71 · Established · likely 2,55–2,87 · 3,1 km · Score 91` — with any segment absent.
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

/**
 * **An invitation a swipe produced says so** — one line under the organiser's card, drawn when
 * the organiser is in the reader's own outgoing list for the challenge's sport
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8).
 *
 * It is the reader's **own act** and nothing else: *why the engine picked them* is what ADR-0143
 * refuses to tell an invitee and this line does not touch it, because Ania saying yes to Karol
 * on Players is a fact she already holds. Client-side, off the same `GET /interest` the deck
 * reads; no code crosses for it. The handle is whole (ADR-0107), and *Players* is the tab's own
 * drawn name, as `HOME_COPY` points at *Play* by its word.
 */
export function saidYesOnPlayersLine(organiserName: string): string {
  return `You said yes to ${organiserName} on Players`;
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
    facts.person.name,
    `Match score ${facts.fit}`,
    levelRow(facts.person),
    ...(facts.distanceKm === undefined ? [] : [`${formatDistanceKm(facts.distanceKm)} away`]),
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

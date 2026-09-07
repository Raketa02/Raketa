/**
 * What a challenge says — five standings read from two sides, and the three sentences about
 * its deadlines.
 *
 * The words are the client's because the code is all that crosses
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §13, §14). They live
 * here rather than in `features/play/` because a challenge outlives the search that made one:
 * the send, the list and the screens that read a standing back are this feature's
 * ([`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md)
 * §8).
 *
 * ## Two sentences per code, and neither is a second state
 *
 * The organiser is asking; an invitee is being asked. One list, one code, and the side is
 * derived from whether the reader holds the organiser seat.
 *
 * **`LINE_UP_INCOMPLETE` carries #221's constraint in its words.** *"The chat opens on the
 * first acceptance and grows with each one"*, which makes it **not a waiting room** — and its
 * obvious phrasing, *waiting for the rest*, is the one that would be false.
 *
 * **`LAPSED` is not a decline**, and the words hold that apart: a day ran out, nobody said no.
 * The `answers challenges` strand needs the denominator, so a lapse that read as a refusal in
 * copy would be a fact quietly restated as a different one.
 *
 * ## An unknown standing
 *
 * There is no arm for one, deliberately: a standing this build cannot read never reaches
 * these functions, and its placement is one of the five where §3 owes a **named gap** rather
 * than a drop — the code *is* the whole line, so `OUT_OF_DATE_GAP` is what the row draws.
 */

import { counted } from '@/shared/formatting/counted';
import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';

import type { ChallengeSide } from '../domain/standing';

/**
 * One standing, with the payload its sentence quotes.
 *
 * A discriminated input rather than `(standing, side, counts)`: three of the five quote a
 * figure or a name, two quote nothing, and a flat signature would let a caller pass a count
 * that belongs to a different standing.
 *
 * **A person is a `NamedPlayer`, never a string.** Two of these sentences name somebody, and
 * ADR-0107's *the whole handle or nobody* is a rule about what may be written — a `name:
 * string` parameter would let a caller shorten a handle on the way in and leave the rule
 * documented rather than held.
 */
export type StandingFacts = { readonly side: ChallengeSide } & (
  | { readonly standing: 'AWAITING_ANSWERS'; readonly awaiting: number }
  | { readonly standing: 'ON' }
  | {
      readonly standing: 'LINE_UP_INCOMPLETE';
      readonly accepted: number;
      readonly awaiting: number;
    }
  | { readonly standing: 'DECLINED'; readonly player: NamedPlayer }
  | { readonly standing: 'LAPSED'; readonly player: NamedPlayer }
);

export function standingLine(facts: StandingFacts): string {
  const organiser = facts.side === 'organiser';

  switch (facts.standing) {
    case 'AWAITING_ANSWERS':
      return organiser
        ? `Waiting on ${counted(facts.awaiting, 'answer', 'answers')}`
        : "They're waiting on you";
    case 'ON':
      return organiser ? "Everybody's in" : "You're in — everybody's in";
    case 'LINE_UP_INCOMPLETE':
      return organiser
        ? `${facts.accepted} in, ${facts.awaiting} still to answer — the chat is already open`
        : `You're in. ${facts.awaiting} still to answer, and the chat is already open`;
    case 'DECLINED':
      return organiser
        ? `${playerName(facts.player)} said no — that seat is open again`
        : 'You said no';
    case 'LAPSED':
      return organiser
        ? `${playerName(facts.player)}'s day ran out — that seat is open again`
        : 'Your day ran out';
  }
}

/**
 * What the pre-send sheet owes: **the irreversibility, and no duration**.
 *
 * *"24 h" is not a string.* Each invited seat carries its own `answer_by`, and a challenge
 * born of a mutual yes has none at all — so one constant stood in for three different
 * sentences, and this is the first of them
 * ([#241](https://github.com/Raketa02/Raketa/issues/241), §14 and §21).
 *
 * **A pre-send sentence naming a duration must name the number the backend will actually
 * derive, or it stops naming one.** There is no `challenges` route the client calls before its
 * first send, `GET /sports` carries the right argument and the wrong home — a per-seat answer
 * window is not a property of squash — and the same screen states the real deadline, per
 * person, from a real timestamp, the moment after the act. So the obligation is discharged by
 * deletion.
 */
export const NOBODY_IS_CONTACTED_YET = 'Nobody is contacted until you send it.';

/**
 * What the pre-send sheet closes with — and it is **not one sentence**.
 *
 * *"Nothing opens until they accept"* is false for doubles: #230 already rewrote the pre-send
 * line for the seat count, and this is the same sentence in its second location. The first
 * acceptance opens the chat, so a doubles sheet promising that nothing opens would be
 * describing a different product.
 */
export function proposeClosing(
  lineUp:
    | { readonly kind: 'singles' }
    | { readonly kind: 'doubles'; readonly sportName: string; readonly stillNeeded: number },
): string {
  if (lineUp.kind === 'singles') return 'Nothing opens until they accept.';
  return (
    `${lineUp.sportName} is doubles — you need ${lineUp.stillNeeded} more. ` +
    'The first person to say yes is in, and you can start talking then.'
  );
}

/**
 * A seat's own deadline, **after** the send — the second of §14's three sentences.
 *
 * `duration` is already formatted: how long is left is read off that seat's `answer_by`
 * against the clock, and a copy deck is not where a clock is read. What this owes is the
 * shape — a person, and the time they have — because the deadline is per seat and nothing
 * about it is a property of the challenge.
 */
export function answerWindowLine(seat: {
  readonly player: NamedPlayer;
  readonly duration: string;
}): string {
  return `${playerName(seat.player)} · ${seat.duration} left`;
}

/**
 * A challenge born of a mutual yes — the third sentence, and it has **no deadline clause**.
 *
 * `ChallengeOpenedFromMutualInterest` carries *"no deadline"* as a distinct event, *"because a
 * nullable `answer_by` is how a later reader invents a deadline that never existed."* The
 * sentence has to be as clear as the event is.
 */
export const MUTUAL_YES = "You both said yes — this one's already on.";

// ---------------------------------------------------------------------------
// The send: the sheet before it, the toast after it, and the two refusals
// ---------------------------------------------------------------------------

/**
 * `SH.propose`'s own title.
 *
 * It names the **moment** rather than the act, so the act is named exactly once — by
 * {@link SEND_CHALLENGE_LABEL}, on the control that opens this sheet and on the control that
 * carries it out. Two spellings of one control is how a screen starts referring to something
 * that is not on it, which is the argument `courtPresentation`'s seat-guard sentence already
 * makes about the swap toggle.
 *
 * Focus lands here on the way in and not on the first action — *"`SH.propose`'s first action is
 * **send**, and landing focus there by default would make the worst outcome the cheapest to
 * trigger"* ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §20.6).
 */
export const PROPOSE_SHEET_TITLE = 'Before you send';

/** The sheet's dismissal, named by what it does — never just *Close*. */
export const PROPOSE_SHEET_CLOSE_LABEL = "Don't send yet";

/** The heading over the handles, whole and one per line. §15: the whole handle, or nobody. */
export const WHO_YOU_ARE_ASKING = "Who you're asking";

/**
 * The act, spelled once and drawn twice: on the court's pinned CTA, and on the sheet that
 * confirms it. The sheet is plainly a confirmation *of that*, which is what one spelling buys.
 */
export const SEND_CHALLENGE_LABEL = 'Send the challenge';

/** The CTA while the send is in flight. Pending is on the pinned control, per #239 §5. */
export const SENDING_LABEL = 'Sending…';

/**
 * **The whole confirmation that the one irreversible act in this feature succeeded.**
 *
 * The send replaces the stack with `[Now]`, which is a placeholder with nothing on it to say a
 * challenge went — so this sentence is not a garnish on a screen that already reports success,
 * it is the report. That is why it is the single **interrupting** announcement in the app
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §20.10).
 *
 * **It promises no notification**, because nothing in this repository can push one: the sentence
 * says how the other side finds out, in the same shape the deck's mutual toast already uses.
 * **Plural-safe** without counting — *they* is right for one invitee and for three, and a count
 * here would be a figure the screen it fires from has already been replaced by.
 */
export const CHALLENGE_SENT = "Challenge sent — they'll see it the next time they open Raketa.";

/**
 * A refused send, first sentence — **the fact, and never the cause.**
 *
 * Four fail-closed gates reach it wearing one sentence, exactly as they reach the withheld row:
 * naming which fired would tell an organiser that a particular person blocked them, was
 * suspended, or changed a safety setting
 * ([ADR-0130](../../../../../docs/adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)).
 * It is written down beside `courtPresentation.ts`'s `WITHHELD_SEAT_LINE` in
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §21 so neither can drift
 * away from the other.
 *
 * **It says *changed*, not *unavailable*.** The fact is that the line-up went out of date; a
 * person's standing is not the organiser's to be told, and *can't be invited now* is a statement
 * about what this app will do rather than a verdict on somebody.
 *
 * **Plural-safe.** A doubles send can lose two seats to one press, so it says *one of these
 * players* — the count is not on the wire either, and counting them would be the payload this
 * refusal refuses to carry.
 */
export const LINE_UP_CHANGED = "Something's changed — one of these players can't be invited now.";

/**
 * The same refusal after the re-read **marked nobody** — the dead end, stated rather than left
 * silent.
 *
 * The send reads profiles live and the read-back reads the index, so the two can disagree — most
 * plausibly on the mutual preference, where the read-back excludes a candidate the partition no
 * longer holds and the send would read them live. *Refused, refreshed, and every seat looks
 * fine* is a screen with nothing on it to act on, so it gets a sentence
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §5.1).
 *
 * **The send is not moved onto the index to close it**: that would buy a rare confusing screen
 * at the price of a safety gate inheriting index staleness, which is the wrong direction on the
 * one class of check that must not be stale.
 */
export const NOTHING_MARKED_AFTER_THE_REFRESH =
  "Something's changed, and one of these players can't be invited right now.";

/**
 * The pair rule's sentence — **the only refusal sentence with a name in it.**
 *
 * The name is **not read off the refusal**: it comes from the player's own challenges, which
 * were always theirs to read, because #222 puts this gate on the *embarrassment* side rather
 * than the safety side. §5.1's rule that a refusal names nobody is about the wire, not about
 * what the screen may end up saying.
 *
 * `name` is §15's `playerName()` — the whole handle, because this is a sentence and a sentence
 * never truncates.
 */
export function openChallengeLine(name: string): string {
  return `You've already got a game waiting with ${name}.`;
}

/**
 * The pair rule **said back with no name in it** — which is what the refusal itself said, and
 * therefore what the court says whenever it has nothing more specific.
 *
 * §21's table has the named sentence and assumes a name is always found. Two states reach this
 * one instead, and they are deliberately not told apart, because the player can act on neither:
 *
 * - **The read has not landed yet.** The refusal is already true and the screen may not sit
 *   silent in front of it, so this is stated first and `openChallengeLine` **replaces** it when
 *   the list names somebody. That is a general statement becoming a specific one, which is the
 *   same shape the gate refusal already has — `LINE_UP_CHANGED` stands while the read-back is
 *   in flight and the seats gain their marks when it lands.
 * - **The game in the way is not one of yours.** The rule binds *every* pair on the court, so
 *   the open challenge can be between two of your invitees — a game that is theirs, on a list
 *   this player has no right to read. There is no name to be had, and inventing the *reason*
 *   there is no name would publish who is missing from whose list.
 *
 * Recorded in [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §21 beside
 * the other three, for the reason that section states about itself: written down together so
 * that none of them can drift away from the rest.
 */
export const A_PAIR_HERE_IS_ALREADY_PLAYING =
  'Two people on this court already have a game between them.';

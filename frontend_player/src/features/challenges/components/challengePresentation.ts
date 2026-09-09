/**
 * What a challenge says — six standings read from two sides, and the four sentences about
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
 * **And it counts open seats, because it can never count answers.** It shipped reading
 * *"{n} in, {m} still to answer"* off an `awaiting` count, and `standing_of` returns
 * `AWAITING_ANSWERS` while **any** seat is still awaiting — so at the rung that yields
 * `LINE_UP_INCOMPLETE` nothing is, `{m}` was structurally zero, and the built line read *"2 in,
 * 0 still to answer"*. It takes `open` instead
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §13,
 * [ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
 * **A field that could only ever be zero is what let the sentence be wrong**, and #221's
 * constraint is untouched: the phrasing that would be false is still *waiting for the rest*.
 *
 * **`LAPSED` is not a decline**, and the words hold that apart: a day ran out, nobody said no.
 * The `answers challenges` strand needs the denominator, so a lapse that read as a refusal in
 * copy would be a fact quietly restated as a different one.
 *
 * **`WITHDRAWN` is neither**, and its word is the record's own
 * ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)).
 * Not *cancel* or *call off*, which are the plan's; not *stand down*, which the root
 * `CONTEXT.md` owns platform-wide for a term that cannot be evaluated. **The invitee who never
 * answered is told the same as the one who accepted** — separating them would say who else was
 * on the court.
 *
 * ## The third reading: an invitee who has left a challenge that has not
 *
 * A padel four where one declines and two accept is `LINE_UP_INCOMPLETE`, and the player who
 * declined still holds a seat — so `GET /challenges` still returns it to them. Keyed on
 * `(standing, side)` alone they would read *"You're in"*, which is false in both clauses. So
 * the invitee's sentence reads **the reader's own seat**, not only their side
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §13.1).
 *
 * The row is not filtered away instead, because the pair rule still binds the reader: a lapsed
 * invitee is unreachable in every sport until this challenge ends, and a row that vanished
 * would take the only available explanation with it. **Neither sentence says how many are in** —
 * they have left, so who is on that court is no longer theirs to be told, and `{m}` is a count
 * of open seats, which is a fact about the arrangement rather than about anybody in it.
 *
 * ## An unknown standing
 *
 * There is no arm for one, deliberately: a standing this build cannot read never reaches
 * these functions, and its placement is one of the five where §3 owes a **named gap** rather
 * than a drop — the code *is* the whole line, so `OUT_OF_DATE_GAP` is what the row draws.
 */

import { counted } from '@/shared/formatting/counted';
import { durationLeft } from '@/shared/formatting/durations';
import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import { standingFactsFor, type Challenge } from '../domain/challenge';
import { HANDLE_SEPARATOR, yourAnswerBy } from '../domain/challengeInbox';
import type { StandingFacts } from '../domain/standing';

export function standingLine(facts: StandingFacts): string {
  const organiser = facts.side === 'organiser';

  switch (facts.standing) {
    case 'AWAITING_ANSWERS':
      return organiser
        ? `Waiting on ${counted(facts.awaiting, 'answer', 'answers')}`
        : "They're waiting on you";
    case 'ON':
      return organiser ? "Everybody's in" : "You're in — everybody's in";
    case 'LINE_UP_INCOMPLETE': {
      const open = counted(facts.open, 'seat open', 'seats open');
      if (organiser) return `${facts.accepted} in, ${open} — the chat is already open`;

      // §13.1. `They are still filling the court` and never a count: a reader who has left is
      // not told who is on it.
      if (facts.ownAnswer === 'DECLINED') return 'You said no. They are still filling the court.';
      if (facts.ownAnswer === 'LAPSED')
        return 'Your day ran out. They are still filling the court.';
      return `You're in. ${open}, and the chat is already open`;
    }
    case 'DECLINED':
      return organiser
        ? `${playerName(facts.player)} said no — that seat is open again`
        : 'You said no';
    case 'LAPSED':
      return organiser
        ? `${playerName(facts.player)}'s day ran out — that seat is open again`
        : 'Your day ran out';
    case 'WITHDRAWN':
      return organiser
        ? 'You withdrew this'
        : `${playerName(facts.player)} withdrew this — that court is closed`;
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
 * **Your own seat, on your own row** — §14's fourth sentence, and the newest of the four.
 *
 * The screen that needed it is new. `{name} · {duration} left` names somebody else and is the
 * **organiser's** sentence, listing each seat and its own clock; until the Chats inbox there
 * was no surface that showed you *your* challenge, so nobody had written the sentence for your
 * own seat. **Naming yourself on your own row would be the app telling you who you are.**
 *
 * It is the row's line whenever the challenge is yours to answer and unanswered — the badge's
 * own predicate, reused, so the badge, the sort and the line cannot disagree
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.2).
 *
 * `duration` is already formatted, for {@link answerWindowLine}'s reason: how long is left is
 * read off `answer_by` against the list's `read_at`, and a copy deck is not where a clock is
 * read. **Draw the clock, never obey it** — this sentence gates no control, and the buttons on
 * the screen behind the row are drawn from the standing the platform sent.
 */
export function yourAnswerWindowLine(duration: string): string {
  return `${duration} left to answer`;
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

// ---------------------------------------------------------------------------
// The Chats inbox: the section's name, the handles a row names, and its one line
// ---------------------------------------------------------------------------

/**
 * The section's own name, and **it carries no count**.
 *
 * `Challenges for you` had to widen: a challenge you *sent* belongs in this list and is drawn
 * nowhere else in the app. Widening breaks the number — `CHALLENGES FOR YOU · 1` agrees exactly
 * with the tab badge, which counts only what is addressed to you — so the count goes and the
 * badge stays the only number on the screen
 * ([#326](https://github.com/Raketa02/Raketa/issues/326) §6).
 *
 * Stored as a word rather than as `CHALLENGES`: the heading is uppercased by 3.3's `eyebrow`
 * role, and a listener should hear a section name rather than a shout.
 */
export const CHALLENGES_HEADING = 'Challenges';

/**
 * The screen a row opens, until [#361](https://github.com/Raketa02/Raketa/issues/361) writes it.
 *
 * A citation rather than filler, which is why it is here and not inlined in the route file: it
 * names what belongs on that screen and admits it is not drawn, which is the whole test a
 * placeholder has to pass — *can a player tell this from a bug*. Held to the same two refusals
 * as every other line in the app: no date is promised, and nothing is said to be empty.
 */
export const CHALLENGE_SCREEN_TITLE = 'Challenge';

export const CHALLENGE_SCREEN_NOT_BUILT =
  'Who asked you, what the game is worth, and your answer — not built yet';

/**
 * The handles this row names, as one line — **whole names, and a count of the ones dropped.**
 *
 * How many fit is `namesThatFit`'s, because it is a rule; what the line looks like is here. The
 * counter says how many people are on that court and not on this line, and it is a bare `+2`
 * rather than a sentence: it sits inside a name list at `cardTitle`, where a clause would read
 * as somebody's handle.
 *
 * **Whoever is dropped is whole on the screen behind the row**, and whole in the row's spoken
 * name — §15's rule is against *inventing* a familiar form, and this invents nothing.
 */
export function handleLine(names: readonly string[], shown: number): string {
  const drawn = names.slice(0, shown);
  const hidden = names.length - drawn.length;

  return hidden === 0 ? drawn.join(HANDLE_SEPARATOR) : `${drawn.join(HANDLE_SEPARATOR)} +${hidden}`;
}

/**
 * **The row's one line, and it has two sources** — chosen by *is this mine to clear*.
 *
 * The time you have left when it is, and §13's standing sentence otherwise
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.2). The
 * choice is the badge's own predicate, so the badge, the sort and this line agree by
 * construction rather than by three implementations remembering the same rule.
 *
 * **The duration folds against the response's `read_at` and never against this phone's clock.**
 * A countdown taken from `Date.now()` drifts out of agreement with the standing the same
 * response folded, which is the one failure that field exists to prevent.
 *
 * A standing this build cannot read draws §3's named gap, because on this row the code **is**
 * the whole line — there is nothing else in the slot for a shorter list to leave behind.
 */
export function challengeRowLine(challenge: Challenge, playerId: string): string {
  const answerBy = yourAnswerBy(challenge, playerId);
  if (answerBy !== undefined) {
    return yourAnswerWindowLine(durationLeft(answerBy, challenge.readAt));
  }

  const facts = standingFactsFor(challenge, playerId);
  return facts === undefined ? OUT_OF_DATE_GAP : standingLine(facts);
}

/**
 * Whether this row draws the urgency stripe — **presence, never magnitude.**
 *
 * Exactly the rows whose line is a duration, which is the same predicate again. There is no
 * stripe on the organiser's row: the clock there is live but it is not theirs to clear, and the
 * stripe marks what the badge counts.
 */
export function rowHasAClockOfYours(challenge: Challenge, playerId: string): boolean {
  return yourAnswerBy(challenge, playerId) !== undefined;
}

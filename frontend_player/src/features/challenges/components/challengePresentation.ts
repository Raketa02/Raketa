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

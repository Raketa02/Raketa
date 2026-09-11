/**
 * The inbox's three rules: **whose turn it is, what a list still holds, and in what order.**
 *
 * `CHALLENGES` on the Chats tab holds every challenge you hold a seat in that is still being
 * arranged — yours and theirs — plus every one that ended recently
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.1). All
 * three questions are things somebody could be **wrong** about, which is why they are here and
 * not in the section that draws them.
 *
 * ## One predicate, read three ways
 *
 * *Is this mine to clear* is the badge's count, the section's sort key and the row's choice of
 * sentence ([#326](https://github.com/Raketa02/Raketa/issues/326) §3), and it is written once
 * so **the badge, the sort and the line agree by construction** rather than by three
 * implementations remembering the same rule. It is deliberately narrow: the organiser is
 * somebody else, your own seat has not answered, and the challenge is live. Nothing else — a
 * number a player cannot get to zero is what makes a badge nag rather than inform.
 *
 * ## An ended challenge is news, and news has a shelf life
 *
 * The wire keeps ended challenges for ever and says so, because *"a list that quietly dropped
 * this morning's lapse would be the same class of lie as a read-back that got shorter."* A
 * screen that drew all of them turns an inbox into an archive. What the row carries is
 * **actionable news** — *{name} said no — that seat is open again* says the pair rule has
 * released and you may send again — so it keeps its place and then leaves.
 *
 * **The wire dates the ending, and the row subtracts it**
 * ([#388](https://github.com/Raketa02/Raketa/issues/388)). `ended_at` is served on the three
 * standings that are endings — exact for a lapse, whose deadline *is* the instant it passed,
 * exact for a withdrawal, which carries the moment somebody decided, and an **upper bound** for
 * a decline, because nothing anywhere records when a person said no. Late rather than early is
 * the right direction: the harm is a player never seeing that a seat reopened, not seeing it a
 * day longer than intended.
 *
 * **What that replaced, and what it fixed.** This used to derive an ending from the latest
 * `answer_by` on the court, which is the most the deadlines can prove. It was right about a
 * lapse and generous about a decline — but a withdrawal is taken on a court where every clock
 * has already stopped ([ADR-0142](../../../../../docs/adr/0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)),
 * so the deadlines said **nothing at all** about when it happened and such a row was kept
 * indefinitely. Over time that row was the archive §1.1 exists to prevent.
 *
 * **`ON` is news here too, and it is the one row the wire does not date.** Everybody is in,
 * nothing about the arrangement can change again, and the game itself lives in Now and in the
 * room the first acceptance opened — so *Everybody's in* is news like the three endings and
 * keeps a row for as long as news is worth keeping. But `ON` is not an **ending**, and
 * `ChallengeSchema.ended_at` says so by being `null` on it: a completed line-up is exactly when
 * two people have a game, which is the opposite of nothing being left. That is the distinction
 * `STILL_BEING_ARRANGED` below is drawn on, one standing wide, and it is why the field is absent
 * here by decision rather than by omission. So the deadline reading survives, scoped to that one
 * standing: every seat accepted means every seat that was asked answered inside its own day, so
 * the latest `answer_by` on the court is an upper bound on the last acceptance — and a
 * mutual-born challenge, `ON` from birth with no deadline anywhere, falls back to when it
 * opened, which is exact.
 */

import { ownSeat, type Challenge, type ChallengeSeat } from './challenge';
import type { Standing } from './standing';

/**
 * How long a finished challenge keeps its row — **24 h, and it is not the conversation's.**
 *
 * A row here is a shelf life on an **inbox**, where the record survives and only the row
 * departs; a conversation's end **destroys an aggregate**
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
 * §7). That the two numbers agree is a coincidence rather than a rule, so this one is spelled
 * here and imported from nowhere.
 */
export const ENDED_ROW_SHELF_LIFE_MS = 24 * 60 * 60 * 1000;

/**
 * **Is this one mine to clear?** — the badge's predicate, and the whole of it.
 *
 * The organiser is somebody else, your own seat has not answered, and the standing is one of
 * the two that still wants an answer. A standing this build cannot read answers **no**: an app
 * that cannot say what a challenge is cannot claim you owe it something.
 */
export function yoursToClear(challenge: Challenge, playerId: string): boolean {
  if (challenge.organiserId === playerId) return false;
  if (challenge.standing !== 'AWAITING_ANSWERS' && challenge.standing !== 'LINE_UP_INCOMPLETE') {
    return false;
  }

  const seat = ownSeat(challenge, playerId);
  return seat !== undefined && seat.answer === undefined;
}

/**
 * How many challenges are waiting on you — the one number on the Chats tab.
 *
 * Counted over the **whole list** rather than over the drawn rows: the badge is chrome read
 * from another tab, and a shelf life is about what an inbox shows rather than about what is
 * owed. The two agree anyway, because nothing that has ended is anybody's to clear.
 */
export function challengesWaiting(challenges: readonly Challenge[], playerId: string): number {
  return challenges.filter((challenge) => yoursToClear(challenge, playerId)).length;
}

/**
 * **When this challenge stopped being arranged** — which is when its row became news, and what
 * the shelf life is measured from. Nothing where the app cannot say.
 *
 * The inverse of `STILL_BEING_ARRANGED` below, dated: two answers, and which one a standing gets
 * is decided by the contract rather than here. The three endings carry `ended_at`; `ON` stopped
 * being arranged when the line-up completed, which the wire does not date, so it is bounded by
 * the court's own deadlines. See the module note for both.
 *
 * It is keyed on the **standing** and never on whether the field happens to be there, so a
 * contract that stopped serving an ending's instant shows up as a row that will not leave
 * rather than as a silent fall back onto the deadlines it was written to replace.
 *
 * `undefined` therefore means one thing where it used to mean two: **the contract claimed an
 * ending and dated none.** That is a broken promise, not a gap in the wire's vocabulary.
 */
export function stoppedBeingArrangedAt(challenge: Challenge): string | undefined {
  if (challenge.standing === 'ON') return completedNoEarlierThan(challenge);
  return challenge.endedAt;
}

/**
 * The last instant the wire can prove a completed line-up completed.
 *
 * The latest deadline on the court, falling back to the moment it opened for a court where
 * nobody was asked — a mutual-born challenge, whose seats are accepted from birth and carry no
 * `answer_by` at all, and which is therefore `ON` the instant it exists.
 */
function completedNoEarlierThan(challenge: Challenge): string {
  return challenge.seats.reduce<string>(
    (latest, seat) =>
      seat.answerBy !== undefined && Date.parse(seat.answerBy) > Date.parse(latest)
        ? seat.answerBy
        : latest,
    challenge.openedAt,
  );
}

/**
 * **The two standings a challenge can still change in** — and the whole of *still being
 * arranged*.
 *
 * The inbox's own question, and deliberately **not** `challengeStands`'. That one is the pair
 * rule's — *does a game still stand between these people* — and it answers **yes** for `ON`,
 * correctly: a completed line-up is exactly when two people have a game. But a completed
 * line-up is not being arranged any more, and a row that counted as *still being arranged* on
 * that reading would never leave the inbox, which is the archive §1.1 exists to prevent.
 *
 * So the two questions are separated at the seam where they disagree, and the disagreement is
 * one standing wide. A `Record` keyed by the union rather than a list, for the reason `ENDED`
 * beside it is one: a seventh standing fails `pnpm typecheck` here rather than quietly
 * counting as one thing or the other.
 */
const STILL_BEING_ARRANGED: Readonly<Record<Standing, boolean>> = {
  AWAITING_ANSWERS: true,
  LINE_UP_INCOMPLETE: true,
  ON: false,
  DECLINED: false,
  LAPSED: false,
  WITHDRAWN: false,
};

/**
 * Whether this row belongs on the inbox at all: still being arranged, or its news still fresh —
 * **and never a challenge the reader themselves said no to.**
 *
 * Two rows stay whatever their age, and it is one rule read twice: **a row the app cannot
 * describe or cannot date is not a row it may decide is finished.** A standing this build cannot
 * read is drawn as the out-of-date gap and keeps its place; so does an ending the contract
 * claimed and did not date.
 *
 * **A no of your own leaves at once**, and that is the shelf life's own argument read from the
 * other side. What the row carries is *news* — a seat reopened, a day run out, a court withdrawn —
 * and it is kept a day so the reader learns something they did not do. A decline is the one
 * departure that is the reader's own act: there is nothing on *You said no* they have to be told,
 * and a court they left going on filling without them is not their news either. So the row goes
 * with the tap, on a singles court it ended and on a doubles court that carries on alike — where
 * the organiser's row for the same no stays its day, because to them it *is* news. A lapse is not
 * a decline: nobody chose it, and *Your day ran out* is kept to be read exactly as before.
 *
 * The record is untouched: `GET /challenges` still holds the seat, the screen still resolves for
 * a stale route, and only the row departs.
 */
export function belongsOnTheInbox(challenge: Challenge, playerId: string): boolean {
  if (ownSeat(challenge, playerId)?.answer === 'DECLINED') return false;
  if (challenge.standing === undefined) return true;
  if (STILL_BEING_ARRANGED[challenge.standing]) return true;

  const stoppedAt = stoppedBeingArrangedAt(challenge);
  if (stoppedAt === undefined) return true;

  return Date.parse(challenge.readAt) - Date.parse(stoppedAt) < ENDED_ROW_SHELF_LIFE_MS;
}

/**
 * **Whose turn it is, then the clock** — the badge's own predicate reused as a sort.
 *
 * Rows you can clear first, least time remaining first; then everything else, newest first. So
 * the thing the badge is counting is the thing at the top of the list, and an ended row keeps
 * its place among the rest rather than being shelved.
 *
 * Newest first is re-derived from `opened_at` rather than inherited from the response's order:
 * the wire promises that order and this half of the sort has to hold for the rows it moves
 * anyway, so reading it off the field is one rule instead of one rule and one assumption.
 *
 * A clearable row with no deadline of its own cannot happen — a seat with no answer was asked,
 * and being asked is what mints an `answer_by` — and it sorts last among its own group rather
 * than first, so an impossible row cannot take the top of the list.
 */
export function inboxOrder(
  challenges: readonly Challenge[],
  playerId: string,
): readonly Challenge[] {
  return [...challenges].sort((a, b) => {
    const mine = yoursToClear(a, playerId);
    if (mine !== yoursToClear(b, playerId)) return mine ? -1 : 1;

    if (mine) return byDeadline(a, b, playerId);
    return Date.parse(b.openedAt) - Date.parse(a.openedAt);
  });
}

/** Least time remaining first, and a row with no deadline of its own after every row with one. */
function byDeadline(a: Challenge, b: Challenge, playerId: string): number {
  const left = ownSeat(a, playerId)?.answerBy;
  const right = ownSeat(b, playerId)?.answerBy;

  if (left === undefined) return right === undefined ? 0 : 1;
  if (right === undefined) return -1;
  return Date.parse(left) - Date.parse(right);
}

/** The section's rows: what still belongs here, in the order the badge implies. */
export function challengeInbox(
  challenges: readonly Challenge[],
  playerId: string,
): readonly Challenge[] {
  return inboxOrder(
    challenges.filter((challenge) => belongsOnTheInbox(challenge, playerId)),
    playerId,
  );
}

/**
 * A seat with somebody in it — **the id is a promise rather than a field that might be there.**
 *
 * The row hashes that id into a poster, so `string | undefined` at the call site is one `?? ''`
 * away from every empty seat in the app sharing one person's face. The narrowing happens once,
 * where the filter that guarantees it is.
 */
export type OccupiedSeat = ChallengeSeat & { readonly playerId: string };

/**
 * Everybody on this court but the reader, in court order — the row's faces and its handles.
 *
 * One rule for both sides: on a challenge you sent it is the people you asked, and on one sent
 * to you it is the organiser and whoever else they asked. An empty seat is nobody and is not in
 * the list, which is the one place a court's *"an empty seat is a seat"* does not apply — a row
 * names people, and a hole is not one.
 */
export function othersOn(challenge: Challenge, playerId: string): readonly OccupiedSeat[] {
  return challenge.seats.filter(
    (seat): seat is OccupiedSeat => seat.playerId !== undefined && seat.playerId !== playerId,
  );
}

/**
 * **How long the reader has left to answer this one**, or nothing where the clock is not theirs.
 *
 * One question with two readers — the row's line and the row's stripe — because the two must
 * agree by construction: a stripe on a row whose line is a standing sentence would be marking
 * a clock that is not there, and a duration with no stripe beside it would be the one urgent row
 * in the list drawn like the rest.
 *
 * It is the badge's predicate plus the deadline the seat carries. A clearable row with no
 * deadline cannot happen — a seat with no answer was asked, and being asked is what mints an
 * `answer_by` — so the absence is a defence rather than a case.
 */
export function yourAnswerBy(challenge: Challenge, playerId: string): string | undefined {
  if (!yoursToClear(challenge, playerId)) return undefined;
  return ownSeat(challenge, playerId)?.answerBy;
}

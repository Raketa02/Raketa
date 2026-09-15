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
 * ([#388](https://github.com/Raketa02/Raketa/issues/388)). `ended_at` is served on the four
 * standings that are endings — exact for a lapse, whose deadline *is* the instant it passed,
 * exact for a withdrawal and for a call-off, which carry the moment somebody acted, and an
 * **upper bound** for a decline, because nothing anywhere records when a person said no. Late
 * rather than early is the right direction: the harm is a player never seeing that a seat
 * reopened, not seeing it a day longer than intended.
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
 * room the first acceptance opened — so *Everybody's in* is news like the four endings and
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

import {
  endingIsTheReadersOwn,
  hasEnded,
  ownSeat,
  standingFactsFor,
  whoEndedIt,
  type Challenge,
  type ChallengeSeat,
} from './challenge';
import { GIVES_UP_THE_SEAT, type SeatAnswer, type Standing } from './standing';

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
 * is decided by the contract rather than here. The four endings carry `ended_at`; `ON` stopped
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
  CALLED_OFF: false,
};

/**
 * **Which of the reader's own answers take the row with them** — a no, and a departure.
 *
 * The shelf life keeps a row a day so the reader learns something they did not do; an act of
 * their own is not that. A decline was the first
 * ([#388](https://github.com/Raketa02/Raketa/issues/388)) and a departure is the second
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §6): *an own left is the reader's own act in the same sense*. A lapse is **not** one — nobody
 * chose it, and *Your day ran out* is kept to be read — and an accepted seat has not left at all.
 *
 * A `Record` keyed by the union rather than a pair of `===`, for `GIVES_UP_THE_SEAT`'s reason: a
 * fifth answer fails `pnpm typecheck` here rather than quietly keeping a row whose reader walked
 * out of it. **Deliberately not that table**, though it differs from it in one cell: that one
 * asks whether a seat is open, this one asks whose act opened it, and the lapse is exactly where
 * the two questions part.
 */
const OWN_ACT_LEAVES_AT_ONCE: Readonly<Record<SeatAnswer, boolean>> = {
  ACCEPTED: false,
  DECLINED: true,
  LAPSED: false,
  LEFT: true,
};

/**
 * Whether this row belongs on the inbox at all: still being arranged, or its news still fresh —
 * **and never a challenge the reader themselves said no to, walked out of, or removed.**
 *
 * Two rows stay whatever their age, and it is one rule read twice: **a row the app cannot
 * describe or cannot date is not a row it may decide is finished.** A standing this build cannot
 * read is drawn as the out-of-date gap and keeps its place; so does an ending the contract
 * claimed and did not date.
 *
 * **A no of your own leaves at once, and so does a departure**, and that is the shelf life's own
 * argument read from the other side. What the row carries is *news* — a seat reopened, a day run
 * out, a court withdrawn — and it is kept a day so the reader learns something they did not do.
 * A decline and a departure are the two ways out that are the reader's own act: there is nothing
 * on *You said no* or *You left* they have to be told, and a court they left going on filling
 * without them is not their news either. So the row goes with the tap, on a singles court it
 * ended and on a doubles court that carries on alike — where the others' row for the same act
 * stays its day, because to them it *is* news. A lapse is not either: nobody chose it, and *Your
 * day ran out* is kept to be read exactly as before ({@link OWN_ACT_LEAVES_AT_ONCE}).
 *
 * **And so does a removal of your own** ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4, [#428](https://github.com/Raketa02/Raketa/issues/428)), which is not a seat's answer and so
 * is read off the standing: a `WITHDRAWN` challenge the reader organised
 * ({@link removedByTheReader}). It is theirs by construction — since ADR-0172 §1 `WITHDRAWN` is
 * *Remove the challenge*'s alone, the organiser's while nobody has joined — so *You withdrew
 * this* is the third sentence that tells the reader nothing; to the people asked it is news, and
 * their row keeps its day.
 *
 * **A court called off is not one of those, whoever's act it was**
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7). To the one left on it by the last departure and to everybody the button ended it for, it
 * is news and keeps its day; the last leaver's own row goes at once as every own *left* does.
 * **The presser's own row stays its day** too: *You called the game off* is their own act, but
 * the row is the one place the others' court is still shown to them with every seat's word
 * behind it, and a person who ended a game for three others is owed the same day's record the
 * others get. **The rule that dropped the row of a court ended by somebody else's departure is
 * retired** — it existed because the only sentence was *? said no*, and the sentence exists now.
 *
 * The record is untouched: `GET /challenges` still holds the seat, the screen still resolves for
 * a stale route, and only the row departs.
 */
export function belongsOnTheInbox(challenge: Challenge, playerId: string): boolean {
  const ownAnswer = ownSeat(challenge, playerId)?.answer;
  if (ownAnswer !== undefined && OWN_ACT_LEAVES_AT_ONCE[ownAnswer]) return false;
  if (removedByTheReader(challenge, playerId)) return false;
  if (challenge.standing === undefined) return true;
  if (STILL_BEING_ARRANGED[challenge.standing]) return true;

  const stoppedAt = stoppedBeingArrangedAt(challenge);
  if (stoppedAt === undefined) return true;

  return Date.parse(challenge.readAt) - Date.parse(stoppedAt) < ENDED_ROW_SHELF_LIFE_MS;
}

/**
 * **A removal of the reader's own** — `WITHDRAWN`, organised by them. Since ADR-0172 §1 the
 * standing is *Remove the challenge*'s alone, and a removal is the organiser's alone, so the
 * organiser seat is the whole of the test: `ended_by` names them too, and is not needed to.
 */
function removedByTheReader(challenge: Challenge, playerId: string): boolean {
  return challenge.standing === 'WITHDRAWN' && challenge.organiserId === playerId;
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
 * Who the row draws, in court order — the row's faces and its handles.
 *
 * An empty seat is nobody and is not in the list, which is the one place a court's *"an empty
 * seat is a seat"* does not apply — a row names people, and a hole is not one. The reader is
 * never in it: naming yourself on your own row would be the app telling you who you are.
 *
 * **A court still being filled names the people still on it.** A seat that has been given up —
 * a no, a day run out, a yes taken back — keeps its occupant on the wire, because the record
 * says who was asked; but a row is *who you would play with*, and two faces of people who said
 * no under a line reading *2 in, 2 seats open* drew a four that was a two
 * ([#429](https://github.com/Raketa02/Raketa/issues/429)). A seat still deciding stays: they
 * were asked and have not said no.
 *
 * **An ended row names who the sentence names** — one rule for the whole shelf
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7): `ended_by`'s face and name, and no other. A doubles *said no* row goes from three faces
 * to one and the tap answers *which court*; the faces that left one by one never come back on
 * the row that ends it; and an ended row is never blank, which is the failure the previous rule
 * — *an ended court names everybody it asked* — was written against and the one before it had.
 * Where the sentence is about the **reader's own act** — *Your day ran out*, *You called the
 * game off* — it names nobody else, so the row draws the people still on the court: the seats
 * not given up, which is the filling rule read once more, and on an ended court is never empty
 * (whoever ended it left somebody on it, or is on it themselves).
 *
 * A completed line-up and a standing this build cannot read name everybody but the reader, as
 * before: neither is being filled, and neither has ended.
 */
export function othersOn(challenge: Challenge, playerId: string): readonly OccupiedSeat[] {
  const facts = standingFactsFor(challenge, playerId);
  const ended = facts !== undefined && hasEnded(facts);
  const aboutTheReader = ended && endingIsTheReadersOwn(facts);

  if (ended && !aboutTheReader) {
    const seat = whoEndedIt(challenge);
    if (seat !== undefined && occupied(seat)) return [seat];
    // The wire named nobody, or somebody who holds no seat — a promise broken, not a row to
    // leave blank: everybody the court asked, which is what the row drew before it could name.
  }

  const stillOnIt = facts !== undefined && (STILL_BEING_ARRANGED[facts.standing] || aboutTheReader);

  return challenge.seats.filter(
    (seat): seat is OccupiedSeat =>
      occupied(seat) &&
      seat.playerId !== playerId &&
      !(stillOnIt && seat.answer !== undefined && GIVES_UP_THE_SEAT[seat.answer]),
  );
}

function occupied(seat: ChallengeSeat): seat is OccupiedSeat {
  return seat.playerId !== undefined;
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

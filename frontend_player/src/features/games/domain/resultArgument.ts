/**
 * **What a player may do about a result, and what the screen is therefore drawing.**
 *
 * One route takes three acts and the record decides which — *"a client that named which would be
 * a client that could name it wrongly, and a mislabelled correction is a proposal nobody may
 * make"*. So nothing here chooses a request. What it chooses is a **screen**, and the ticket
 * names why that matters: a correction and a counter are the same `POST` and completely
 * different news, and *"a player will spend an attempt fixing a typo"* unless the difference is
 * visible before the tap.
 *
 * Eight states, folded from the standing, the scores on the table, whether anybody has agreed,
 * and which seat is yours.
 *
 * | Standing | On the table | The screen |
 * | --- | --- | --- |
 * | `AWAITING_ENTRY` | — | the entry, and when it stops being sayable |
 * | `NEVER_PLAYED` | — | a ghost: nothing to do, and nobody marked for it |
 * | `CALLED_OFF` | — | the fourth end (ADR-0163): somebody ended it — a departure or a press, and the screen says who (ADR-0172) — and nobody is marked for it |
 * | `AWAITING_ANSWER` | your score | free correction, and the hour silence agrees |
 * | `AWAITING_ANSWER` | their score | agree, or disagree **with a score** |
 * | `AWAITING_ANSWER` | both scores | both of them, and the agreement that ends the argument |
 * | `AWAITING_ANSWER` | an agreement | who agreed, when it settles, and what is left to do |
 * | `CONFIRMED` | — | the agreed score, and what it said about you |
 * | `UNSCORED` | — | an evening, not evidence |
 * | `STARTED_SHORT` | — | a booked game whose hour came with a seat open: no result |
 * | `NO_SHOW_REPORTED` | a report | who was marked as not coming, and the dispute for them (#560) |
 * | `NO_SHOW` | — | who did not come: the reports nobody disputed (#560) |
 *
 * ## Which of the three is read off the count, and never off an absence
 *
 * `proposals` carries nought, one or two, and **the count is the state**: nothing on the table,
 * one score waiting on the other side, or the disagreement. The field it replaced was absent for
 * *nothing entered* and for *both sides have spoken* alike, which is two opposite things in one
 * spelling ([#317](https://github.com/Raketa02/Raketa/issues/317)) — so the standing had to tell
 * them apart, and now it only says the argument is still live at all.
 *
 * ## An agreement is a **state**, and not a flag riding on three of them
 *
 * Somebody agreeing settles nothing for the length of the grace, and the standing goes on
 * reading `AWAITING_ANSWER` throughout — but everything a screen says about the game changes:
 * two of the acts stop being legal, and **both were being offered because nothing on the wire
 * said anybody had answered.** A correction is refused with `the_other_side_has_answered`, and a
 * second agreement from the same side with `the_result_is_already_accepted`.
 *
 * So it is `agreed`, an arm of its own, rather than an optional field on the three states it can
 * happen in. Carried as a field it was a state every renderer had to remember to pre-empt its
 * own `switch` with, and the one that forgot said something false — which is how the body came
 * to promise *anybody can still put a different score up* over a disagreement in which each side
 * had already used its one turn.
 *
 * It **keeps both proposals**, because what is left to do is read off them and off nothing else:
 * inside the grace a counter still beats an agreement — the whole reason the grace exists — and
 * the side that may make one is the side that has not spoken. Two scores standing means neither
 * can, which is the aggregate's one-per-side cap rather than a rule invented here.
 *
 * ## Somebody did each of these things, and two of the eight say who
 *
 * A seat carries a handle ([ADR-0141](../../../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)),
 * so *the other side put a score up* and *the other side agreed* can name the person they are
 * about. Two states and no more: an entry, a correction and a disagreement are acts of a
 * **side** — a score is one side's claim and the aggregate caps it per side, not per person —
 * and naming whoever typed one would attribute a side's turn to a teammate.
 *
 * Whoever a sentence names is a {@link NamedPlayer} rather than a string, on
 * `challengePresentation`'s precedent: *you*, *a player*, and a seat the record can no longer
 * describe are three cases, and a formatter taking an optional handle would let the third read
 * as the second with an empty name.
 *
 * **Nothing here folds a standing.** The standing is *derived from the record and the clock*,
 * and `read_at` is what every duration on these screens is measured from; a client that decided
 * *the grace has passed* would be the second place that answer lives.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import {
  openSeats,
  type Acceptance,
  type CalledOffBy,
  type Game,
  type NoShowReport,
  type Score,
  type StandingProposal,
} from './game';
import type { GameSide, Outcome } from './vocabulary';

/**
 * The one act a screen state offers, in the order the screen draws them. **`dispute` is not about
 * a score** — it is *I was there*, the reported player's answer to a no-show report (#560) — and
 * marking somebody as not coming is not here either: it is an act per person, offered beside the
 * entry rather than instead of it (`noShowRows` in `noShows.ts`).
 */
export type ResultAct = 'enter' | 'correct' | 'accept' | 'counter' | 'dispute';

/**
 * **What an entry arm leads with** — the plan while it is being agreed, the score once the moment
 * is here.
 *
 * `AWAITING_ENTRY` is one standing and
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.2 lands two
 * different cards on two different things inside it: *Planning* and *Game on* arrive at **the
 * Planning arm**, and *Needs result* arrives at **the score grid**. What tells them apart is the
 * four-rung ladder, which reads a **plan** — and this feature may never learn one
 * exists (ADR-0149 §1). So the fold happens in `features/plans`, where the ladder lives and where
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.3 says
 * *"every surface reads it — the rail, the card, the gloss, and the game screen's arm"*, and what
 * crosses is **this** — a word about what the screen leads with, in this feature's own vocabulary
 * rather than a rung in somebody else's.
 *
 * **It changes what leads and never what is offered.** *We played* is available in every entry arm
 * — `standing_of` gates entry on `entry_closes_at` and on nothing else, so four people can arrange
 * a game at six and play it at eight without ever filling a slot — so on the plan lead the grid is
 * a press away rather than absent.
 */
export type EntryLead = 'the-plan' | 'the-score';

/**
 * The three acts that open a grid. **At most one of them is ever offered at once**, which is
 * what lets {@link editingAct} read the answer off {@link actsOffered} instead of restating it.
 */
export type EditingAct = Exclude<ResultAct, 'accept' | 'dispute'>;

/** The two scores on the table, **from the reader's side of the net**. Either may be absent. */
export interface ScoresOnTable {
  readonly ours?: StandingProposal;
  readonly theirs?: StandingProposal;
}

/**
 * An agreement that has not settled yet, **from the reader's side of the net**.
 *
 * The wire names the side whose score was agreed with. Which of the two people that is news for
 * is the same join this file does for a proposal, done once here so that no screen repeats it:
 * *they agreed with your score* and *your side agreed with theirs* are the two sentences, and
 * they are opposite halves of one fact.
 */
export interface StandingAgreement {
  /** Whose score was agreed with. */
  readonly with: 'ours' | 'theirs';
  /** Who agreed. **You**, on your own side's agreement in a doubles game, or the person. */
  readonly by: NamedPlayer;
  /** When it becomes the result — measured from the **score**, never from anybody's tap. */
  readonly settlesAt: string;
}

export type ResultArgument =
  /** No seat of this game is yours. The client half of `you_were_not_on_this_court`. */
  | { readonly kind: 'not-yours' }
  /**
   * A state this build has no word for. It draws `OUT_OF_DATE_GAP` and offers nothing: acting
   * on a game whose state we cannot name is how a correction becomes a second proposal.
   *
   * **Two ways in.** A standing this build cannot read, which is the ordinary one and the reason
   * old builds live on real phones for months. And an answer awaited with **nothing on the
   * table**, which the aggregate cannot produce and the standing's own fold states rather than
   * leaves to a `max()` over an empty sequence — a client that read it as a disagreement would
   * offer an agreement with a score nobody put up.
   */
  | { readonly kind: 'unreadable' }
  /**
   * Nobody has said it happened. **`seatOpen` is whether somebody left and nobody has filled
   * the seat** (ADR-0162): the entry is withheld while it is true, because the server refuses a
   * result on a short court and a game with a gap in it is not one anybody could have played.
   */
  | { readonly kind: 'awaiting-entry'; readonly entryClosesAt?: string; readonly seatOpen: boolean }
  | { readonly kind: 'never-played' }
  /**
   * Called off while a seat was open — an ending like the ghost's with nobody marked.
   * **`ending` says how it ended, and by whom where anybody's act did**
   * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §4, §8; [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
   * §3): the departure that emptied the court, named, or the hour that found it still short of
   * a player, which names nobody by design.
   */
  | { readonly kind: 'called-off'; readonly ending: CalledOffEnding }
  | { readonly kind: 'ours-stands'; readonly proposal: StandingProposal }
  /** `by` is whoever on the other side put it up — the one person a screen here can name. */
  | {
      readonly kind: 'theirs-stands';
      readonly proposal: StandingProposal;
      readonly by: NamedPlayer;
    }
  | {
      readonly kind: 'both-stand';
      readonly ours: StandingProposal;
      readonly theirs: StandingProposal;
    }
  /**
   * Somebody has agreed and the grace has not run out. **It replaces whichever of the three it
   * happened in**, and keeps their scores: what is still legal here is read off which of them
   * stands, and every sentence off which side agreed.
   */
  | ({ readonly kind: 'agreed'; readonly agreement: StandingAgreement } & ScoresOnTable)
  | { readonly kind: 'confirmed'; readonly score?: Score; readonly outcome?: Outcome }
  | { readonly kind: 'unscored' }
  /** A booked game whose hour came with a seat still open: it takes no result (#544). */
  | { readonly kind: 'started-short' }
  /**
   * **Somebody was marked as not coming, and a report's day still runs** (#560; the mechanics
   * §15.3). The reader's own mark where one names them — whose `open` day is the one act this arm
   * offers, *I was there* — and everybody else's, in the court's order.
   */
  | {
      readonly kind: 'no-show-reported';
      readonly yours?: NoShowMark;
      readonly others: readonly NoShowMark[];
    }
  /**
   * **Every report has had its day, and one stood**: the game does not count. `didNotCome` is the
   * reports nobody disputed — a disputed one fell, and is on nobody's record.
   */
  | { readonly kind: 'no-show'; readonly didNotCome: readonly NamedPlayer[] };

/**
 * **One no-show report, from the reader's side** — who it marks and where it stands. *Mark* is the
 * glossary's own verb for it: the players who came marking one who didn't.
 */
export interface NoShowMark {
  /** *You* on the reader's own, the whole name, or `?` where `users` lost them. */
  readonly who: NamedPlayer;
  /** The end of their day to say they came — the backend's instant. */
  readonly disputeBy: string;
  /**
   * `open` — undisputed, its day not over when the list was read: it may still be disputed.
   * `disputed` — they said they came, and the report fell. `stood` — undisputed, its day over.
   */
  readonly state: 'open' | 'disputed' | 'stood';
}

/**
 * **How a game was called off, and by whom** — the game screen's heading and body are keyed on it.
 *
 * Two ways and no third since ADR-0175 §1: a **departure** that emptied the court, whose leaver
 * the wire names, and **the hour**, which found the court still short of a player when its
 * moment passed and names nobody. `format` is the court's size, because the body says *the
 * singles game* or *the doubles game* — the one sentence on the screen that names the shape.
 * Nobody presses a call-off any more; a record written while somebody could still folds, as a
 * departure by the person it names.
 */
export type CalledOffEnding =
  | {
      readonly how: 'departure';
      /** Who left — `you` for the reader's own, the whole name, or `?` where `users` lost them. */
      readonly by: NamedPlayer;
      readonly format: 'singles' | 'doubles';
    }
  | { readonly how: 'the-hour'; readonly format: 'singles' | 'doubles' };

/**
 * Which side of the net is yours — **a join, not a rule.**
 *
 * `SeatingSchema` carries a side, a player id and a handle and states no `Relationship`, unlike
 * the arrangements a builder reads, so the answer is a lookup of your own id in a frozen court.
 * `undefined` when no seat is yours, which the list cannot produce and a link can.
 */
export function sideOf(game: Game, playerId: string): GameSide | undefined {
  return game.seats.find((seat) => seat.playerId === playerId)?.side;
}

/**
 * Who somebody on this court is, **in the reader's own terms** — the one join that turns an id
 * on this contract into somebody a sentence can name.
 *
 * *You* for the reader themselves, because a player reading their own handle in a row about
 * them is the one place the whole handle is the wrong word. The unknown player's `?` for a seat
 * `users` can no longer answer for, and for an id that holds no seat at all — the second is
 * unreachable from a game's own fields and is answered rather than thrown, on the rule the
 * court draws by: a seat is never emptied.
 */
export function whoIs(game: Game, reader: string, playerId: string): NamedPlayer {
  if (playerId === reader) return { kind: 'you' };
  const name = game.seats.find((seat) => seat.playerId === playerId)?.name;
  return name === undefined ? { kind: 'unknown' } : { kind: 'player', name };
}

/**
 * Everybody on this court but you, **in the order the challenge handed it over.**
 *
 * The court's order and never a re-sort: which side was short is part of what a court is, and a
 * list re-ordered here would say a different thing about the same evening on two screens.
 *
 * **An open seat holds nobody**, so it is not in a list of people: a sentence *with X and Y*
 * about a court somebody left names the ones still on it, and never a `?` for the gap.
 */
export function othersOn(game: Game, reader: string): readonly NamedPlayer[] {
  return game.seats.flatMap((seat) =>
    seat.playerId === undefined || seat.playerId === reader
      ? []
      : [whoIs(game, reader, seat.playerId)],
  );
}

/**
 * The fourth end, as the screen names it: the hour where the wire named nobody, and otherwise
 * the departure — who, told from the reader — and the court's shape, told off its size.
 */
function calledOffEnding(game: Game, reader: string): CalledOffEnding {
  const format = game.seats.length <= SINGLES_SEATS ? 'singles' : 'doubles';
  if (game.calledOffBy === undefined) return { how: 'the-hour', format };
  return { how: 'departure', by: namedFrom(game.calledOffBy, reader), format };
}

/**
 * `whoIs`'s three answers, off a field that carries its own name rather than off a seat — a
 * leaver's seat is vacated (ADR-0172 §4), and a no-show report names its player whole (#560).
 */
function namedFrom(subject: CalledOffBy | NoShowReport, reader: string): NamedPlayer {
  if (subject.playerId === reader) return { kind: 'you' };
  if (subject.name === undefined) return { kind: 'unknown' };
  return { kind: 'player', name: subject.name };
}

/** How many seats a singles court has — two, and the boundary between the two words. */
const SINGLES_SEATS = 2;

/**
 * Everybody on your side but you, and everybody across the net — **as counts.**
 *
 * Counts and not people even though a seat carries a handle: its readers are the singles/doubles
 * sentence and the two score-column labels, and both are statements about a **side**. Who is on
 * the court by name is {@link othersOn}.
 */
export function courtSizes(game: Game, side: GameSide) {
  const ours = game.seats.filter((seat) => seat.side === side).length;
  return { ours, theirs: game.seats.length - ours };
}

/** What this game is asking of this player, right now. */
export function resultArgument(game: Game, playerId: string): ResultArgument {
  const side = sideOf(game, playerId);
  if (side === undefined) return { kind: 'not-yours' };

  if (game.standing === undefined) return { kind: 'unreadable' };

  switch (game.standing) {
    case 'AWAITING_ENTRY':
      return {
        kind: 'awaiting-entry',
        entryClosesAt: game.entryClosesAt,
        seatOpen: openSeats(game.seats).length > 0,
      };
    case 'NEVER_PLAYED':
      return { kind: 'never-played' };
    case 'CALLED_OFF':
      return { kind: 'called-off', ending: calledOffEnding(game, playerId) };
    case 'CONFIRMED':
      return { kind: 'confirmed', score: game.score, outcome: game.outcome };
    case 'UNSCORED':
      return { kind: 'unscored' };
    case 'STARTED_SHORT':
      return { kind: 'started-short' };
    case 'NO_SHOW_REPORTED':
      return noShowReported(game, playerId);
    case 'NO_SHOW':
      return {
        kind: 'no-show',
        didNotCome: game.noShows.flatMap((report) =>
          report.disputedAt === undefined ? [namedFrom(report, playerId)] : [],
        ),
      };
    case 'AWAITING_ANSWER': {
      const ours = game.proposals.find((one) => one.side === side);
      const theirs = game.proposals.find((one) => one.side !== side);
      const agreement = agreementFrom(game, playerId, side);

      if (ours === undefined) {
        // An answer awaited with nothing on the table at all — the case the standing's own fold
        // states rather than leaves to a `max()` over an empty sequence, and the aggregate
        // cannot produce it.
        if (theirs === undefined) return { kind: 'unreadable' };
        return agreement === undefined
          ? {
              kind: 'theirs-stands',
              proposal: theirs,
              by: whoIs(game, playerId, theirs.proposedBy),
            }
          : { kind: 'agreed', agreement, theirs };
      }
      if (agreement !== undefined) return { kind: 'agreed', agreement, ours, theirs };
      return theirs === undefined
        ? { kind: 'ours-stands', proposal: ours }
        : { kind: 'both-stand', ours, theirs };
    }
  }
}

/** The reader's own mark, and everybody else's, while a report's day still runs. */
function noShowReported(game: Game, playerId: string): ResultArgument {
  const marks = game.noShows.map((report) => ({
    playerId: report.playerId,
    mark: markOf(report, playerId, game.readAt),
  }));
  const yours = marks.find((one) => one.playerId === playerId)?.mark;
  return {
    kind: 'no-show-reported',
    ...(yours === undefined ? {} : { yours }),
    others: marks.flatMap((one) => (one.playerId === playerId ? [] : [one.mark])),
  };
}

/**
 * A report in the reader's terms. **Whether its day is still open** is read off two of the
 * backend's own instants — the report's `disputeBy` and the list's `readAt` — and never off this
 * phone's clock: it is the server's `may_dispute`, asked of the moment the list was folded.
 */
function markOf(report: NoShowReport, reader: string, readAt: string): NoShowMark {
  const state =
    report.disputedAt !== undefined
      ? 'disputed'
      : Date.parse(readAt) < Date.parse(report.disputeBy)
        ? 'open'
        : 'stood';
  return { who: namedFrom(report, reader), disputeBy: report.disputeBy, state };
}

/** An agreement in the reader's own terms, and `undefined` where none stands. */
function agreementFrom(
  game: Game,
  playerId: string,
  side: GameSide,
): StandingAgreement | undefined {
  const acceptance: Acceptance | undefined = game.acceptance;
  if (acceptance === undefined) return undefined;
  return {
    with: acceptance.ofSide === side ? 'ours' : 'theirs',
    by: whoIs(game, playerId, acceptance.agreedBy),
    settlesAt: acceptance.settlesAt,
  };
}

/**
 * The scores on the table, **from this side of the net** — and either may be absent.
 *
 * The controls hang off these two rather than off the state's name: an agreement is with
 * `theirs`, a correction is of `ours`, and a counter answers `theirs` with a score of our own.
 * Folding it here is what keeps the screen from restating which arms carry which score.
 */
export function scoresOnTable(argument: ResultArgument): ScoresOnTable {
  switch (argument.kind) {
    case 'ours-stands':
      return { ours: argument.proposal };
    case 'theirs-stands':
      return { theirs: argument.proposal };
    case 'both-stand':
    case 'agreed':
      return { ours: argument.ours, theirs: argument.theirs };
    default:
      return {};
  }
}

/**
 * Which act a grid opened on this state would send — **`undefined` where no grid may open.**
 *
 * The screen never names the act on the request, and it does have to name it in two places a
 * player reads: the send's own word, and whether opening the grid is *entering* or *answering*.
 * That is a rule about the state rather than about the screen, so it lives here beside the one
 * that says which controls exist at all.
 *
 * **Read off {@link actsOffered}**, because at most one of the three ever stands beside the
 * agreement — so the two cannot disagree about a state, and the rule that an agreement takes the
 * correction away is written once.
 */
export function editingAct(argument: ResultArgument): EditingAct | undefined {
  return actsOffered(argument).find(
    (act): act is EditingAct => act !== 'accept' && act !== 'dispute',
  );
}

/**
 * The acts this state offers, **in the order the screen draws them**.
 *
 * `accept` leads `counter` because agreeing is the ordinary answer and disagreeing is the one
 * that has to carry a score — and because *"there is no bare rejection"* means the second
 * control is never the cheap one.
 */
export function actsOffered(argument: ResultArgument): readonly ResultAct[] {
  switch (argument.kind) {
    case 'awaiting-entry':
      // *We played* is withheld while a seat is open (#411 rule 5): the seat stays open until it
      // is filled, the game is called off, or the window closes into *Never played*.
      return argument.seatOpen ? [] : ['enter'];
    case 'ours-stands':
      return ['correct'];
    case 'theirs-stands':
      return ['accept', 'counter'];
    case 'both-stand':
      // Either side may agree with the other's, and that is the only end short of the game going
      // unscored. Never a counter — this side has had its one turn, which is what bounds the
      // argument to two rounds.
      return ['accept'];
    case 'agreed':
      // Correcting is refused with `the_other_side_has_answered` and a second agreement with
      // `the_result_is_already_accepted`, so both controls go. What is left is the disagreement,
      // and only the side that has not spoken may make one — two scores standing means neither
      // can, which is the aggregate's cap rather than a rule invented here.
      return argument.ours === undefined ? ['counter'] : [];
    case 'no-show-reported':
      // *I was there* — the reported player's alone, inside their own day (#560). Nobody else
      // answers a report: the platform does not arbitrate, and a dispute falls the report whole.
      return argument.yours?.state === 'open' ? ['dispute'] : [];
    case 'not-yours':
    case 'unreadable':
    case 'never-played':
    case 'called-off':
    case 'confirmed':
    case 'unscored':
    case 'started-short':
    case 'no-show':
      return [];
  }
}

/**
 * **Every sentence these screens say.** Nothing the games contract sends is prose.
 *
 * A `GameStanding`, a `GameKind` and an `Outcome` are codes and the words for them are the
 * client's
 * ([ADR-0022](../../../../../docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so
 * this file is the feature's copy deck and the components are assembled from it — the same
 * shape
 * `features/play/components/*Presentation.ts` takes, and for the same reason:
 * *code → message, never message → message*, and **a sentence is never a template inlined in a
 * component**.
 *
 * ## Four sentences carry unusual weight, and the ticket names all four
 *
 * - **Silence confirming has to be visible before it happens**, or silence is a trap rather
 *   than a default. So the standing line of a game with a score on the table *always* names the
 *   duration and what happens at the end of it, on the row as well as on the screen — it is not
 *   a footnote a player reaches by tapping.
 * - **An unscored game reads as an evening, not an error.** Nothing about it is a failure and
 *   nobody is at fault: it says these people played, it is in the count of how much somebody has
 *   played, and it moves nobody's Level. There is no red, no *could not*, and no *unfortunately*.
 * - **A correction is not a second proposal**, and the screen says which one it is offering
 *   before the tap. *"A player will spend an attempt fixing a typo"* is the failure this whole
 *   deck exists to prevent.
 * - **Nobody is penalised for any of it** — ADR-0049, carried whole by
 *   [ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) §5.
 *   Not the silent loser, not the four who all went home, not the
 *   side whose counter went unaccepted. Every sentence here that could be read as a reproach
 *   says so out loud.
 *
 * ## A person is named where a person acted, and a side where a side did
 *
 * A seat carries a handle
 * ([ADR-0141](../../../../../docs/adr/0141-a-game-names-its-court-and-the-court-is-the-gate.md)),
 * and the split is not a matter of taste. **A score is a side's claim** — the aggregate caps one
 * per side and either side may agree with the other's — so the two columns of every score here
 * stay *Your side* and *Their side*, and naming whoever typed one would charge a side's single
 * turn to a teammate. **Agreeing and putting a score up are things a person did**, and those two
 * sentences say who.
 *
 * The handle is drawn **whole** wherever it appears — these are sentences, and
 * [ADR-0107](../../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4
 * forbids deriving a familiar form from one. `playerName()` is the single formatter, and it is
 * what draws the `?` for a seat `users` can no longer answer for.
 *
 * ## The words are the prototype's where the prototype had them
 *
 * `prototype/result-confirmation`'s variant C is this screen, and its copy is prior art rather
 * than a first draft: **propose a modification** is the product's word for a counter and *dispute*
 * is not, the entry's send is *send this score*, and a correction is *change what I entered* —
 * which says, in the control's own name, the thing the ticket says a player must not have to
 * learn the hard way. What is rewritten is only what the model moved: there are no absolute
 * times here because this platform has no calendar. The prototype's names came **back** — a seat
 * carries a handle now — under the rule two sections up, which is narrower than the prototype's:
 * a person where a person acted, a side where a side did.
 *
 * ## A score is never printed as a string
 *
 * `6-4 3-6 6-2` is not a score until you know whose 6 it is, and in a doubles game with four
 * people and two sides an unlabelled one is unusable. So every score on these screens is drawn
 * as a **table with both sides named**, and what this file writes is the spoken form of it —
 * which is the same fact in the register a listener gets.
 */

import { YOU_MARK } from '@/features/player_record/types';
import { levelRow } from '@/features/play/types';
import { counted } from '@/shared/formatting/counted';
import { handleStem, playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { sentenceList } from '@/shared/formatting/sentenceList';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Game, GameSeat } from '../domain/game';
import type { PairingSeat } from '../domain/pairing';
import { sidesForReader } from '../domain/pairing';
import {
  othersOn,
  resultArgument,
  type CalledOffEnding,
  type ResultArgument,
} from '../domain/resultArgument';
import type { ScoreKey, ScoreProblem } from '../domain/score';
import { scoreColumn, type GameKind, type Outcome } from '../domain/vocabulary';

import type { ScoreView } from './gameAccessibility';

import { durationLeft, durationSince } from '@/shared/formatting/durations';

// ---------------------------------------------------------------------------
// The head of the screen
// ---------------------------------------------------------------------------

/**
 * The eyebrow at the head of the screen: the sport, **who you played**, and how
 * long ago it was arranged.
 *
 * **A duration and never a date**, because this platform has no calendar to print one against —
 * the grid is *an ordinary week*, a `Window` is a label on a search rather than a proposed time,
 * and there is no date picker anywhere in this app. That duration used to be the *only* thing
 * telling two padel games apart, which made three games in a week three near-identical rows
 * ([#319](https://github.com/Raketa02/Raketa/issues/319)); the handles are what tell them apart
 * now, and the duration goes on saying which was longest ago.
 *
 * **The court's own order, and the whole of every handle.** A doubles court is three people and
 * a comma-and list of three sixty-four-character handles is a long line — it is one the row
 * clips rather than one this deck shortens, because
 * [ADR-0107](../../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md) §4
 * is about what a sentence *says*, and a box deciding how much of a sentence fits is that box's
 * business.
 */
export function gameEyebrow(sportName: string, game: Game, playerId: string): string {
  const played = withWhom(othersOn(game, playerId));
  return `${sportName}${played} · arranged ${durationSince(game.plannedAt, game.readAt)} ago`;
}

/** The two shapes of court, read off the seats the game actually has. */
const SINGLES = 'Singles';
const DOUBLES = 'Doubles';

/** How many seats a singles court has. Two, and the boundary between the two words above. */
const SINGLES_SEATS = 2;

/**
 * The kind, as the eyebrow says it — **`Counted`, never `Competitive`**: that is a search's word
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.4 #8), and
 * the design's own forecast sentence says *a counted game*.
 */
const KIND_WORD: Readonly<Record<GameKind, string>> = { COUNTED: 'Counted', FRIENDLY: 'Friendly' };

/**
 * `Doubles · Counted` — **the eyebrow on the plan lead, and the whole head of that screen**
 * ([#414](https://github.com/Raketa02/Raketa/issues/414)).
 *
 * The format and the kind, and nothing else: the card under it names the people and the plan
 * names the day, so the handles and *arranged n ago* that `gameEyebrow` carries would be the same
 * facts twice on one screen. The format is read off the seats — the rule the Now card's retired
 * eyebrow used, living here now — and the kind off the game; **a kind this build cannot read
 * drops its clause and the format stands**, so a game whose kind is absent is still headed as a
 * game. There is no title under it: the design draws none, and 10.3 is amended to say so.
 *
 * **Not uppercased here.** The header's style does that, and a second copy in the string would
 * reach a screen reader as letters.
 */
export function formatEyebrow(game: Game): string {
  const format = game.seats.length <= SINGLES_SEATS ? SINGLES : DOUBLES;

  return game.kind === undefined ? format : `${format} · ${KIND_WORD[game.kind]}`;
}

/**
 * *with kasia_w, tomek.p and marekb* — **and the empty string for a court with nobody else on
 * it**, which is the stale-link case rather than a game.
 *
 * `counted()` is not reached for: nothing here is counted, and the join is a list of names in
 * the court's own order. The last comma is an *and* because this is prose and not a legend — and
 * that join is `sentenceList`'s, which is the platform's one spelling of it (§22.6).
 */
function withWhom(others: readonly NamedPlayer[]): string {
  const names = others.map(playerName);

  return names.length === 0 ? '' : ` · with ${sentenceList(names)}`;
}

// ---------------------------------------------------------------------------
// What a game is, in one line
// ---------------------------------------------------------------------------

/**
 * The one sentence that says what this game is asking of you — **on the row and on the screen,
 * and it is the same sentence in both places.**
 *
 * A row that summarised and a screen that explained would be two claims about one standing, and
 * the first person to notice would be somebody who read the row, tapped it, and found a
 * different deadline.
 */
export const NOT_YOURS_LINE = 'No game of yours has this address.';

/**
 * **The same sentence, for a surface that holds a game and not an argument** — the one thing
 * this deck says outside its own feature.
 *
 * Now's card is `features/plans`' ([#367](https://github.com/Raketa02/Raketa/issues/367)) and the
 * gloss it draws under an ended or argued game is this line: what the card adds for the four
 * `AWAITING_ENTRY` rungs is written there, and for everything else the sentence already exists,
 * has a test, and is the one the screen behind the card says. So what crosses the seam is the
 * **sentence** rather than the fold and the deck — a surface that reached for `resultArgument`
 * would be reading a `GameStanding` outside the one file allowed to
 * ([`resultArgument.ts`](../domain/resultArgument.ts)).
 *
 * It takes the game rather than the pair because the instant is the game's: `readAt` travels on
 * every row precisely so a screen holding one game does not have to be handed the list's fold.
 */
export function gameStandingLine(game: Game, playerId: string): string {
  return standingLine(resultArgument(game, playerId), game.readAt);
}

export function standingLine(argument: ResultArgument, readAt: string): string {
  switch (argument.kind) {
    case 'not-yours':
      return NOT_YOURS_LINE;
    case 'unreadable':
      return OUT_OF_DATE_GAP;
    case 'awaiting-entry':
      return argument.entryClosesAt === undefined
        ? 'Nobody has said this one happened yet.'
        : `Nobody has said this one happened yet — ${durationLeft(argument.entryClosesAt, readAt)} left to say you played.`;
    case 'never-played':
      return 'Nobody said this one happened before the window closed, so nothing was recorded.';
    case 'called-off':
      // The gloss on the card's tag and the standing line alike — one word for this ending
      // everywhere (ADR-0172 §8). Who and how are the heading's and the body's, not this line's.
      return 'Called off';
    case 'ours-stands':
      return `Your side's score is on the table. If nobody answers within ${durationLeft(argument.proposal.answerBy, readAt)}, it stands.`;
    case 'theirs-stands':
      // **The one sentence on these screens that was addressed to nobody.** *That's right*
      // settles a score against a person, and until a seat carried a handle the screen could
      // not say which (#319).
      return `${playerName(argument.by)} put a score up. If you say nothing for ${durationLeft(argument.proposal.answerBy, readAt)}, it stands.`;
    case 'both-stand':
      return "Both sides wrote a score down and they don't match.";
    case 'agreed': {
      // The side it is news for is the only thing that differs, and it is the whole of why this
      // is on the standing line: the line is **the row's sentence too**, so the person whose
      // score was agreed with reads it without opening anything.
      // *You* on your own tap, and your partner by name on theirs — the second is the whole
      // reason the accepter travels: in a doubles game *your side agreed* is news about somebody
      // the reader did not watch do it.
      const agreed = playerName(argument.agreement.by);
      const who =
        argument.agreement.with === 'ours'
          ? `${agreed} agreed with your score.`
          : `${agreed} agreed with their score.`;
      return `${who} It becomes the result in ${durationLeft(argument.agreement.settlesAt, readAt)}.`;
    }
    case 'confirmed':
      return 'Agreed.';
    case 'unscored':
      return 'Nobody agreed a score.';
    case 'started-short':
      return SEAT_WAS_EMPTY;
    case 'no-show-reported': {
      // The marked player's own line says how long they have, as a score's says how long silence
      // takes: what happens when it runs out is visible before it does (#560).
      const { yours } = argument;
      if (yours === undefined) {
        const marked = argument.others.map((mark) => playerName(mark.who));
        return `${sentenceList(marked)} ${marked.length > 1 ? 'were' : 'was'} marked as not coming.`;
      }
      switch (yours.state) {
        case 'open':
          return `You were marked as not coming. ${durationLeft(yours.disputeBy, readAt)} left to say you were there.`;
        case 'disputed':
          return 'You said you were there, so the mark is gone.';
        case 'stood':
          return 'You were marked as not coming, and your day to say otherwise has passed.';
      }
    }
    case 'no-show':
      return argument.didNotCome.length === 0
        ? 'Somebody didn’t come.'
        : `${sentenceList(argument.didNotCome.map(playerName))} didn’t come.`;
  }
}

/**
 * **Everybody else's report, one line each** (#560) — what became of it: their day still running,
 * and how long it has; said they were there; or the day over and nobody said so. The reader's own
 * report is the standing line's and the clock's, so it is not repeated here.
 */
export function reportLines(argument: ResultArgument, readAt: string): readonly string[] {
  if (argument.kind !== 'no-show-reported') return [];
  return argument.others.map((mark) => {
    const name = playerName(mark.who);
    switch (mark.state) {
      case 'open':
        return `${name} — ${durationLeft(mark.disputeBy, readAt)} left to say they were there`;
      case 'disputed':
        return `${name} says they were there`;
      case 'stood':
        return `${name} didn’t come`;
    }
  });
}

/** *A seat was empty.* — the standing line of a booked game that started short (#544). */
const SEAT_WAS_EMPTY = 'A seat was empty.';

/**
 * **The ghost's body** — nothing anybody is measured on moves (ADR-0163 §3) — said of a game that
 * never happened.
 */
const NOBODY_IS_MARKED_FOR_THAT = 'Nobody is marked for that. Not you, not any of the others.';

/**
 * **The ending block's one heading** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §8, [ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §3): both ways a game is called off are a shortage — a departure emptied the court, or the
 * hour found it still short of a player — and the heading says so without a name; the body says
 * which. *{name} called the game off* went with the press. Exported for the suite that walks the
 * ended court one feature over.
 */
export const CALLED_OFF_FOR_LACK_OF_PLAYERS = 'The game was called off for lack of players';

/**
 * **The trash's spoken name** — the one control on a called-off card besides *What happened?*,
 * a glyph with its word spoken ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §8). *This card* and not *this game*: the act removes a card and nothing else, and the name
 * says exactly that much.
 */
export const REMOVE_THIS_CARD = 'Remove this card';

/**
 * The ending's body: a departure names who left and says the shape of the game it ended; the
 * hour says nobody filled the seat and the same shape. Both end with the ghost's own fact about
 * the strands — the same fact about the same people (ADR-0163 §3), because a call-off is neither
 * an evening nor a game that never happened.
 */
function calledOffBody(ending: CalledOffEnding): string {
  if (ending.how === 'the-hour') {
    return ending.format === 'singles'
      ? 'Nobody filled the seat in time, so the singles game is called off. Nobody is marked for it — not you, not them.'
      : 'Nobody filled the seat in time, so the doubles game is called off. Nobody is marked for it — not you, not any of them.';
  }

  const name = playerName(ending.by);
  return ending.format === 'singles'
    ? `${name} left, so the singles game is called off. Nobody is marked for it — not you, not them.`
    : `${name} was the last to leave, so the doubles game is called off. Nobody is marked for it — not you, not any of them.`;
}

/**
 * The screen's own title — **variant C's, unchanged**, plus the three states the prototype's
 * five screens did not have to name.
 */
export function resultTitle(argument: ResultArgument): string {
  switch (argument.kind) {
    case 'not-yours':
      return 'Not your game';
    case 'unreadable':
      return 'This game';
    case 'awaiting-entry':
      return 'The score';
    case 'never-played':
      return 'It never happened';
    case 'called-off':
      return CALLED_OFF_FOR_LACK_OF_PLAYERS;
    case 'ours-stands':
      return 'Sent — waiting';
    case 'theirs-stands':
      return 'Is that right?';
    case 'both-stand':
      return 'Two scores';
    case 'agreed':
      // Not *Sent — waiting* and not *Two scores*: both are titles about an open question, and
      // the question has been answered. What is left is the grace running out.
      return 'Agreed — settling';
    case 'confirmed':
      return 'The result';
    case 'unscored':
    case 'started-short':
    case 'no-show':
      return 'No result';
    case 'no-show-reported':
      switch (argument.yours?.state) {
        case undefined:
          return 'Somebody didn’t come';
        case 'open':
          return 'Were you there?';
        case 'disputed':
          return 'You said you were there';
        case 'stood':
          return 'Marked as not coming';
      }
  }
}

/**
 * **The clock, as the prototype drew it**: a figure big enough to read at arm's length, and one
 * sentence saying what happens when it runs out.
 *
 * Variant C's own arrangement, and the whole of *silence confirming has to be visible before it
 * happens* — the two sides read the same fact differently on purpose, which is what the
 * prototype recorded as the main thing to react to: *"this stands unless you act"* to one side,
 * *"this stands unless they act"* to the other.
 *
 * The prototype quoted an absolute time beside the duration — *"a countdown alone never says
 * WHEN"* — and that clause is **deleted rather than translated**: there is no calendar anywhere
 * in this product and no date picker in this app, so an absolute time would be the first one and
 * it would be this screen inventing it.
 */
export function clockLine(argument: ResultArgument, readAt: string): ClockBlock | undefined {
  // An agreement moves the clock off the answer window and onto the grace, which is a shorter
  // span measured from a different moment — the **score**, never anybody's tap. Silence has
  // stopped being the question, so the sentence under the figure stops naming it.
  if (argument.kind === 'agreed') {
    return {
      figure: durationLeft(argument.agreement.settlesAt, readAt),
      line: 'until this becomes the result. Nothing more is needed from anybody.',
    };
  }

  if (argument.kind === 'ours-stands') {
    return {
      figure: durationLeft(argument.proposal.answerBy, readAt),
      line: 'left for the other side to answer. If they say nothing, this becomes the result.',
    };
  }
  if (argument.kind === 'theirs-stands') {
    return {
      figure: durationLeft(argument.proposal.answerBy, readAt),
      line: 'until this becomes the result. Nobody has to do anything — silence confirms it.',
    };
  }
  // The marked player's day, at arm's length — what saying nothing does, before it happens (#560).
  if (argument.kind === 'no-show-reported' && argument.yours?.state === 'open') {
    return {
      figure: durationLeft(argument.yours.disputeBy, readAt),
      line: 'left to say you were there. After that the mark stands.',
    };
  }
  if (argument.kind === 'awaiting-entry' && argument.entryClosesAt !== undefined) {
    return {
      figure: durationLeft(argument.entryClosesAt, readAt),
      line: 'left to say this game happened. After that it is recorded as one that never did.',
    };
  }
  return undefined;
}

/** A figure to read at arm's length, and the sentence under it. */
export interface ClockBlock {
  readonly figure: string;
  readonly line: string;
}

/**
 * What an unscored game **still is** — variant C's fact list, with the two lines the model
 * changed.
 *
 * The prototype named the other side (*"You have now played with Kuba & Ada"*) and stated the
 * kind as a fact (*"It was a counted match, not a friendly"*); the kind is `worthLine`'s and may
 * be absent, and the naming is the **eyebrow's**, two lines above this list on the same screen.
 * A second copy of the court here would be the same fact twice in one view. What is left is the
 * three that are true of every unscored game and read as an account rather than as an apology.
 */
export const UNSCORED_FACTS: readonly string[] = [
  'It is in your history, and in how much you have played',
  'You have now played with the people who were on this court',
  'It moved nobody’s Level, and nobody lost anything',
];

/**
 * The paragraph under the title — the part of the rule a player has to know **before** they act.
 *
 * `undefined` where the standing line has already said the whole of it: a second sentence
 * restating the first is what teaches somebody to stop reading the first.
 */
export function resultBody(
  argument: ResultArgument,
  { booked = false }: { readonly booked?: boolean } = {},
): string | undefined {
  switch (argument.kind) {
    case 'awaiting-entry':
      // ADR-0137 §2 for a player: there is no booking behind any of this, so the entry is not
      // paperwork about a game the platform already knows about — it *is* the record. **A booked
      // game has a booking behind it** (#556), and somebody may not have come to it (#560), so it
      // says the other thing that can be said instead of a score.
      return booked
        ? 'Putting a score in records how this game went. If somebody didn’t come, say so below instead.'
        : 'Putting a score in is what records that this game happened. There is nothing else behind it — no booking, no calendar.';
    case 'never-played':
      return NOBODY_IS_MARKED_FOR_THAT;
    // The fourth end is drawn as the ghost is (#419 §3): neither an evening nor a game that never
    // happened, so nothing anybody is measured on moves (ADR-0163) — and the body says the
    // ghost's own fact, naming the person where a departure ended it (ADR-0172 §8).
    case 'called-off':
      return calledOffBody(argument.ending);
    case 'ours-stands':
      return 'You can change what you entered until they answer, and it does not use your side’s one turn up. If they put something else up instead, only an acceptance settles it.';
    case 'theirs-stands':
      return 'One tap from either of you settles it now. A modification always carries a score of its own — there is no way to just say no — and agreeing is never how you avoid a penalty, because there is none.';
    case 'both-stand':
      // **It names the exit rather than stating an ending.** ADR-0137 §4 has always allowed
      // either side to accept the other's here, and with both scores on the response the screen
      // can finally offer it — so the sentence promises the control that is drawn under it, and
      // goes on saying that the other ending costs nobody anything.
      return 'Raketa doesn’t decide between them. One of you agreeing with the other’s score is the only thing that gives this game a result; if neither of you does it stays unscored, which takes nothing away from anybody. Nobody is marked for a disagreement, on either side.';
    case 'agreed':
      // **The one sentence that has to know how many scores are up.** The grace is a window in
      // which a disagreement still wins, and saying so over a game where each side has already
      // used its one turn would promise an act `state_result` refuses with
      // `your_side_has_already_answered` — the same failure the old `both-stand` copy was
      // written to avoid, one state along. Which side could make one is the screen's business
      // and not this sentence's: what differs here is only whether anybody can.
      return argument.ours !== undefined && argument.theirs !== undefined
        ? 'Both scores stay up until then, and neither side can put another one there — each side gets one, and both have been used. Nobody is marked either way.'
        : 'Until then, anybody who played can still put a different score up. That window is what stops somebody quick to their phone from closing the door on a player who has not read the score yet. Nobody is marked either way.';
    case 'unscored':
      // Variant C's own lead, and the register the ticket asks for: *an evening, not evidence*
      // — an account of what it still is, never an apology for what it is not.
      return 'Nobody wrote a score down, so this one counted as an evening. Nobody is marked for it.';
    case 'started-short':
      // The mechanics §14.1: *it cannot take a result … no levels move, and nothing goes on the
      // record of the players who stayed*.
      return 'Somebody left after the club’s cut-off and nobody took the seat, so this game can’t take a result. No Level moved, and nobody who stayed is marked for it.';
    case 'no-show-reported': {
      // Nobody arbitrates (the mechanics §15.3): a dispute falls the report whole, silence lets it
      // stand, and the game does not count either way.
      switch (argument.yours?.state) {
        case undefined:
          return 'Each of them has a day to say they were there; if they don’t, the mark stands. Either way the game doesn’t count and no Level moves — and nobody who came is marked for it.';
        case 'open':
          return 'If you were there, say so: the mark falls and nothing goes on your record. If you don’t, it stands — not turning up is the strongest mark on a record. The game doesn’t count either way, and no Level moves.';
        case 'disputed':
          return 'Raketa doesn’t decide who is right, so the game doesn’t count and no Level moves — and nothing about it is on your record.';
        case 'stood':
          return 'The game doesn’t count, and no Level moves.';
      }
    }
    case 'no-show':
      return argument.didNotCome.some((who) => who.kind === 'you')
        ? 'Nobody said otherwise in time, so the mark stands: the game didn’t count, and not turning up is the strongest mark on a record.'
        : 'The game didn’t count and no Level moved. Nobody who came is marked for it.';
    case 'not-yours':
    case 'unreadable':
    case 'confirmed':
      return undefined;
  }
}

/**
 * What this evening is worth — **stamped when it was arranged and never derived at the end.**
 *
 * **It says what is counted and not what that will one day move.** *An agreed score moves both
 * sides' Levels* is the thing everybody assumes this sentence says, and it is a promise this
 * build cannot keep: ADR-0137's own Consequences record that *"the rating context has nothing to
 * subscribe to"*, and reading confirmed results forward is [#304](https://github.com/Raketa02/Raketa/issues/304)'s
 * unbuilt work. So the counted line states the fact — it is evidence and it is on your record —
 * and the friendly line keeps its **negative**, which is true whether or not anything reads it.
 *
 * `undefined` when the kind is a code this build cannot read: the clause is dropped and every
 * other sentence on the screen still stands, which is `the-words.md` §3's split applied to a
 * fact that keys no total.
 */
export function worthLine(kind: GameKind | undefined): string | undefined {
  if (kind === undefined) return undefined;
  return kind === 'COUNTED'
    ? 'This one counts, so an agreed score becomes part of your record.'
    : 'This one is a friendly. The score is for the record, and it is not evidence about how anybody plays.';
}

/** What a confirmed result said about you. `undefined` where the wire gave no outcome. */
export function outcomeLine(outcome: Outcome | undefined): string | undefined {
  if (outcome === undefined) return undefined;
  return outcome === 'WIN' ? 'You won.' : 'You lost.';
}

// ---------------------------------------------------------------------------
// The court, with nobody on it
// ---------------------------------------------------------------------------

/**
 * Who was on court, **as a shape** — the eyebrow above it is where they are named.
 *
 * A doubles line naming four people would put the same three handles on screen twice, and this
 * sentence's job is the other half: how many were out there, and who was against whom.
 */
export function courtLine(ours: number, theirs: number): string {
  return ours + theirs > SINGLES_SEATS
    ? 'Doubles — you and your partner against two others.'
    : 'Singles — you against one other player.';
}

/**
 * What the two columns of every score on these screens are called.
 *
 * **Sides and never people, even where a handle is available.** A score is a fact about a side —
 * one per side, and either side may agree with the other's — so a column headed with a name
 * would attribute a doubles score to one of the two who played it, and a listener reading a set
 * cell by cell would hear the wrong person's six.
 */
export function sideLabels(ours: number): { readonly ours: string; readonly theirs: string } {
  return ours > 1 ? { ours: 'Your side', theirs: 'Their side' } : { ours: 'You', theirs: 'Them' };
}

// ---------------------------------------------------------------------------
// The score: its shape, and the words for one
// ---------------------------------------------------------------------------

/**
 * What one row of the grid is called, and what the sport is played in. **The prototype's own
 * table** — a set in tennis and padel, a game in squash and badminton — because a squash player
 * reading *set 3* is reading about a different sport.
 */
const SET_NOUN: Readonly<
  Record<Sport, { readonly one: string; readonly many: string; readonly note: string }>
> = {
  padel: { one: 'Set', many: 'sets', note: 'Sets and games' },
  tennis: { one: 'Set', many: 'sets', note: 'Sets and games' },
  squash: { one: 'Game', many: 'games', note: 'Games and points' },
  badminton: { one: 'Game', many: 'games', note: 'Games and points' },
};

/** `Set 2`, `Game 4` — the label down the side of the grid, and the head of a refusal. */
export function setLabel(sport: Sport, index: number): string {
  return `${SET_NOUN[sport].one} ${index}`;
}

/**
 * What the app is and is not checking, said once, under the grid — **the prototype's own line**:
 * *"{what the sport is played in} · the app knows the shape, not the rulebook."*
 *
 * The reason is worth stating to the player: local variation runs from golden points to timed
 * formats, and an app that ruled on those would eventually call a real evening illegal.
 */
export function shapeNote(sport: Sport): string {
  return `${SET_NOUN[sport].note} · we know the shape, not the rulebook`;
}

/** What a key of the pad draws: a value, the ceiling with a `+`, or the rub-out's own word. */
export function keyFace(key: ScoreKey, padTo: number): string {
  switch (key.kind) {
    case 'value':
      return String(key.value);
    case 'higher':
      return `${padTo}+`;
    case 'rub':
      return RUB_OUT_LABEL;
  }
}

/** The winner's row on a printed score, as a **word** — because Part 13 forbids a mark alone. */
export const WON_MARK = 'won';

/** Why the grid will not take this draft yet. One function per variant, because they differ. */
export function scoreProblemLine(problem: ScoreProblem, sport: Sport): string {
  const noun = SET_NOUN[sport];
  switch (problem.code) {
    case 'no-sets':
      return `Put the first ${noun.one.toLowerCase()} in to continue.`;
    case 'a-gap':
      return `${setLabel(sport, problem.set)} is empty — the ${noun.many} go in the order they were played.`;
    case 'half-a-set':
      return `${setLabel(sport, problem.set)} has one side missing.`;
    case 'level-set':
      return `${setLabel(sport, problem.set)} cannot end level — a ${noun.one.toLowerCase()} that is level has not finished.`;
    case 'no-winner':
      return `This score names no winner. Add the deciding ${noun.one.toLowerCase()}.`;
  }
}

/**
 * The one refusal that is about the **other** side's score rather than about this draft.
 *
 * A counter is pre-loaded with the score it is answering, because a real disagreement is
 * usually one digit — and an unchanged one sent back would be a second proposal that agrees
 * with the first, which leaves the game unscored between two people who agreed. So it is
 * refused here rather than paid for a day later.
 */
export const COUNTER_IS_THEIR_SCORE =
  'That is the score they put up. Agree with it rather than sending it back — two matching scores nobody accepts still leave the game unscored.';

/** A score in the reader's own order, as words. The drawing names both sides; so does this. */
export function spokenScore({ score, sport, mine, sides }: ScoreView): string {
  const column = scoreColumn(mine);
  return score.sets
    .map((set, index) => {
      const ours = column === 'a' ? set.a : set.b;
      const theirs = column === 'a' ? set.b : set.a;
      return `${setLabel(sport, index + 1)}, ${sides.ours} ${ours}, ${sides.theirs} ${theirs}`;
    })
    .join('. ');
}

/** `3 sets`, `1 game` — through the app's one pluralisation seam, so no sentence hardcodes an s. */
export function setsCounted(sport: Sport, sets: number): string {
  const noun = SET_NOUN[sport];
  return counted(sets, noun.one.toLowerCase(), noun.many);
}

// ---------------------------------------------------------------------------
// The controls
// ---------------------------------------------------------------------------

/** The entry's send — variant C's *Send this score*, and the only act on an unclaimed game. */
export const ENTER_LABEL = 'Send this score';

/**
 * *Change what I entered* — free, and **not** your side's one turn.
 *
 * Variant C's own word, and the control's name is where the ticket's *"a player will spend an
 * attempt fixing a typo"* is actually answered: *change what I entered* cannot be read as a
 * second turn, where *propose* could.
 */
export const CORRECT_LABEL = 'Change what I entered';

/** Agreeing, from across the net. One opponent is the whole of the evidence a score was real. */
export const ACCEPT_LABEL = 'That’s right';

/**
 * Disagreeing — which **opens the grid** rather than sending anything.
 *
 * **The product's word is *propose a modification*, never *dispute***, which the spec delta this
 * flow was written in states outright and the prototype drew. There is no bare rejection in this
 * flow, so this control is the door to a score and the send is the one under it.
 */
export const COUNTER_LABEL = 'Propose a modification';

/** Backing out of a grid that was opened over something already on screen. */
export const CANCEL_LABEL = 'Leave it as it is';

/**
 * What each printed score **is**, spoken before the figures — the one thing about a score that
 * differs by where it is drawn.
 *
 * Two of them name the same score from opposite sides of one disagreement, and they are drawn
 * together: *the score on the table* is what a lone one is called, and it stops being that word
 * the moment there are two of them and one is yours.
 */
export const SCORE_LEAD = {
  agreed: 'The agreed score',
  ours: 'Your score',
  theirs: 'Their score',
  only: 'The score on the table',
} as const;

/** The heading over the score a counter is answering, still on the table beside the new one. */
export const STILL_ON_THE_TABLE = 'THEIRS — STILL ON THE TABLE';

/** The heading over the grid a counter types into, so the two tables are never confused. */
export const YOURS = 'YOURS';

/** The send under the grid, named for the act the record will read it as. */
export function submitLabel(act: 'enter' | 'correct' | 'counter'): string {
  switch (act) {
    // Variant C sends an entry and a correction under the same word, and the reason survives:
    // the grid is the same instrument doing the same thing, and only the counter is a different
    // act. Repeating `CORRECT_LABEL` here would put the button that OPENED the grid and the
    // button that sends it under one name, which is how a screen starts referring to something
    // that is not on it.
    case 'enter':
    case 'correct':
      return ENTER_LABEL;
    case 'counter':
      return 'Propose this instead';
  }
}

/** The busy label under every one of them — the same act, still happening. */
export const SENDING_LABEL = 'Sending…';

// ---------------------------------------------------------------------------
// Somebody didn't come (#560; the Games & Fill in mechanics §15.3)
// ---------------------------------------------------------------------------

/**
 * The block's eyebrow, where a booked game's result is entered. Stored as words and drawn
 * uppercase, `BALANCE_FORECAST`'s rule.
 */
export const DIDNT_COME = 'Didn’t come?';

/** The one line under it — when to use it, and what it does, before anybody presses. */
export const DIDNT_COME_LINE =
  'Only for somebody who didn’t turn up at all. The game then doesn’t count, and they get a day to say they were there.';

/**
 * ***Kuba Nowak didn't come*** — the control on a row, and the act on the sheet: the mechanics'
 * own words, the name **whole** (ADR-0171), never a first name derived from it.
 */
export function didNotComeLabel(who: NamedPlayer): string {
  return `${playerName(who)} didn’t come`;
}

/** The row of a player the club's desk checked in — drawn, and nothing to press. */
export function checkedInLine(who: NamedPlayer): string {
  return `${playerName(who)} · checked in at the club`;
}

/**
 * The sheet's title names **the moment**, so the act is named once — by the control that carries it
 * out — on the leave sheet's rule.
 */
export const NO_SHOW_SHEET_TITLE = 'Before you say so';

/** The sheet's dismissal, named by what it does. */
export const NO_SHOW_SHEET_CLOSE_LABEL = 'Don’t mark anybody';

/**
 * **The sheet's three lines** — when it is for, what it does to the game, and what it does to them:
 * the mechanics' 24 hours, said before the report as the product's rule; after it, the screen reads
 * the server's own instant.
 */
export function noShowSheetBody(who: NamedPlayer): readonly string[] {
  const name = playerName(who);
  return [
    `Say this only if ${name} didn’t turn up at all — not for being late.`,
    'The game won’t count, and nobody’s Level moves.',
    `${name} gets 24 hours to say they were there. If they don’t, it stands — the strongest mark on a record.`,
  ];
}

/** ***I was there*** — the marked player's dispute, pinned while their day runs. */
export const DISPUTE_LABEL = 'I was there';

/**
 * The rub-out key. **A word rather than ⌫**, for the reason the on-court mark is a word rather
 * than a tick: Archivo ships no U+2713 and no U+232B either, and a glyph a family does not carry
 * is a box on somebody's phone.
 */
export const RUB_OUT_LABEL = 'Rub out';

// ---------------------------------------------------------------------------
// The court's pairing — the forecast block and the players card (the-words.md §25)
// ---------------------------------------------------------------------------

/**
 * The forecast block's eyebrow. **Stored as words and drawn uppercase** by the eyebrow style,
 * for `formatEyebrow`'s reason: a second copy in the string would reach a screen reader as
 * letters.
 */
export const BALANCE_FORECAST = 'Balance forecast';

/**
 * The word between the two side strengths, and the whole of what the middle column says.
 *
 * Lower case, because it is a unit rather than a heading: the two figures either side of it are
 * the sentence. The builder's forecast card says the same word in the same place, and it is
 * spelled here rather than borrowed because it is a word this screen says and §25 lists.
 */
export const GAP_WORD = 'gap';

/**
 * **What a confirmed score does**, under the percentage — the counted game moves everybody, the
 * friendly moves nobody. `undefined` for a kind this build cannot read: the sentence is dropped
 * and the figure above it still stands, which is §3's split applied to a clause that keys no
 * total. It is `worthLine`'s fact in the forecast's register — *movement*, beside the number that
 * says how even — and not that sentence again, because the two sit on one screen four cards
 * apart and a reader who has read one should not be told it twice in the same words.
 */
export function forecastSentence(kind: GameKind | undefined): string | undefined {
  if (kind === undefined) return undefined;
  return kind === 'COUNTED'
    ? 'A counted game — a confirmed score moves everybody’s level.'
    : 'A friendly — nothing moves.';
}

/** The two stake tiles' names. *If*, because on a game the result has not happened. */
export const WIN_TILE = 'If you win';
export const LOSE_TILE = 'If you lose';

/**
 * The bar's two labels — **stems**, yours then theirs.
 *
 * A segment half a card wide cannot hold sixty-four characters, and `handleStem` is the one cut
 * ADR-0107 permits: a prefix of what somebody typed, drawn where a box draws and never where a
 * sentence names. *You* leads your side because a player reading their own handle on a bar about
 * them is the one place the whole handle is the wrong word; a seat `users` cannot answer for is
 * the unknown player's `?`. Singles is the same rule with one name a side.
 */
export function barLabels(seats: readonly GameSeat[], playerId: string): readonly [string, string] {
  const [yours, theirs] = halves(seats, playerId);
  // The cut is made on the name and never on *You* or on `?`: neither is a name, and
  // `handleStem` is licensed for a prefix of what somebody typed.
  const stem = (seat: GameSeat): string => {
    const who = named(seat, playerId);
    return who.kind === 'player' ? handleStem(who.name) : playerName(who);
  };

  return [yours.map(stem).join(SIDE_JOIN), theirs.map(stem).join(SIDE_JOIN)];
}

/** How two stems on one side are joined on the bar. The builder's own join, for the same box. */
const SIDE_JOIN = ' + ';

/**
 * The same two sides **as a sentence names them** — every name whole, over *and* — for the
 * split row's spoken name. `barLabels` is the drawing and this is the register a listener gets;
 * the two are computed off one split of the court so they cannot disagree about who is where.
 */
export function sideNames(seats: readonly GameSeat[], playerId: string): readonly [string, string] {
  const [yours, theirs] = halves(seats, playerId);
  const name = (seat: GameSeat): string => playerName(named(seat, playerId));

  return [sentenceList(yours.map(name)), sentenceList(theirs.map(name))];
}

/** Who a seat holds, in the reader's own terms — `whoIs`'s rule, read off the seat in hand. */
function named(seat: GameSeat, playerId: string): NamedPlayer {
  if (seat.playerId === playerId) return { kind: 'you' };
  return seat.name === undefined ? { kind: 'unknown' } : { kind: 'player', name: seat.name };
}

/**
 * The court split into your side and theirs — the domain's one split, and an empty pair for a
 * reader holding no seat, which the plan lead never draws for.
 */
function halves(
  seats: readonly GameSeat[],
  playerId: string,
): readonly [readonly GameSeat[], readonly GameSeat[]] {
  const sides = sidesForReader(seats, playerId);
  return sides === undefined ? [[], []] : [sides.yours, sides.theirs];
}

/**
 * One seat's Level, in the row under the handle — `the-words.md` §6.4's level row with the
 * confidence as a fourth clause: `2,71 · Established · likely 2,55 – 2,87 · 74% sure`.
 *
 * The first three clauses are Play's `levelRow`, cited rather than re-spelled, so the band's name,
 * the range's dash and the two-decimal comma cannot drift between a card and this row. The fourth
 * is the engine's own whole percentage through the one formatter, and the word *sure* is this
 * screen's — the challenge card says `{n}% sure` the same way.
 */
export function seatLevelLine(seat: PairingSeat): string {
  return `${levelRow(seat)} · ${formatPercent(seat.confidence)} sure`;
}

/**
 * The players card's footer — the promise the record sheet keeps, and the gesture that opens it.
 *
 * **Tap, not hold**: the design's *press and hold* is refused on #285's argument — a hold has no
 * affordance, no announcement and no equivalent in the accessibility API — and the sentence says
 * the gesture that is actually there. The second sentence is the record's own authorship promise,
 * said where the reader is about to open one.
 */
export const PLAYERS_FOOTER =
  'Tap anyone for their record — level, form and how they behave. Counted by the system; nobody writes text about people here.';

/** The players card's eyebrow. Stored as words, drawn uppercase — `BALANCE_FORECAST`'s rule. */
export const PLAYERS = 'Players';

/**
 * **The row for a seat somebody left** (ADR-0162, #411 rule 6) — the words where a handle would
 * be, an empty face beside them, no level row, and nothing to press: there is no record to open
 * for nobody. The seat is drawn rather than dropped, because a players card that listed three
 * people on a doubles court would be describing a different game.
 */
export const OPEN_SEAT = 'Open seat';

/**
 * Who a row is about: the name where the account still has one, and whether it is yours.
 *
 * Not `NamedPlayer`, because that formatter's *you* is a sentence's word for its reader and this
 * row draws the name **whole** with the mark after it — `recordHandle`'s shape on the record
 * sheet, for the same reason: a panel with your face on it and a stranger's name under it.
 */
export interface PlayerRowPerson {
  /** Absent where `users` no longer has the account, which draws the unknown player's `?`. */
  readonly name?: string;
  readonly yours: boolean;
}

/** The whole name, with the one mark that says it is yours. */
export function playerRowName(person: PlayerRowPerson): string {
  const name =
    person.name === undefined
      ? playerName({ kind: 'unknown' })
      : playerName({ kind: 'player', name: person.name });
  return person.yours ? `${name} ${YOU_MARK}` : name;
}

/**
 * What the row's tap is called — **the record it opens, by whose it is.** *Your record* for your
 * own, because a control named *me_'s record* on a screen addressed to *me_* has read the reader
 * their own handle; the sheet it opens is retitled the same way.
 */
export function recordLabel(person: PlayerRowPerson): string {
  return person.yours ? 'Your record' : `${playerRowName(person)}’s record`;
}

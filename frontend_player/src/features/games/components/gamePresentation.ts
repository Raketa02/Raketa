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
 * - **When silence makes a score the result is said before it happens**, and so is that saying
 *   nothing costs nothing ([#656](https://github.com/Raketa02/Raketa/issues/656), F-RESULT-35.1).
 *   The standing line of a game with a score on the table names **the moment** — *at 20:30 on
 *   Wednesday*, on the club's clock — and the clock block under it the duration. It is not a
 *   footnote a player reaches by tapping. The screen said *there is no penalty* over a silence
 *   that cost a miss until ADR-0195 made silence free; it says *saying nothing costs nothing*
 *   now, and talks about penalties nowhere.
 * - **A game with no score reads as an evening, not an error** — a full game nobody recorded
 *   (*Played · no score*, #655) and two scores naming different winners (*Disputed*, #654). Each
 *   says why it took no score, over the facts both share: these people played, it is in the count
 *   of how much somebody has played, and it moves nobody's Level. There is no red, no *could not*,
 *   and no *unfortunately*.
 * - **A correction is not a second proposal**, and the screen says which one it is offering
 *   before the tap. *"A player will spend an attempt fixing a typo"* is the failure this whole
 *   deck exists to prevent.
 * - **Nobody is penalised for not answering** — ADR-0049, carried whole by
 *   [ADR-0137](../../../../../docs/adr/0137-a-result-is-the-record-that-a-game-happened.md) §5
 *   and made true of the record by ADR-0195. Not the silent loser, not the four who all went
 *   home. Every sentence here that could be read as a reproach says so out loud.
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
 * learn the hard way. What is rewritten is only what the model moved. The prototype quoted an
 * absolute time beside every duration and this deck once deleted it, because nothing had a
 * calendar; **a booked game has one**, so the moment a score settles is named again, on the club's
 * clock (#656). The prototype's names came **back** — a seat
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

import { platformClock, platformDay, weekdayOf } from '@/shared/date/platformZone';
import { counted } from '@/shared/formatting/counted';
import { handleStem, playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import { sentenceList } from '@/shared/formatting/sentenceList';
import { dayName } from '@/shared/vocabulary/availabilityPresentation';
import { COUNTED_GAME_SENTENCE } from '@/shared/vocabulary/forecastPresentation';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Game, GameSeat, Score } from '../domain/game';
import { sidesForReader } from '../domain/pairing';
import type {
  AttendanceBlock,
  AttendanceSaid,
  AttendanceTap,
  LocationRefusal,
} from '../domain/attendance';
import { othersOn, type CalledOffEnding, type ResultArgument } from '../domain/resultArgument';
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
 * **A duration and never a date** — written when nothing in this app had a calendar to print one
 * against. A booked game has one now, and its details print the day; this eyebrow keeps the
 * duration because it is the one line every game state carries alike. That duration used to be the *only* thing
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

export function standingLine(argument: ResultArgument, readAt: string): string {
  switch (argument.kind) {
    case 'not-yours':
      return NOT_YOURS_LINE;
    case 'unreadable':
      return OUT_OF_DATE_GAP;
    case 'awaiting-entry':
      return argument.entryClosesAt === undefined
        ? 'No score yet.'
        : `No score yet — ${durationLeft(argument.entryClosesAt, readAt)} left to put one up.`;
    case 'for-fun':
      // Nothing is asked, so the line is a statement: no question mark, no deadline (#654).
      return argument.score === undefined
        ? 'Played for fun. Nobody is asked anything.'
        : 'Played for fun.';
    case 'played-no-score':
      return 'Nobody put a score up, so it counts as played.';
    case 'called-off':
      // The gloss on the card's tag and the standing line alike — one word for this ending
      // everywhere (ADR-0172 §8). Who and how are the heading's and the body's, not this line's.
      return 'Called off';
    case 'ours-stands':
      return `Your side’s score is up. If nobody answers, it becomes the result${settlesWhen(argument.proposal.answerBy, readAt)}.`;
    case 'theirs-stands':
      // **The moment, and who it waits on** (#656): *if neither he nor Paula answers, 6–4 6–3
      // becomes the result at 20:30 on Wednesday*. The person who put it up is named, because
      // *That's right* settles a score against a person (#319).
      return `${playerName(argument.by)} put a score up. If ${argument.withPartner ? 'neither of you answers' : 'you don’t answer'}, it becomes the result${settlesWhen(argument.proposal.answerBy, readAt)}.`;
    case 'both-stand':
      return `Both sides put a score up, and they don’t match. Unless one side agrees with the other’s, it settles${settlesWhen(argument.settlesAt, readAt)}.`;
    case 'confirmed':
      // Agreed with, settled by silence, or the closer of two scores naming one winner (#654) — the
      // wire does not say which, so the line says what is true of all three.
      return 'Counted.';
    case 'disputed':
      return 'The two scores named different winners.';
    case 'started-short':
      return SEAT_WAS_EMPTY;
    case 'not-here-yet':
      // **Who waits, to the player awaited; whom they wait for, to everybody else** (#658). Who
      // tapped is on no wire, so the awaited player reads everybody the game waits with — in
      // singles that is the one person who could have.
      if (argument.yours) {
        return argument.here.length === 0
          ? 'The others are waiting for you.'
          : `${sentenceList(argument.here.map(playerName))} ${argument.here.length > 1 ? 'are' : 'is'} waiting for you.`;
      }
      return argument.awaited.length === 0
        ? 'Waiting for somebody to arrive.'
        : `Waiting for ${sentenceList(argument.awaited.map(playerName))}.`;
    case 'didnt-come':
      // The reader's own first: *You and Oscar Nowak didn't come* would put *You* mid-sentence, and
      // the block names whoever else said they were there.
      if (argument.yours !== undefined) return 'You didn’t come.';
      return argument.absent.length === 0
        ? 'Somebody didn’t come.'
        : `${sentenceList(argument.absent.map(playerName))} didn’t come.`;
  }
}

/**
 * *at 20:30 on Wednesday* · *at 20:30 today* — **the moment a score settles, on the club's clock**,
 * with the space that joins it to the sentence (#656). A booked game has a calendar, so the moment
 * is named as the story names it rather than only counted down to; it is the platform zone's clock
 * that every booked hour in this app is drawn on, so two people on one court read one moment.
 * **An instant that cannot be read drops the clause** — the clock block under the line still
 * carries the duration — rather than inventing a day.
 */
function settlesWhen(at: string, readAt: string): string {
  const day = platformDay(at);
  const clock = platformClock(at);
  const weekday = day === undefined ? undefined : weekdayOf(day);
  if (day === undefined || clock === undefined || weekday === undefined) return '';
  return day === platformDay(readAt) ? ` at ${clock} today` : ` at ${clock} on ${dayName(weekday)}`;
}

/**
 * *by 17:30* · *by 17:30 on Thursday* — **a deadline on the club's clock**, with the space that
 * joins it to the sentence: the time alone on the day the list was read, the weekday too on any
 * other, or where the read's instant was not handed over.
 * An instant that cannot be read drops the clause rather than inventing a day.
 */
function byWhen(at: string, readAt: string | undefined): string {
  const day = platformDay(at);
  const clock = platformClock(at);
  const weekday = day === undefined ? undefined : weekdayOf(day);
  if (day === undefined || clock === undefined || weekday === undefined) return '';
  const today = readAt !== undefined && day === platformDay(readAt);
  return today ? ` by ${clock}` : ` by ${clock} on ${dayName(weekday)}`;
}

/** *A seat was empty.* — the standing line of a booked game that started short (#544). */
const SEAT_WAS_EMPTY = 'A seat was empty.';

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
 * The ending's body: a departure names who left and says the shape of the game it ended; the
 * hour says nobody filled the seat and the same shape. Both end with the fact that nobody is
 * marked for it (ADR-0163 §3), because a call-off is not an evening: nobody played.
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
 * The screen's own title — **variant C's**, plus the states the prototype's five screens did not
 * have to name. *How did it go?* and *Is that right?* are the two questions §15.2 asks after the
 * hour, and the For fun game, which asks none, reads *Played* (#656).
 */
export function resultTitle(argument: ResultArgument): string {
  switch (argument.kind) {
    case 'not-yours':
      return 'Not your game';
    case 'unreadable':
      return 'This game';
    case 'awaiting-entry':
      return 'How did it go?';
    case 'for-fun':
      return 'Played';
    case 'played-no-score':
      return 'Played · no score';
    case 'called-off':
      return CALLED_OFF_FOR_LACK_OF_PLAYERS;
    case 'ours-stands':
      return 'Sent — waiting';
    case 'theirs-stands':
      return 'Is that right?';
    case 'both-stand':
      return 'Two scores';
    case 'confirmed':
      return 'The result';
    case 'disputed':
      return 'Disputed';
    case 'started-short':
      return 'No result';
    case 'not-here-yet':
      return argument.yours ? 'Are you here?' : 'Not here yet';
    case 'didnt-come':
      return argument.yours?.state === 'may-claim' ? 'Were you there?' : 'Didn’t come';
  }
}

/**
 * **The clock, as the prototype drew it**: a figure big enough to read at arm's length, and one
 * sentence saying what happens when it runs out.
 *
 * Variant C's own arrangement, and the half of *when silence makes a score the result is said
 * before it happens* that the standing line does not carry — the two sides read the same fact
 * differently on purpose, which is what the
 * prototype recorded as the main thing to react to: *"this stands unless you act"* to one side,
 * *"this stands unless they act"* to the other.
 *
 * The prototype quoted an absolute time beside the duration — *"a countdown alone never says
 * WHEN"*. **The standing line above the clock says when** now that a booked game has a calendar
 * (#656), so the block keeps the duration alone rather than saying the moment twice.
 */
export function clockLine(argument: ResultArgument, readAt: string): ClockBlock | undefined {
  if (argument.kind === 'ours-stands') {
    return {
      figure: durationLeft(argument.proposal.answerBy, readAt),
      line: 'left for the other side to answer. If they say nothing, this becomes the result.',
    };
  }
  // **Silence is free** (ADR-0195): the side being asked reads, at arm's length, that saying
  // nothing costs nothing — the sentence F-RESULT-35.1 found missing under a silence that cost a
  // miss.
  if (argument.kind === 'theirs-stands') {
    return {
      figure: durationLeft(argument.proposal.answerBy, readAt),
      line: 'until this becomes the result if nobody answers. Saying nothing costs nothing.',
    };
  }
  // Two scores settle without an agreement when the later one's day is up (#654).
  if (argument.kind === 'both-stand') {
    return {
      figure: durationLeft(argument.settlesAt, readAt),
      line: 'until this settles, if neither side agrees with the other’s score.',
    };
  }
  // **The half hour, at arm's length, at the court** (#658): to the player awaited, how long to
  // arrive; to everybody else, how long the score waits.
  if (argument.kind === 'not-here-yet' && argument.arriveBy !== undefined) {
    return {
      figure: durationLeft(argument.arriveBy, readAt),
      line: argument.yours
        ? 'left to arrive. After that it’s Didn’t come.'
        : 'left for them to arrive. No score goes in until then.',
    };
  }
  // The day to say *I was there* — what saying nothing does, before it happens.
  if (argument.kind === 'didnt-come' && argument.yours?.state === 'may-claim') {
    return {
      figure: durationLeft(argument.yours.claimBy, readAt),
      line: 'left to say you were there. After that, Didn’t come stands.',
    };
  }
  // Nothing else counts down: the entry's window is its standing line's clause, and the entry arm
  // draws no clock over the grid it is about.
  return undefined;
}

/** A figure to read at arm's length, and the sentence under it. */
export interface ClockBlock {
  readonly figure: string;
  readonly line: string;
}

/**
 * What a game with no score **still is** — variant C's fact list, drawn under the two endings that
 * took none and were still played: *Played · no score* and *Disputed*.
 *
 * The prototype named the other side (*"You have now played with Kuba & Ada"*) and stated the
 * kind as a fact (*"It was a counted match, not a friendly"*); the kind is `worthLine`'s and may
 * be absent, and the naming is the **eyebrow's**, two lines above this list on the same screen.
 * A second copy of the court here would be the same fact twice in one view. What is left is the
 * three that are true of every one of them and read as an account rather than as an apology.
 */
export const EVENING_FACTS: readonly string[] = [
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
  { booked = false, readAt }: { readonly booked?: boolean; readonly readAt?: string } = {},
): string | undefined {
  switch (argument.kind) {
    case 'awaiting-entry':
      // ADR-0137 §2 for a player: there is no booking behind any of this, so the entry is not
      // paperwork about a game the platform already knows about — it *is* the record. **A booked
      // game has a booking behind it** (#556), and somebody may not have come to it (#560), so it
      // says the other thing that can be said instead of a score.
      return booked
        ? 'Putting a score in records how this game went.'
        : 'Putting a score in is what records that this game happened. There is nothing else behind it — no booking, no calendar.';
    case 'for-fun':
      // A score for fun stands as it is put and is put to nobody (#654), so the body says so before
      // the send — and says nothing once there is one.
      if (argument.score !== undefined) return undefined;
      // Across an open seat nothing may go in, so the body offers nothing either (#411 rule 5).
      return argument.seatOpen
        ? 'Nobody is asked anything after a game for fun, and no Level moves.'
        : 'You can add the score if you like, up to a day after the game. It stands as you put it — nobody is asked to agree, and no Level moves.';
    case 'played-no-score':
      // #655: a booked, paid, full court is the evidence that the game was played.
      return 'The court was booked and full, so this counts as a game played for everybody on it — just with no score.';
    // The fourth end (#419 §3): not an evening, so nothing anybody is measured on moves
    // (ADR-0163) — and the body names the person where a departure ended it (ADR-0172 §8).
    case 'called-off':
      return calledOffBody(argument.ending);
    case 'ours-stands':
      // Corrections end with the entry window, a day after the hour (#654).
      return 'You can change what you entered until they answer — up to a day after the game — and it doesn’t use your side’s one turn. If they put a different score up instead, either side can still agree with the other’s.';
    case 'theirs-stands':
      // **It settles now, and says so only because it does** (#654): one *That's right* is the
      // result at once. What silence does is the standing line's and the clock's.
      return argument.withPartner
        ? 'If it’s right, one That’s right from either of you makes it the result now. If it isn’t, put the right score up — there is no way to just say no.'
        : 'If it’s right, That’s right makes it the result now. If it isn’t, put the right score up — there is no way to just say no.';
    case 'both-stand':
      // **It names the exit, and both ways it ends without one** (#654): the closer score where
      // both name the same winner, no Level where they name different ones.
      return 'Rakieta doesn’t decide between them. If one of you agrees with the other’s score, that settles it at once. If nobody does by then: when both scores name the same winner, the closer one counts; when they name different winners, no Level moves.';
    case 'disputed':
      return 'Each side said a different side won, and neither agreed with the other’s score in time. Rakieta doesn’t decide who won.';
    case 'started-short':
      // The mechanics §14.1: *it cannot take a result … no levels move, and nothing goes on the
      // record of the players who stayed*.
      return 'Somebody left after the club’s cut-off and nobody took the seat, so this game can’t take a result. No Level moved, and nobody who stayed is marked for it.';
    case 'not-here-yet': {
      // What the half hour decides, said before it runs out (#658; ADR-0195 §3): on time within 10
      // minutes of the start, Came late up to 30, Didn't come after — and to everybody else, that
      // the tap cost them nothing.
      const by =
        argument.arriveBy === undefined
          ? ' within the half hour'
          : byWhen(argument.arriveBy, readAt);
      return argument.yours
        ? `Tap I’m here once you’re at the club — your phone checks where you are. Within 10 minutes of the start you’re on time; after that it’s Came late. If you haven’t arrived${by}, it’s Didn’t come and the game takes no score.`
        : `No score goes in while somebody is awaited. If they arrive${by}, the game goes on as usual — Came late if it was more than 10 minutes after the start. If not, it’s Didn’t come: the game takes no score and doesn’t count. Saying so costs you nothing.`;
    }
    case 'didnt-come':
      switch (argument.yours?.state) {
        case 'may-claim':
          return `If you were there and your phone let you down, say I was there${byWhen(argument.yours.claimBy, readAt)}. Once somebody who played confirms it, it’s Came late and the game goes on. Until then the game takes no score.`;
        case 'claimed':
          return 'You said you were there. Once somebody who played confirms it, it’s Came late and the game goes on. Until then the game takes no score.';
        case 'final':
          return 'The game took no score and didn’t count, and no Level moved.';
        case undefined:
          return 'The game takes no score and doesn’t count, and no Level moves. Nobody who came is marked for it.';
      }
    case 'not-yours':
    case 'unreadable':
    case 'confirmed':
      return undefined;
  }
}

/**
 * **Whether this screen says what the evening is worth** — where a score is up or stands, or may
 * still be added for fun, and nowhere it took none: *its result becomes part of your record* over a
 * game that reads *no Level moved* would be two claims about one evening. Never on the entry
 * either, whose sentence about what a score records is its body's.
 */
export function saysWhatItIsWorth(argument: ResultArgument): boolean {
  switch (argument.kind) {
    case 'ours-stands':
    case 'theirs-stands':
    case 'both-stand':
    case 'confirmed':
    case 'for-fun':
      return true;
    case 'not-yours':
    case 'unreadable':
    case 'awaiting-entry':
    case 'played-no-score':
    case 'called-off':
    case 'disputed':
    case 'started-short':
    case 'not-here-yet':
    case 'didnt-come':
      return false;
  }
}

/**
 * **Whether this ending is an evening, not evidence** — the endings that took no score and still
 * count as played (*Played · no score* and *Disputed*), each drawn over {@link EVENING_FACTS}. A game
 * somebody didn't come to is not one: it never counts.
 */
export function endsAsAnEvening(argument: ResultArgument): boolean {
  switch (argument.kind) {
    case 'played-no-score':
    case 'disputed':
      return true;
    case 'not-yours':
    case 'unreadable':
    case 'awaiting-entry':
    case 'for-fun':
    case 'called-off':
    case 'ours-stands':
    case 'theirs-stands':
    case 'both-stand':
    case 'confirmed':
    case 'started-short':
    case 'not-here-yet':
    case 'didnt-come':
      return false;
  }
}

/**
 * **The score that stands, what it is called, and what it said about you** — a counted game's
 * *result*, or a For fun game's *score* once one is up; nothing on every other state, where a score
 * is on the table rather than standing, or there is none. Either of the two may be absent where the
 * wire sent none, and the line the screen draws for each is dropped with it.
 */
export function settledScore(
  argument: ResultArgument,
): { readonly score?: Score; readonly lead: string; readonly outcome?: string } | undefined {
  switch (argument.kind) {
    case 'confirmed':
      return {
        score: argument.score,
        lead: SCORE_LEAD.result,
        outcome: outcomeLine(argument.outcome),
      };
    case 'for-fun':
      return {
        score: argument.score,
        lead: SCORE_LEAD.played,
        outcome: outcomeLine(argument.outcome),
      };
    case 'not-yours':
    case 'unreadable':
    case 'awaiting-entry':
    case 'played-no-score':
    case 'called-off':
    case 'ours-stands':
    case 'theirs-stands':
    case 'both-stand':
    case 'disputed':
    case 'started-short':
    case 'not-here-yet':
    case 'didnt-come':
      return undefined;
  }
}

/**
 * What this evening is worth — **stamped when it was arranged and never derived at the end.**
 *
 * **It says what is counted, not how far anybody moves.** Levels do move once a counted result
 * settles (#654: within a minute), and by how much is the forecast's to say before the game, not
 * this line's after it. So the counted line states the fact — its result is evidence and it is on
 * your record — and the friendly line keeps its **negative**, which is true whatever reads it.
 *
 * `undefined` when the kind is a code this build cannot read: the clause is dropped and every
 * other sentence on the screen still stands, which is `the-words.md` §3's split applied to a
 * fact that keys no total.
 */
export function worthLine(kind: GameKind | undefined): string | undefined {
  if (kind === undefined) return undefined;
  return kind === 'COUNTED'
    ? 'This one counts, so its result becomes part of your record.'
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
 * usually one digit — and an unchanged one sent back is the same score twice, which settles a day
 * later what *That's right* settles now (#654). So it is refused here, pointing at the tap.
 */
export const COUNTER_IS_THEIR_SCORE =
  'That’s the score they put up. If it’s right, agree with it instead.';

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
  /** The score that stands — agreed, settled by silence, or the closer of two (#654). */
  result: 'The result',
  /** A For fun game's, which nobody was asked to agree with (#654). */
  played: 'The score',
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
// Who's here (#658; ADR-0195 §3)
// ---------------------------------------------------------------------------

/**
 * **The block's eyebrow** — *Who's here* while the half hour runs, *Who was there* after it. Stored
 * as words and drawn uppercase, `BALANCE_FORECAST`'s rule.
 */
export const ATTENDANCE_EYEBROW: Readonly<Record<AttendanceBlock['phase'], string>> = {
  'at-the-court': 'Who’s here',
  afterwards: 'Who was there',
};

/**
 * **The one line under it while *isn't here yet* is offered** — what it is for, and **why the phone
 * reads where it is**, said before anybody presses: the tap works only from the club, and nothing is
 * kept. No sheet stands in front of the tap: it costs its maker nothing, and an arrival lifts it.
 */
export const NOT_HERE_YET_LINE =
  'Tap for anybody who isn’t at the court yet. It works only from the club — your phone reads where you are as you tap, and keeps nothing.';

/**
 * **The control about somebody else**, named whole (ADR-0199 §1): *oscar.n isn't here yet*,
 * *oscar.n is here* — the *they're here* of the mechanics — and *Yes, oscar.n was here*.
 */
export function attendanceTapLabel(tap: AttendanceTap, who: NamedPlayer): string {
  const name = playerName(who);
  switch (tap) {
    case 'not-here-yet':
      return `${name} isn’t here yet`;
    case 'here':
      return `${name} is here`;
    case 'was-here':
      return `Yes, ${name} was here`;
  }
}

/** **What is said beside somebody** — *Oscar Nowak came late*, *You came late*. */
export function attendanceLine(said: AttendanceSaid, who: NamedPlayer): string {
  const name = playerName(who);
  switch (said) {
    case 'not-here-yet':
      return `${name} isn’t here yet`;
    case 'came-late':
      return `${name} came late`;
    case 'says-they-were-there':
      return `${name} says they were there`;
  }
}

/** ***I'm here*** — the awaited player's own, pinned while they are awaited. */
export const IM_HERE_LABEL = 'I’m here';

/** ***I was there*** — the late claim, pinned while its day runs. */
export const I_WAS_THERE_LABEL = 'I was there';

/**
 * **Why a tap at the club went nowhere** — the phone asked for its location and was refused, it is
 * refused for good, or it could not tell where it is, and nothing was sent; or what it sent was too
 * rough to place it at the club. Each says why the location is needed; the two a setting changes
 * point at it.
 */
export const LOCATION_AT_THE_TAP: Readonly<Record<LocationRefusal, string>> = {
  refused:
    'Rakieta needs your location to check you’re at the club. Allow it when your phone asks, then tap again.',
  blocked:
    'Location is off for Rakieta, so it can’t check you’re at the club. Turn it on in Settings — it’s read only when you tap.',
  'no-fix': 'Your phone couldn’t tell where you are. Try again in a moment.',
  rough:
    'Your phone could only tell roughly where you are, so Rakieta couldn’t check you’re at the club. Turn on Precise Location for Rakieta in Settings, or try again in a moment.',
};

/** The remedy beside a permission refused for good, and beside a rough fix. */
export const OPEN_SETTINGS = 'Open Settings';

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
 * **The forecast block's own words are `shared/vocabulary`'s** — the eyebrow, *gap*, the counted
 * sentence and the two tiles — since the block moved to `shared/ui` when a competitive game's
 * details drew it too ([#839](https://github.com/Raketa02/Raketa/issues/839)). They are
 * cited here because this screen says them, and a suite reads them off this feature's copy deck.
 */
export {
  BALANCE_FORECAST,
  GAP_WORD,
  LOSE_TILE,
  WIN_TILE,
} from '@/shared/vocabulary/forecastPresentation';

/**
 * **What a confirmed score does**, under the percentage — a counted game moves everybody's level.
 * `undefined` for a kind this build cannot read: the sentence is dropped and the figure above it
 * still stands, which is §3's split applied to a clause that keys no total. It is `worthLine`'s
 * fact in the forecast's register — *movement*, beside the number that says how even — and not
 * that sentence again, because the two sit on one screen four cards apart and a reader who has read
 * one should not be told it twice in the same words. The sentence is the block's
 * (`COUNTED_GAME_SENTENCE`): a competitive game's details say it too.
 *
 * **A friendly has no sentence, because it has no forecast** (#841, ADR-0207 §5): a For-fun game
 * draws the Social vibe card where *A friendly — nothing moves.* stood (`pairingCardOf`), so the
 * negative went with the block it stood under.
 */
export function forecastSentence(kind: GameKind | undefined): string | undefined {
  return kind === 'COUNTED' ? COUNTED_GAME_SENTENCE : undefined;
}

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

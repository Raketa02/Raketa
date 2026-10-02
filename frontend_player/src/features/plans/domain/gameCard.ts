/**
 * **Which card a game draws, which door it carries, and how long an ending keeps one.**
 *
 * The rail is a list of games at every moment of one life
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4), so the
 * card's name is folded here **at read time** from a standing, the slot count and the clock —
 * **there is no client-side state machine and no status column**, and nothing about a game is
 * remembered between two reads of it.
 *
 * The fold is two questions in one order. **The standing decides first**: an ending is an ending
 * whatever the plan says, and only `AWAITING_ENTRY` reaches {@link rungOf}. That is the seam #329
 * and #324 kept crossing — a game whose score is being argued about is not *Game on* because its
 * plan happens to be whole, and a plan is not consulted about a game that never happened.
 *
 * ## `import type`, and the arrow it keeps
 *
 * `features/plans` may import `features/games` and never the reverse
 * ([ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §1). What crosses here is a **type**, so nothing of that feature is in this module at runtime
 * and `domain/` stays the pure TypeScript `docs/architecture.md` Part 1 requires. The alternative
 * — restating the five standings as a local union — is exactly the drift a shared vocabulary
 * exists to stop.
 */

import type { EntryLead, Game } from '@/features/games/types';

import { RUNGS, rungOf, type CourtRead } from './ladder';
import type { Plan } from './slots';

/**
 * Every card the Now rail can draw, in the order the rungs are read and the endings arrive: the
 * four rungs, the argument, the four endings, and the gap.
 *
 * **`confirm` is one name over four arms.** §5.2 lists *Confirm the result* four times because
 * `GameScreen` has four `AWAITING_ANSWER` arms behind it; the card is the same card in all four,
 * because the door lands on the arm the standing derives and the sentence beneath it is the one
 * `features/games` already writes for that arm.
 */
export const GAME_CARD_NAMES = [
  ...RUNGS,
  'confirm',
  'counted',
  'uncounted',
  'never-played',
  // The fourth end (ADR-0163): an act rather than a fold, shelved from its own instant.
  'called-off',
  'unreadable',
] as const;

/**
 * Every card the Now rail can draw, **derived from the list above** rather than declared beside
 * it, so an eleventh name cannot exist in one and not the other. The four rungs come from the
 * ladder itself, which is what makes *the ladder names four of these* a fact of the types.
 */
export type GameCardName = (typeof GAME_CARD_NAMES)[number];

/**
 * **The named door in a card's footer** — §5.2's table, and the rule over it: *the button carries
 * the act's verb, it navigates, and it never writes.*
 *
 * `undefined` is a card with nothing to press, which three of the endings and the gap are: a
 * control offering an act that state cannot take would be the app naming a thing it cannot do.
 * **The fourth ending's card opens the game screen** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §8): a called-off card names nobody, and *What happened?* is the door to the screen that does
 * — the same `open` as *Game on*'s, and the word is `nowPresentation`'s. The trash beside it is
 * not a door: it writes, and it is `features/games`' own act composed into the card's footer.
 *
 * **`fill` names the door on a court somebody left, and it navigates like the other three.** It
 * ran the fill from the card and landed in the builder when it arrived
 * ([#419](https://github.com/Raketa02/Raketa/issues/419)); the QA walk found that a card door
 * landing in *Build a doubles* is the wrong screen for a game that already exists, and it now
 * opens the game screen — the same screen the room's *Details* opens — where the fill is the
 * arm's primary act ([#429](https://github.com/Raketa02/Raketa/issues/429) F1). So the rule
 * above holds for every door without an exception: each carries a verb, navigates, and writes
 * nothing.
 */
export const GAME_DOORS = ['open', 'we-played', 'confirm', 'fill'] as const;

/**
 * **The named door in a card's footer**, derived from the list above rather than declared beside
 * it — `SPORTS` → `Sport`'s own shape, so a fourth door cannot exist in one and not the other.
 */
export type GameDoor = (typeof GAME_DOORS)[number];

/** How long an ended game keeps its card — **24 h, and #335's number one tab over.** */
export const ENDED_CARD_SHELF_LIFE_MS = 24 * 60 * 60 * 1000;

/** What this game is asking of the player, as the card that says so. */
export function gameCardName(game: Game, plan: Plan | undefined): GameCardName {
  // A standing this build has no word for draws the named gap and offers nothing: naming a card
  // after a state we cannot read is how a player is sent to a screen about something else.
  if (game.standing === undefined) return 'unreadable';

  switch (game.standing) {
    case 'AWAITING_ENTRY':
      return rungOf(plan, game);
    case 'AWAITING_ANSWER':
      return 'confirm';
    case 'CONFIRMED':
      return 'counted';
    case 'UNSCORED':
    // A booked game that started short is uncounted too, *a seat was empty* — and a booked game
    // is Home's card, never this rail's (#556), so the word is only ever a fallback here. So is a
    // booked game somebody did not come to, whatever the report comes to (#560).
    case 'STARTED_SHORT':
    case 'NO_SHOW_REPORTED':
    case 'NO_SHOW':
      return 'uncounted';
    case 'NEVER_PLAYED':
      return 'never-played';
    case 'CALLED_OFF':
      return 'called-off';
  }
}

/**
 * The door this card carries, and `undefined` where it carries none.
 *
 * A `Record` keyed by the union rather than a `switch`, for the reason every other table in this
 * app is one: an eleventh card name fails `pnpm typecheck` here rather than quietly drawing no
 * door.
 */
const DOOR: Readonly<Record<GameCardName, GameDoor | undefined>> = {
  // The plan is read on the screen, so the two planning rungs open it and say so.
  planning: 'open',
  'game-on': 'open',
  // The plan survives a departure (#411 rule 6), and the seat is dealt with on the game screen,
  // whose primary act on this rung is the fill (#419, landed there by #429 F1).
  'needs-a-player': 'fill',
  // *We played* is available in every `AWAITING_ENTRY` arm; this is the one that leads with it —
  // the agreed point is behind the fold, so *you played* is the likeliest true sentence. A game
  // on the day itself is *Game on* or *Planning* and reaches it one press in (ADR-0166).
  'needs-result': 'we-played',
  confirm: 'confirm',
  counted: undefined,
  uncounted: undefined,
  'never-played': undefined,
  // *What happened?* — the screen behind the card is where the ending says who (ADR-0172 §8).
  'called-off': 'open',
  unreadable: undefined,
};

export function doorOf(name: GameCardName): GameDoor | undefined {
  return DOOR[name];
}

/**
 * **Which card carries the trash** — *Remove this card*, the reader's own dismissal, on the
 * called-off card and on no other ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §5). The other endings' cards carry a score or a strand's verdict and are the record for the
 * day they stay; this one carries nothing the challenge row does not, and it is the one a player
 * wants gone. A `Record` over the union, so widening the trash is a row here and a decision,
 * never a fall-through — the record names it out of scope.
 */
const CLEARABLE: Readonly<Record<GameCardName, boolean>> = {
  planning: false,
  'game-on': false,
  'needs-a-player': false,
  'needs-result': false,
  confirm: false,
  counted: false,
  uncounted: false,
  'never-played': false,
  'called-off': true,
  unreadable: false,
};

export function mayBeCleared(name: GameCardName): boolean {
  return CLEARABLE[name];
}

/**
 * **Whether this card is one of the games that need you** — what Home's badge counts
 * ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)):
 * *a result to enter or confirm, a payment to confirm, a seat open in your game.* Three of those are
 * cards this rail already draws; *a payment to confirm* is the booked game's, and arrives with it.
 *
 * A `Record` over the union, so a new card name is a decision here rather than a fall-through.
 * **`confirm` is the one that cannot be read off the name**: the card is the same in all four
 * `AWAITING_ANSWER` arms, and only two of them wait on you — so it is asked of the caller, which is
 * handed `features/games`' fold (`awaitsYourAgreement`) and crosses it as an answer rather than an
 * import, keeping this module the pure TypeScript it is. It is asked about that card and no other.
 */
const NEEDS_YOU: Readonly<Record<GameCardName, boolean | 'when-a-score-awaits-you'>> = {
  planning: false,
  'game-on': false,
  // A seat open in your game — the fill is yours as much as anybody's on the court.
  'needs-a-player': true,
  // A result to enter: the agreed point is behind the fold.
  'needs-result': true,
  // A result to confirm — only where a score is waiting on your agreement.
  confirm: 'when-a-score-awaits-you',
  counted: false,
  uncounted: false,
  'never-played': false,
  'called-off': false,
  unreadable: false,
};

export function needsYou(name: GameCardName, scoreAwaitsYou: () => boolean): boolean {
  const rule = NEEDS_YOU[name];
  return rule === 'when-a-score-awaits-you' ? scoreAwaitsYou() : rule;
}

/**
 * The plan a game is folded with — its court's row, found by the challenge the game was opened
 * from (ADR-0164 §1), and `undefined` where the list has not landed or holds none.
 */
export function planOf(game: Game, plans: readonly Plan[] | undefined): Plan | undefined {
  return plans?.find((one) => one.challengeId === game.challengeId);
}

/**
 * **How many of the rail's cards need you** — the number on Home's column. The rail's own rows,
 * each folded with its own plan exactly as the rail folds it, so the badge counts the cards Home
 * draws and no others; `scoreAwaitsYou` is `awaitsYourAgreement` for the reader, handed in.
 */
export function gamesNeedingYou(
  games: readonly Game[],
  plans: readonly Plan[] | undefined,
  scoreAwaitsYou: (game: Game) => boolean,
  drawnElsewhere?: ReadonlySet<string>,
): number {
  return railGames(games, drawnElsewhere).filter((game) =>
    needsYou(gameCardName(game, planOf(game, plans)), () => scoreAwaitsYou(game)),
  ).length;
}

/**
 * **The rail's own cards** — the games on the rail (`belongsOnTheRail`) that no other card stands
 * for. A game booked through a group is on `GET /games` too, and its booking's card is drawn first
 * on the rail and counted on Home's column by its own read
 * ([#556](https://github.com/Raketa02/Raketa/issues/556)), so the rail and the badge leave every
 * Game in `drawnElsewhere` out: one game is one card and one count.
 */
export function railGames(
  games: readonly Game[],
  drawnElsewhere: ReadonlySet<string> = NOTHING_ELSEWHERE,
): readonly Game[] {
  return games.filter((game) => belongsOnTheRail(game) && !drawnElsewhere.has(game.gameId));
}

/** Nothing drawn elsewhere: one empty set rather than one per call. */
const NOTHING_ELSEWHERE: ReadonlySet<string> = new Set();

/**
 * **What the game screen's entry arm leads with** — the card's own door, read as a landing.
 *
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.2 lands
 * *Planning* and *Game on* on the plan and *Needs result* on the score grid, and it says why the
 * two tables cannot disagree: **the verb names what you arrive at.** So this is derived from
 * {@link doorOf} rather than written beside it — a second `Record` over the four rungs is a
 * second opinion about where a button goes, and the one that drifted would send a player to a
 * screen that is not what its own button promised.
 *
 * It is here rather than in `features/games` because it reads the ladder, which reads a plan
 * (ADR-0149 §1); what crosses back into that feature is the word and never the rung
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.3 —
 * *"every surface reads it … and the game screen's arm"*).
 */
export function entryLeadOf(court: CourtRead, plan: Plan | undefined): EntryLead {
  return doorOf(rungOf(plan, court)) === 'we-played' ? 'the-score' : 'the-plan';
}

/**
 * **The last instant this game's own record dates, or nothing** — the ending a shelf life is
 * measured from.
 *
 * The wire dates one ending exactly and approximates the others, so the three cases differ:
 *
 * - A game that was **called off** carries `called_off_at`, the act's own instant, and it is
 *   read first because the other two fields cannot date it: `entry_closes_at` is `null` on it —
 *   *the window no longer matters, and a card that shelved itself by it would stay for eight
 *   days* — and `played_at` never is, because a game is called off only while a seat is open and
 *   nothing is recorded on a short court
 *   ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)).
 * - A game that **never happened** ended at `entry_closes_at`, and that is exact: the window
 *   closing *is* the ending.
 * - A game that **was played** carries `played_at` and nothing later — the proposal's deadline and
 *   the acceptance's grace are both gone by the time it is counted or unscored. So the card leaves
 *   a day after somebody said the game happened rather than a day after the argument ended.
 *
 * **The second one has a consequence worth naming, because it is the commonest path.** `played_at`
 * *is* the entry, and silence confirms a score one answer window after the entry — so a game
 * counted by **silence** reaches `CONFIRMED` at almost exactly the moment this shelf runs out, and
 * its *Counted* card is drawn barely or not at all. What is left drawing one is a score somebody
 * **agreed with**, which settles after a grace shorter than the window. That is 24 h from the game
 * rather than 24 h from the argument, and it is the reading §4.1's own cost statement takes —
 * *after a day a finished game and its score are unreachable in this build* — but the clean fix is
 * one field on the contract and one subtraction here, exactly as the challenge inbox's is.
 *
 * The two fields are mutually exclusive on the wire — `entry_closes_at` is `null` once somebody
 * has said it happened — so reading them in this order picks the right one in each case rather
 * than choosing between two candidates.
 */
function endedNoEarlierThan(game: Game): string | undefined {
  return game.calledOffAt ?? game.entryClosesAt ?? game.playedAt;
}

/**
 * Whether this game belongs on the rail at all: still live, or ended in the last day.
 *
 * **An undated ending stays, and so does a standing this build cannot read** — the same two
 * refusals the challenge inbox makes, for the same reason: a card the app cannot describe is not
 * a card it may decide is finished.
 */
export function belongsOnTheRail(game: Game): boolean {
  if (game.standing === undefined) return true;
  if (game.standing === 'AWAITING_ENTRY' || game.standing === 'AWAITING_ANSWER') return true;

  const ended = endedNoEarlierThan(game);
  if (ended === undefined) return true;

  return Date.parse(game.readAt) - Date.parse(ended) < ENDED_CARD_SHELF_LIFE_MS;
}

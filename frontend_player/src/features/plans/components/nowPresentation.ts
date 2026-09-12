/**
 * **Every word Now's rail and its card say** — the heading, the tag's word, the sport word, the
 * slot labels' spoken form, the door's verb, the one line under the slots, and the name a listener
 * gets ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4,
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.6 and §24.5) — and the
 * two tables keyed on the card's name that are not words: the stage's dot, and the accent.
 *
 * The card is **header · slots + court · footer**
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)): a stage chip and the sport word, three
 * plan slots each with a bright-or-dim bar, the court with faces, and two doors. Every slot but
 * the court is written here. It is this feature's for the reason the rail is: the card is a
 * composition naming domain nouns, and the nouns are a plan's
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.4).
 *
 * ## The gloss became a bar
 *
 * The card used to add one sentence — *Still to agree: where*, the next unfilled slot in slot
 * order — and the whole reason it named only the next one was to stay four words on a card whose
 * figure and line had already spent the room. The slots column draws **all three**, and an
 * unfilled one draws `Not agreed yet` under a dim bar, so the sentence would now be the column
 * said again in prose. What survives of it is {@link cardLine}: ***Needs result*'s window**, which
 * is the one live fact a passed agreement leaves, and **the endings' standing**, which is
 * `features/games`' own sentence and the same one the screen behind the card says — so no card
 * loses a fact it drew before.
 *
 * ## The figure and the line went with it, and the hour is still printed once
 *
 * The figure took one of three shapes and the line took whatever it did not, which was the
 * mechanism for *the hour is printed once*. The slots are that mechanism now, by construction:
 * the hour has one row, the day has one row, and neither is anywhere else on the card.
 *
 * ## No absolute instant and no countdown, except the one the window owns
 *
 * A plan is **drawn literally and never counted down** (ADR-0145 §7): its day and its hour are
 * wall-clock facts, and the date beside the weekday is a calendar square rather than an instant.
 * The single duration on this card is *Needs result*'s, and it is folded from `entry_closes_at`
 * against the games list's `read_at` — never against the phone.
 *
 * ## Two tables that are not words live here anyway
 *
 * {@link STAGE_DOT} and {@link ACCENT} are colours and a variant, keyed on the card's name beside
 * the word the same name draws. They are here rather than in the component because they are
 * **decisions about a name** — which stage is still in the players' hands, which is settled — and
 * a `Record` over the union is what makes a tenth name fail `pnpm typecheck` in one file rather
 * than draw a dotless tag in another.
 */

import { gameStandingLine, openSeats, type Game } from '@/features/games/types';
import { counted } from '@/shared/formatting/counted';
import { durationLeft } from '@/shared/formatting/durations';
import { theme, type ButtonVariant } from '@/shared/ui';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';

import type { GameCardName } from '../domain/gameCard';
import { isRung } from '../domain/ladder';
import { PLAN_SLOTS, type Plan, type PlanSlot } from '../domain/slots';

import { SLOT_EYEBROW, spokenSlotValue } from './planPresentation';

// ---------------------------------------------------------------------------
// The rail
// ---------------------------------------------------------------------------

/** The heading over the rail. Drawn uppercase by 3.3's section rule, and never `h2`. */
export const GAMES_HEADING = 'Your games';

/**
 * `YOUR GAMES · n` — **the heading and its count**, which is the one number on this screen.
 *
 * A rail pages through everything it holds, so the count is what says how much there is; the dots
 * under it say where you are, and neither is the other.
 */
export function gamesHeading(count: number): string {
  return `${GAMES_HEADING} · ${count}`;
}

// ---------------------------------------------------------------------------
// The tag — the card's name, and the stage's dot
// ---------------------------------------------------------------------------

/**
 * What the tag says.
 *
 * **The tag is the card's name** ([#324](https://github.com/Raketa02/Raketa/issues/324)), which is
 * affordable here because ADR-0148 §6's refusal was about a **cross-context read** and a game card
 * reads its own standing. On the dark shell every tag is 6.4's `on-dark` pill, so the table holds
 * the word and nothing else: the urgency the light card carried as the pill's `warn` / `ok`
 * variant is the **dot's** now ({@link STAGE_DOT}), with the word beside it — Part 13's *never
 * colour alone*, discharged by the name itself.
 *
 * **A standing this build cannot read draws no tag at all.** There is no name to say and inventing
 * one would name a state; the gap lands in the line instead, which is where the whole line is
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 — *the standing is the
 * whole line*).
 */
export const CARD_TAG: Readonly<Record<GameCardName, string | undefined>> = {
  planning: 'Planning',
  'game-on': 'Game on',
  today: 'Today',
  'needs-result': 'Needs result',
  // The fifth rung, above the clock (#411 rule 5): a seat somebody left, drawn empty on the
  // court beside it. The errand and not the shape — the court says how many.
  'needs-a-player': 'Needs a player',
  confirm: 'Confirm the result',
  counted: 'Counted',
  uncounted: 'Uncounted',
  'never-played': 'Never played',
  'called-off': 'Called off',
  unreadable: undefined,
};

/**
 * **The dot is the stage's** — the one surface on which a `Tag`'s dot is not a sport's
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * 6.4 fixed the dot as *the sport's, and only the sport's*, on the argument that a token with two
 * meanings stops meaning either. That argument holds: the sport moved to a **word** in the header,
 * so on this card the dot has one meaning, and it is the stage's. Three colours for three facts —
 * `arranging` while the game is still in the players' hands (a plan to finish, a seat to fill, a
 * result to enter, an answer owed), `mint` where it is settled (the plan complete, the day here,
 * the score counted), and the quiet hairline on the three endings nobody scored. A card with no tag
 * has no dot to colour.
 */
export const STAGE_DOT: Readonly<Record<GameCardName, string | undefined>> = {
  planning: theme.color.arranging,
  'game-on': theme.color.mint,
  today: theme.color.mint,
  'needs-result': theme.color.arranging,
  'needs-a-player': theme.color.arranging,
  confirm: theme.color.arranging,
  counted: theme.color.mint,
  uncounted: theme.color.onDarkHair,
  'never-played': theme.color.onDarkHair,
  'called-off': theme.color.onDarkHair,
  unreadable: undefined,
};

/**
 * **The card's name where it follows something else on one line** — `Padel · planning`, the
 * conversation header's sub-line ([#401](https://github.com/Raketa02/Raketa/issues/401)).
 *
 * A second table rather than `CARD_TAG[name].toLowerCase()` at the call site, because the
 * lowering is a decision about **words** and belongs where the words are: *Game on* → *game on* is
 * right, and a name that ever holds a proper noun would be wrong the same way, silently, on every
 * surface that lowered it. `nowPresentation.test.ts` holds the two tables equal *until* that day,
 * so they cannot drift apart by accident and can only part on purpose.
 *
 * It is the **same vocabulary as the tag** — the four rungs and the endings, folded at read time
 * from data the surface already holds — and not the standing `features/games` reads. What crosses
 * the feature boundary is a **card name** and the word for it, and never a standing
 * ([ADR-0157](../../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)).
 * A card the tag has no name for has no word here either: the header draws the sport alone
 * rather than inventing a state.
 */
const CARD_STATE_WORD: Readonly<Record<GameCardName, string | undefined>> = {
  planning: 'planning',
  'game-on': 'game on',
  today: 'today',
  'needs-result': 'needs result',
  'needs-a-player': 'needs a player',
  confirm: 'confirm the result',
  counted: 'counted',
  uncounted: 'uncounted',
  'never-played': 'never played',
  'called-off': 'called off',
  unreadable: undefined,
};

export function cardStateWord(name: GameCardName): string | undefined {
  return CARD_STATE_WORD[name];
}

// ---------------------------------------------------------------------------
// The accent — the settled bar and the wide button, from one row
// ---------------------------------------------------------------------------

/** The bar's bright colour, and the variant of the wide button under it. One row, never two. */
export interface CardAccent {
  readonly bar: string;
  readonly button: ButtonVariant;
}

/**
 * **The accent by name** — the colour a settled slot's bar is drawn in, and the variant of the
 * wide door beneath the slots ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * One table for both, so a card cannot draw a volt bar over a mint door: the bar says *the plan
 * is settled here* and the button says what to do next, and they are one accent because they are
 * one card. **Volt on Planning** — the card that is about settling the plan, and the design's own
 * lime — which gives volt a meaning on this card it had nowhere else: a bright bar is a slot
 * everybody has agreed. It stays off `primary`; 1.2's coral list is closed.
 *
 * **Mint on everything else, as a soft default.** The real look of the other eight cards is not
 * in #410 — the author supplies it — and until then every card is drawn by this shell in the
 * palette's settled colour so the rail does not mix two visual languages, and a game flipping to
 * *Game on* under your thumb does not jump layouts.
 *
 * **`settled`, and not a `mint` variant invented beside it.** 6.1's `settled` is the mint button
 * and the only one: its fill is `mintInk`, which is what Rule C requires under a white label, and
 * that is the whole of what this card asks of it. Its docstring's clause about a second press is
 * about the location step's control, whose *act* is what has been obtained; here the settled thing
 * is the game — a full court, everybody in — and the label carries the verb, which is 6.1's own
 * split (*a control that turns green must also change its words*). A `mint` variant whose every
 * style equalled `settled`'s would be a colour-named copy of a meaning-named control, kept only
 * until a design replaces it — the second card `shared/ui/README.md` refuses.
 */
export const ACCENT: Readonly<Record<GameCardName, CardAccent>> = {
  planning: { bar: theme.color.volt, button: 'volt' },
  'game-on': { bar: theme.color.mint, button: 'settled' },
  today: { bar: theme.color.mint, button: 'settled' },
  'needs-result': { bar: theme.color.mint, button: 'settled' },
  'needs-a-player': { bar: theme.color.mint, button: 'settled' },
  confirm: { bar: theme.color.mint, button: 'settled' },
  counted: { bar: theme.color.mint, button: 'settled' },
  uncounted: { bar: theme.color.mint, button: 'settled' },
  'never-played': { bar: theme.color.mint, button: 'settled' },
  'called-off': { bar: theme.color.mint, button: 'settled' },
  unreadable: { bar: theme.color.mint, button: 'settled' },
};

// ---------------------------------------------------------------------------
// The sport word
// ---------------------------------------------------------------------------

/** The marked kind, and the only one that is said. A counted game says nothing about being one. */
const FRIENDLY = 'Friendly';

/**
 * The sport word's parts — the sport, and `Friendly` only when the game is one.
 *
 * **Nothing here says *singles* or *doubles*: the court says the format** — four squares is a
 * four and two is a two — and a word restating a picture directly beside it is the doubling the
 * figure and the line were once split to prevent. *Friendly* is the marked case (ADR-0150),
 * because a `GameKind` this build cannot read drops the clause and every other word on the card
 * stands — a game whose kind is absent is drawn as a game.
 */
function sportParts(game: Game, sportName: string): readonly string[] {
  return game.kind === 'FRIENDLY' ? [sportName, FRIENDLY] : [sportName];
}

/**
 * `Padel` · `Padel · Friendly` — **the sport word, top right, as it is drawn.** Uppercase is the
 * eyebrow's own rule and is applied by the style, so the words are stored as words.
 */
export function sportWord(game: Game, sportName: string): string {
  return sportParts(game, sportName).join(' · ');
}

/**
 * The same, **spoken** — `Padel, friendly`. A clause rather than the drawn row, because a `·`
 * between two words is a separator a listener has no reading for.
 */
export function sportSpoken(game: Game, sportName: string): string {
  const [sport, ...marks] = sportParts(game, sportName);

  return [sport, ...marks.map((mark) => mark.toLowerCase())].join(', ');
}

// ---------------------------------------------------------------------------
// The line under the slots
// ---------------------------------------------------------------------------

/**
 * **The one line the card keeps** — the window on *Needs result*, and the standing on everything
 * that is not a rung. `undefined` on the three rungs whose whole account is the slots.
 *
 * ***Needs result* is the override that survived the gloss**, because a passed agreement makes the
 * unfilled slots irrelevant and the entry window is the only live fact left. It **obeys nothing**:
 * the card does not close at zero, because `standing_of` gates entry on `entry_closes_at` and the
 * server derives the standing. Where the wire dated no window, somebody has already said the game
 * happened and there is nothing left to count down — so nothing is drawn, where a duration of
 * nothing would be a lie.
 *
 * **Everything that is not a rung already has a sentence**, and it is `features/games`'
 * `gameStandingLine` — the same line the screen behind the card says, so a player who reads a
 * card, taps it and finds a different deadline is not a state this can reach. The membership test
 * is the ladder's own rather than a cascade over the four names: a fifth rung spelled there and not
 * here would fall through to the sentence written for an ended game, which is the one failure a
 * single rule exists to prevent.
 */
export function cardLine(name: GameCardName, { game, playerId }: CardFacts): string | undefined {
  if (name === 'needs-result') {
    return game.entryClosesAt === undefined
      ? undefined
      : `${durationLeft(game.entryClosesAt, game.readAt)} left`;
  }

  if (isRung(name)) return undefined;

  return gameStandingLine(game, playerId);
}

/** The three facts a card is composed from — the game, the plan beside it, and who is reading. */
export interface CardFacts {
  readonly game: Game;
  readonly plan: Plan | undefined;
  readonly playerId: string;
}

// ---------------------------------------------------------------------------
// The footer
// ---------------------------------------------------------------------------

/**
 * **The wide door on Planning** — the next thing to do, on the card that is about doing it.
 *
 * It opens the game screen exactly as *Game on*'s `Open` does — the door is `open` on both, and
 * `domain/gameCard.ts` says so — and the word differs because the destination is the same and the
 * reason for going is not: on *Game on* you go to read a plan, on *Planning* you go to finish one.
 * *Finish* and not *Lock*, because the lock is an act with its own control on that screen
 * (ADR-0155), and a door that named it would be promising a button it does not press.
 */
export const FINISH_THE_PLAN = 'Finish the plan';

/**
 * **The wide door's verb, per name** — §22.7's three, one per rung, and *Finish the plan* on the
 * card whose door is `open` but whose errand is not
 * ([#413](https://github.com/Raketa02/Raketa/issues/413)).
 *
 * Keyed by the **card's name** rather than by the door, because the door *Planning* carries is
 * the same `open` as *Game on*'s and the word on it is not. Each carries its act's **verb**,
 * navigates, and never writes: *the grid is the screen*, so the verb names what you arrive at and
 * the standing guarantees you arrive there. `nowPresentation.test.ts` holds this table in step
 * with `domain/`'s `DOOR` — a word exactly where there is a door — so neither can gain a row the
 * other lacks.
 */
const DOOR_LABEL: Readonly<Record<GameCardName, string | undefined>> = {
  planning: FINISH_THE_PLAN,
  'game-on': 'Open',
  // The same `open` door as *Game on*'s, under the same word, until #419 turns it into *Fill the
  // seat*: the screen is where the seat is dealt with, and no dead door ships in the meantime.
  'needs-a-player': 'Open',
  // *One act, one spelling* (§22.7). The screen behind this card draws the same verb on the arm
  // that leads with its plan, so the word is `shared/vocabulary/theActsWords.ts`' rather than
  // either feature's — the two of them reach each other at load time, and a word read across that
  // seam while a module is being evaluated reads a half-built one.
  today: WE_PLAYED,
  'needs-result': WE_PLAYED,
  confirm: 'Confirm the result',
  counted: undefined,
  uncounted: undefined,
  'never-played': undefined,
  'called-off': undefined,
  unreadable: undefined,
};

export function doorLabel(name: GameCardName): string | undefined {
  return DOOR_LABEL[name];
}

// ---------------------------------------------------------------------------
// What a card announces
// ---------------------------------------------------------------------------

/**
 * **One slot, spoken** — `Where, Zabłocie Sport, court 3` · `Day, Sunday 9 Aug` · `Time, 19:00` ·
 * `Day, Not agreed yet`.
 *
 * `planTagsName`'s register one surface over: the slot is named because a listener hears three
 * values in a row and has nothing to attach them to, and the comma rather than a colon because
 * this is prose and the chip's is a control's name. The value is `spokenSlotValue`'s — the one
 * spelling every spoken slot reads — asked for **with its date**, because this is the one surface
 * that draws one. The **place is spoken whole**, comma and court and all (§20.4) — the drawn row
 * shortens it, and this is the half the drawing cannot keep. The card's own labels are used, so a
 * listener hears *Time* where the card draws `TIME`.
 */
export function cardSlotSpoken(plan: Plan | undefined, slot: PlanSlot): string {
  return `${SLOT_EYEBROW[slot]}, ${spokenSlotValue(plan, slot, { date: true })}`;
}

/**
 * **The gap in the court, said** — `An open seat` · `2 open seats` — and nothing on a full court.
 *
 * The court is drawn into a hidden subtree and the tag names the errand, so without this a
 * listener would hear *Needs a player* and have no idea how short the court is. Counted from
 * `openSeats`, the one definition of *open*; the singular is an article rather than a `1`,
 * because this is a clause in prose and not a legend.
 */
export function openSeatsSpoken(game: Game): string | undefined {
  const open = openSeats(game.seats).length;
  if (open === 0) return undefined;

  return open === 1 ? 'An open seat' : counted(open, 'open seat', 'open seats');
}

/**
 * The card, as one element: **the tag, the sport, the open seat where there is one, the three
 * slots as sentences, then the line.**
 *
 * §24.5 as amended by [#413](https://github.com/Raketa02/Raketa/issues/413). The **sport** is
 * named because a listener has no picture of the court in front of them, and it is what tells two
 * padel games in a week apart — and the **open seat** is named for the same reason, one clause
 * after it. **The door's verb is no longer part of this name**: the body is not pressable, the two
 * buttons are the only doors and each is an element of its own — so a name ending in `Open`
 * beside a button announcing `Open` would be the double announcement 6.8 refuses.
 *
 * The slots are spoken in the app's own order, read from `slots.ts` rather than restated here.
 */
export function gameCardLabel({
  name,
  sportName,
  game,
  plan,
  playerId,
}: CardFacts & {
  readonly name: GameCardName;
  readonly sportName: string;
}): string {
  return [
    CARD_TAG[name],
    sportSpoken(game, sportName),
    openSeatsSpoken(game),
    ...PLAN_SLOTS.map((slot) => cardSlotSpoken(plan, slot)),
    cardLine(name, { game, plan, playerId }),
  ]
    .filter((part): part is string => part !== undefined)
    .map((part) => (part.endsWith('.') ? part : `${part}.`))
    .join(' ');
}

/**
 * The court inside the card, said once and then hidden.
 *
 * `Court` requires a summary because four seats announced against nothing are four seats a
 * listener cannot place. Here the card around it is the element, so this sentence is drawn into a
 * hidden subtree and never heard — it is passed because the component's contract asks for it, and
 * the honest one to pass is the one that would be true if it were.
 */
export function cardCourtSummary(sportName: string, seats: number): string {
  return `${sportName}, ${seats} seats.`;
}

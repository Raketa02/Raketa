/**
 * **Every word Now's rail and its card say** — the heading, the tag, the eyebrow, the figure, the
 * line and the gloss, plus the two names a listener gets
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4,
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.6 and §24.5).
 *
 * The card is **tag · eyebrow · figure · line · gloss · court · footer**, and every slot but the
 * court is written here. It is this feature's for the reason the rail is: the card is a
 * composition naming domain nouns, and the nouns are a plan's
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.4).
 *
 * ## The gloss is one rule for three rungs, and one override
 *
 * > **Name the next slot still to agree, in ADR-0144's order — and *Needs result* overrides it
 * > with the time left.**
 *
 * Naming only the **next** slot is what keeps it four words, and it hands the fuller account to
 * the game screen's checklist ([#368](https://github.com/Raketa02/Raketa/issues/368)), which is
 * the one place the whole list is printed. Deriving it from the slot count alone is what stops
 * there being a fourth string to keep in step with the ladder — ***Today* uses the slot rule, and
 * it is the case that justifies it**: #324's second amendment dropped *Today*'s three-slot
 * requirement, so a *Today* card may genuinely have no hour, and `Still to agree: the hour` on the
 * morning of the game is exactly the alarm a player wants.
 *
 * ***Needs result* overrides**, because a passed agreement makes the unfilled slots irrelevant and
 * the entry window is the only live fact left. It **obeys nothing**: the card does not close at
 * zero, because `standing_of` gates entry on `entry_closes_at` and the server derives the standing.
 *
 * **Everything that is not one of the four rungs already has a sentence**, and it is
 * `features/games`' `gameStandingLine` — the same line the screen behind the card says, so a
 * player who reads a card, taps it and finds a different deadline is not a state this can reach.
 *
 * ## The hour is printed once, and that is what the figure and the line are for
 *
 * The design draws `19:30` in the figure and then `Yesterday · 19:30` beneath it, which is the
 * same doubling as its own *"answer by Tomorrow · 17:00 17:00"*. So the figure takes one of three
 * shapes and **the line takes whatever the figure did not**.
 *
 * The **place** is the one value that can overflow, so it is drawn through #335's *shorter value,
 * not a second line* and **spoken whole**, which is §20.4 one surface over — the same split
 * `planPresentation.ts` already makes for the chip.
 *
 * ## No absolute instant and no countdown, except the one the window owns
 *
 * A plan is **drawn literally and never counted down** (ADR-0145 §7): its day and its hour are
 * wall-clock facts. The single duration on this card is *Needs result*'s, and it is folded from
 * `entry_closes_at` against the games list's `read_at` — never against the phone.
 */

import { gameStandingLine, type Game } from '@/features/games/types';
import { durationLeft } from '@/shared/formatting/durations';
import { placeWithoutTheCourt } from '@/shared/formatting/placeName';
import type { TagVariant } from '@/shared/ui';
import { WE_PLAYED } from '@/shared/vocabulary/theActsWords';

import type { GameCardName, GameDoor } from '../domain/gameCard';
import { isRung } from '../domain/ladder';
import { unfilledSlots, type Plan } from '../domain/slots';

import { SLOT_IN_A_SENTENCE, STILL_TO_AGREE, dayChipName } from './planPresentation';

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
// The tag — the card's name
// ---------------------------------------------------------------------------

/**
 * What the tag says, and what tone it says it in.
 *
 * **The tag is the card's name** ([#324](https://github.com/Raketa02/Raketa/issues/324)), which is
 * affordable here because ADR-0148 §6's refusal was about a **cross-context read** and a game card
 * reads its own standing. **The dot is the sport's and urgency is the tag's variant** (#338 §4):
 * a token with two meanings stops meaning either, so the amber is the whole pill and the word is
 * beside it — which is also Part 13's *never colour alone*, discharged by the name itself.
 *
 * `warn` is the three cards a clock is running on — the day is today, the window is closing, an
 * answer is owed — and `ok` the two that are settled. *Planning* and the two quiet endings are
 * `base`: **an unscored game reads as an evening, not an error**, so neither of them is red and
 * neither is amber.
 *
 * **A standing this build cannot read draws no tag at all.** There is no name to say and inventing
 * one would name a state; the gap lands in the gloss instead, which is where the whole line is
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 — *the standing is the
 * whole line*).
 */
export const CARD_TAG: Readonly<
  Record<GameCardName, { readonly label: string; readonly variant: TagVariant } | undefined>
> = {
  planning: { label: 'Planning', variant: 'base' },
  'game-on': { label: 'Game on', variant: 'ok' },
  today: { label: 'Today', variant: 'warn' },
  'needs-result': { label: 'Needs result', variant: 'warn' },
  confirm: { label: 'Confirm the result', variant: 'warn' },
  counted: { label: 'Counted', variant: 'ok' },
  uncounted: { label: 'Uncounted', variant: 'base' },
  'never-played': { label: 'Never played', variant: 'base' },
  unreadable: undefined,
};

// ---------------------------------------------------------------------------
// The eyebrow
// ---------------------------------------------------------------------------

/** The two shapes of court, read off the seats the game actually has. */
const SINGLES = 'Singles';
const DOUBLES = 'Doubles';

/** The marked kind, and the only one that is said. A counted game says nothing about being one. */
const FRIENDLY = 'Friendly';

/** How many seats a singles court has. Two, and the boundary between the two words above. */
const SINGLES_SEATS = 2;

/**
 * `DOUBLES · FRIENDLY` — **the eyebrow carries only facts this build holds.**
 *
 * §4.2 lists a third clause, `YOU OWN IT`, and it **goes with ownership**: nothing on this
 * platform owns a game, *Needs an owner* is one of the seven refused states, and the app does not
 * name a thing it cannot do.
 *
 * *Friendly* is the marked case, because a `GameKind` this build cannot read drops the clause and
 * every other word on the card stands — a game whose kind is absent is drawn as a game.
 */
function eyebrowParts(game: Game): readonly string[] {
  const court = game.seats.length <= SINGLES_SEATS ? SINGLES : DOUBLES;

  return game.kind === 'FRIENDLY' ? [court, FRIENDLY] : [court];
}

/** The eyebrow as it is **drawn**: the parts, in the row's own separator. */
export function cardEyebrow(game: Game): string {
  return eyebrowParts(game).join(' · ');
}

// ---------------------------------------------------------------------------
// The figure and the line
// ---------------------------------------------------------------------------

/**
 * The card's one large slot: **the hour, a weekday, or nothing.**
 *
 * The `kind` travels because the two are drawn in different type roles — 1.4 is categorical that
 * numbers are monospaced always, so an hour is `num` and a weekday is 3.3's `display`, the one
 * sans role above `h1` and the one that exists for exactly this. A component branching on
 * `/^\d/` would be that decision made by a regular expression.
 */
export type CardFigure =
  | { readonly kind: 'hour'; readonly value: string }
  | { readonly kind: 'weekday'; readonly value: string };

/**
 * What the figure holds, and `undefined` where a plan names no moment at all.
 *
 * **§4.2's three shapes are a partition over (hour, day) and are read as one**: *the hour*; *the
 * weekday when there is a day and no hour*; *nothing when there is no day*. The third clause is
 * the remaining cell — no hour **and** no day — because the second names its own hour condition
 * and the first does not. The other reading, in which an hour agreed before a day draws nothing,
 * would take an agreed value off the card entirely, and the line does not pick it up: the line is
 * *whatever the figure did not*, and it never carries the hour.
 *
 * **The weekday is the weekday, and never *Today* or *Yesterday*.** Inside the horizon a weekday
 * is exact, and inside 24 h — which is all an ending gets — it can only be today or yesterday
 * anyway, so the format needs no fallback for a game ten days old. What it must not do is say
 * *Today* on a card whose **tag** already says *Today*: that is the same doubling the figure and
 * the line were split to prevent, one register over.
 */
export function cardFigure(plan: Plan | undefined): CardFigure | undefined {
  if (plan?.hour !== undefined) return { kind: 'hour', value: plan.hour };
  if (plan?.day !== undefined) return { kind: 'weekday', value: dayChipName(plan.day) };

  return undefined;
}

/**
 * The line under the figure: **whatever the figure did not take** — the day, and the place.
 *
 * `place` is the **drawn** half, shortened by #335's rule; {@link cardLineSpoken} is the same line
 * with the value whole. A plan with nothing agreed has no line at all rather than an empty one.
 */
export function cardLine(plan: Plan | undefined): string | undefined {
  return joinLine(plan, (place) => placeWithoutTheCourt(place));
}

/** The same line, **spoken** — the place whole, comma and court and all (§20.4). */
export function cardLineSpoken(plan: Plan | undefined): string | undefined {
  return joinLine(plan, (place) => place);
}

function joinLine(plan: Plan | undefined, place: (written: string) => string): string | undefined {
  const parts: string[] = [];

  // The day, only where the figure took the hour instead — the doubling this split exists to stop.
  if (plan?.day !== undefined && plan.hour !== undefined) parts.push(dayChipName(plan.day));
  if (plan?.place !== undefined) parts.push(place(plan.place));

  return parts.length === 0 ? undefined : parts.join(' · ');
}

// ---------------------------------------------------------------------------
// The gloss
// ---------------------------------------------------------------------------

/**
 * The gloss where the checklist is empty. Said on *Game on*, and on *Today* once it is.
 *
 * **Not the checklist's sentence**, which is `NOTHING_IS_LEFT_TO_AGREE` and ends in a full stop:
 * a card's gloss is a label under a figure and the screen's is a line of prose, and §22.6 spells
 * the two differently on purpose.
 */
export const NOTHING_LEFT_TO_AGREE = 'Nothing left to agree';

/**
 * What the card's gloss says — **one rule for three rungs, one override, and the built sentence
 * for everything else.**
 *
 * It must add what the tag, the figure and the line have not, and must not restate the button.
 */
export function cardGloss(name: GameCardName, { game, plan, playerId }: CardFacts): string {
  if (name === 'needs-result' && game.entryClosesAt !== undefined) {
    return `${durationLeft(game.entryClosesAt, game.readAt)} left`;
  }

  // **The ladder's own membership test, and never a cascade over the four names.** A fifth rung
  // spelled here and not there would fall through to the sentence written for an ended game, which
  // is the one failure the gloss being *one rule for three rungs* exists to prevent.
  //
  // *Needs result* reaches the slot rule only where the wire dated no window, which is a game
  // somebody has already said happened — the entry closed, and there is nothing left to count
  // down. The slot sentence is true of it, where a duration of nothing would not be.
  if (isRung(name)) {
    const next = unfilledSlots(plan)[0];

    return next === undefined
      ? NOTHING_LEFT_TO_AGREE
      : `${STILL_TO_AGREE}: ${SLOT_IN_A_SENTENCE[next]}`;
  }

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
 * **The named door in the footer** — §22.7's three, one per rung.
 *
 * Each carries its act's **verb**, navigates, and never writes: *the grid is the screen*, so the
 * verb names what you arrive at and the standing guarantees you arrive there.
 */
const DOOR_LABEL: Readonly<Record<GameDoor, string>> = {
  open: 'Open',
  // *One act, one spelling* (§22.7). The screen behind this card draws the same verb on the arm
  // that leads with its plan, so the word is `shared/vocabulary/theActsWords.ts`' rather than
  // either feature's — the two of them reach each other at load time, and a word read across that
  // seam while a module is being evaluated reads a half-built one.
  'we-played': WE_PLAYED,
  confirm: 'Confirm the result',
};

export function doorLabel(door: GameDoor): string {
  return DOOR_LABEL[door];
}

// ---------------------------------------------------------------------------
// What a card announces
// ---------------------------------------------------------------------------

/**
 * The card, as one element: **the tag, the eyebrow, the figure and line, the gloss, then the
 * door's verb.**
 *
 * §24.5, with the **sport** named in the eyebrow's clause — a listener has no picture of the court
 * in front of them, and a sport dot is legal in this system only where the sport is named
 * (`theme.ts`: *"a surface that draws one of these with no name beside it reopens the question as
 * surely as a fifth sport"*). The drawing names it under the court; the label names it here.
 *
 * **The door's verb is part of this name and is not an element of its own.** The body tap and the
 * named door go to the same place — #336 made that a rule — so they are one action and one
 * element, and the ✉ beside them is the second because it goes somewhere else.
 *
 * The place is spoken **whole** and the figure is spoken as it is drawn: the hour and the weekday
 * are both already words a listener can act on.
 */
export function gameCardLabel({
  name,
  sportName,
  game,
  plan,
  playerId,
  door,
}: CardFacts & {
  readonly name: GameCardName;
  readonly sportName: string;
  readonly door: GameDoor | undefined;
}): string {
  const tag = CARD_TAG[name];
  const figure = cardFigure(plan);
  const line = cardLineSpoken(plan);

  return [
    tag?.label,
    // Spoken as a clause rather than as the drawn row: a `·` between two words is a separator a
    // listener has no reading for, and the sport leads because it is what tells two padel games
    // in a week apart.
    [sportName, ...eyebrowParts(game).map((part) => part.toLowerCase())].join(', '),
    figure?.value,
    line,
    cardGloss(name, { game, plan, playerId }),
    door === undefined ? undefined : doorLabel(door),
  ]
    .filter((part): part is string => part !== undefined)
    .join('. ');
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

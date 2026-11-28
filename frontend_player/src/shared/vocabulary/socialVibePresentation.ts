/**
 * **How much a For-fun table shares, in a word** — the Social vibe's four bands
 * ([ADR-0207](../../../../docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
 * §8, [#838](https://github.com/Rakieta02/Rakieta/issues/838)).
 *
 * The words are written in [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §33.
 *
 * ## Beside the forecast's bands, and never its colours
 *
 * The Social vibe is For fun's headline number where the forecast is Competitive's (ADR-0207 §5),
 * so its bands sit beside `balancePresentation`'s, below every feature that draws the number: the
 * deck card, the Social vibe card (#840), the Friends card and Post a game's fits (#842). **One
 * ladder drives both the word and the tone**, from one hue family — volt, a dimmed volt, then grey.
 * The forecast's green / amber / red is not reused: a vibe is not a verdict, and *Fresh mix* is not
 * a bad game.
 *
 * **The thresholds are the app's presentation** (ADR-0207 §8). The server sends only the %, and the
 * breaks can be tuned here once real numbers exist, with no ruleset release. Which colour each tone
 * is belongs to the surface that draws it (`SocialVibeRow`), as `BALANCE_FIGURE` is the bar's.
 *
 * **The percentage is the server's and is never derived here.** It is worked out from everybody's
 * tags now, on every read; this file only says what it is called.
 */

import { socialTagName } from './socialTagPresentation';
import type { SocialTagId } from './socialTags';

/** The three tones a band is drawn in. Never `ok` / `warn` / `bad`: they would mean a verdict. */
export type SocialVibeTone = 'volt' | 'dimVolt' | 'grey';

/** A band: the word said beside the number, and the tone it is drawn in. */
export interface SocialVibeBand {
  readonly word: string;
  readonly tone: SocialVibeTone;
}

/** The name the row carries inside its bar and leads its spoken name with. */
export const SOCIAL_VIBE = 'Social vibe';

/**
 * The bands' floors, in the order they are tested — 70 / 45 / 20 (ADR-0207 §8).
 *
 * A list of pairs rather than a `Record`, for `balancePresentation`'s reason: the value that decides
 * a band is a threshold, and an ordered vocabulary keeps its order where a reader can see it.
 */
const BANDS: readonly (readonly [number, SocialVibeBand])[] = [
  [70, { word: 'Great vibe', tone: 'volt' }],
  [45, { word: 'Good vibe', tone: 'volt' }],
  [20, { word: 'Some common ground', tone: 'dimVolt' }],
];

/** Below every floor. Named rather than inlined, so the fourth band is as findable as three. */
const FRESH_MIX: SocialVibeBand = { word: 'Fresh mix', tone: 'grey' };

/**
 * **The figure every mark draws** — the served %, held to 0–100 and whole. The server sends a whole
 * 0–100, so this only holds a slip to the scale rather than drawing *130%*, and it is applied once,
 * before anything is banded, printed or said, so the figure, its band and its words never disagree.
 */
export function socialVibeShown(pct: number): number {
  return Math.round(Math.min(100, Math.max(0, pct)));
}

/**
 * *Great vibe* · *Good vibe* · *Some common ground* · *Fresh mix*, each with its tone.
 *
 * `pct` is the served Social vibe, a whole percent; a value between two floors takes the lower
 * band, as the forecast's word does.
 */
export function socialVibeBand(pct: number): SocialVibeBand {
  return BANDS.find(([floor]) => pct >= floor)?.[1] ?? FRESH_MIX;
}

/**
 * **The row, spoken** — *Social vibe, 82 percent, Great vibe* (ADR-0207 §8).
 *
 * The figure is said as words, not read off `82%`, and rounded the one way this app rounds a
 * percentage (`formatPercent`), so the spoken number is the drawn one.
 */
export function socialVibeSpoken(pct: number): string {
  return `${SOCIAL_VIBE}, ${Math.round(pct)} percent, ${socialVibeBand(pct).word}`;
}

// ---------------------------------------------------------------------------
// The Social vibe card — its columns and its rows (#840; ADR-0207 §6, for fun 7)
// ---------------------------------------------------------------------------

/** Your column's name: you are *You*, the others their nicknames. */
export const SOCIAL_VIBE_YOU = 'You';

/** An account that can no longer be named heads its column as a tile names it. */
const UNNAMED = '?';

/**
 * **A column's name, as drawn** — *You*, or the nickname whole: the column shortens it with an
 * ellipsis where it is long, so a name is never cut in the words.
 */
export function socialVibeColumnName(column: SocialVibeCarrier): string {
  if (column.isYou) return SOCIAL_VIBE_YOU;
  return column.name ?? UNNAMED;
}

/** Somebody at the table, as a row's spoken name needs them: you, or their nickname. */
export interface SocialVibeCarrier {
  readonly isYou: boolean;
  /** Absent for an account that can no longer be named. */
  readonly name?: string;
}

/**
 * **A row of the grid, spoken** — *Stays for a drink: you, kuba.w* (ADR-0207 §6).
 *
 * The tag's words without its emoji (`socialTagName`: a glyph read aloud describes the layout),
 * then everybody who carries it, in the columns' order — you first. A nickname is said whole, as
 * its owner wrote it; an account no longer named is *somebody*, as the deck's sides say it. The
 * grid's dots are drawn for the eye; this is the same fact for the ear, so a listener hears who
 * shares each of their tags without a column to read down.
 */
export function socialVibeRowSpoken(
  tag: SocialTagId,
  carriers: readonly SocialVibeCarrier[],
): string {
  const who = carriers.map((one) => (one.isYou ? 'you' : (one.name ?? 'somebody')));
  return `${socialTagName(tag)}: ${who.join(', ')}`;
}

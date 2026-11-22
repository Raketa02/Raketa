/**
 * **How much a For-fun table shares, in a word** — the Social vibe's four bands
 * ([ADR-0207](../../../../docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
 * §8, [#838](https://github.com/Raketa02/Raketa/issues/838)).
 *
 * The words are written in [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §33.
 *
 * ## Beside the forecast's bands, and never its colours
 *
 * The Social vibe is For fun's headline number where the forecast is Competitive's (ADR-0207 §5),
 * so its bands sit beside `balancePresentation`'s, below every feature that draws the number: the
 * deck card today, the Friends card, Post a game's fits and the Social vibe card next. **One ladder
 * drives both the word and the tone**, from one hue family — volt, a dimmed volt, then grey. The
 * forecast's green / amber / red is not reused: a vibe is not a verdict, and *Fresh mix* is not a
 * bad game.
 *
 * **The thresholds are the app's presentation** (ADR-0207 §8). The server sends only the %, and the
 * breaks can be tuned here once real numbers exist, with no ruleset release. Which colour each tone
 * is belongs to the surface that draws it (`SocialVibeRow`), as `BALANCE_FIGURE` is the bar's.
 *
 * **The percentage is the server's and is never derived here.** It is worked out from everybody's
 * tags now, on every read; this file only says what it is called.
 */

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

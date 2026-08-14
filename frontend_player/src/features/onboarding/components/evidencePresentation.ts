/**
 * How the evidence trail is drawn — and only that.
 *
 * The trail's words are the server's: every label, detail and sentence is authored there so
 * wording can be corrected without an App Store release, and every direction is computed by
 * the engine from that category's own evidence against the final estimate, so retuning a
 * constant moves the explanation with it. **This file decides nothing about the rating.** It
 * answers one question per row: how do I draw what I was sent?
 *
 * **Render uniformly, emphasise what you recognise.** Two keys have a treatment of their
 * own; everything else takes the default. **An unrecognised key renders with the default
 * treatment and is never dropped** — old app versions live on real phones for months, and a
 * key the engine adds next week has to reach a phone that last updated in the spring. That
 * is a correctness requirement, not a nicety: a widener silently missing from the trail
 * would leave a player reading a range that nothing on the screen accounts for.
 *
 * The same rule applies to a direction, and there the fallback is *no mark at all* rather
 * than a default one. A word this build cannot read is not grounds for drawing an arrow —
 * the row still shows what the category said, which is the part the client did not invent.
 */

import type { NoteVariant } from '@/shared/ui';

/**
 * The engine's widener keys, as of this build. They are matched, never authored: what a key
 * *means* is the server's `label` and `detail`, and neither is restated here.
 */
const CONTRADICTION = 'answers-disagreed';
const TIME_AWAY = 'time-away';

/**
 * A contradiction is `amber` — *watch this, reversible, not yet wrong*. It is emphatically
 * not `coral` and not `red`: the app did not pick a side and is not accusing anybody, and a
 * failure colour would read as one. Time away is `info`, which explains rather than states.
 * Everything else is `base`.
 */
const VARIANT_BY_KEY: Readonly<Record<string, NoteVariant>> = {
  [CONTRADICTION]: 'amber',
  [TIME_AWAY]: 'info',
};

export function widenerVariant(key: string): NoteVariant {
  return VARIANT_BY_KEY[key] ?? 'base';
}

export interface DirectionMark {
  /** A shape, so the direction survives not being able to see colour. */
  readonly glyph: string;
  /** And a word, because a shape alone is not readable either. */
  readonly word: string;
  /** The same fact in a sentence, for the row's accessible name. */
  readonly spoken: string;
}

const MARKS: Readonly<Record<string, DirectionMark>> = {
  up: { glyph: '▲', word: 'Above', spoken: 'above your level' },
  down: { glyph: '▼', word: 'Below', spoken: 'below your level' },
  neutral: { glyph: '—', word: 'In line', spoken: 'in line with your level' },
};

/** `undefined` for a direction this build cannot read — the row draws without a mark. */
export function directionMark(direction: string): DirectionMark | undefined {
  return MARKS[direction];
}

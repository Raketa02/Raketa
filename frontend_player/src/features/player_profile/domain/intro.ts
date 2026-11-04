/**
 * The **intro**: one line a player writes about themselves, and the rules it is held to
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md);
 * the cap from [ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §9).
 *
 * At most 250 characters after trimming, no line break, in any language — and
 * **optional**: a player who skips has no intro, not an empty one. It is the first free text
 * this platform shows a stranger, and the fence that made that admissible is the backend's:
 * a line carrying a phone number, an email, a URL or an `@handle` is refused at the write,
 * with one coarse reason and never the pattern it matched.
 *
 * ## Two of the three reasons are shape, and this side sees them coming
 *
 * `too_long` and `multiline` are facts about the string a player can watch themselves
 * produce, so the step reads them off the draft and shuts *Next* rather than letting somebody
 * walk six screens to be sent back to this one. `contains_contact` is the pattern, and the
 * pattern is deliberately not restated here — a client's copy of it would be a staler one on
 * every phone the day it is tuned from a refusal. The same three-member vocabulary names both
 * what this rule pre-empts and what the commit's refusal says, so the sentence table has one
 * key and no reason arrives without words.
 *
 * ## Counted the way the server counts
 *
 * Python's `len` counts code points; a JavaScript string's `.length` counts UTF-16 units, on
 * which one emoji is two. A cap this side enforced in units would refuse a line of emoji the
 * server admits — a false refusal is a rewrite the player did not owe — so the count is in
 * code points, which is what `Array.from` yields.
 */

import type { AppError } from '@/shared/errors';

/**
 * The most characters an intro may hold, after trimming. The server's number, restated once —
 * 250 since ADR-0200 §9, which retired ADR-0170 §4's hundred with the deck card it fitted.
 */
export const INTRO_CAP = 250;

/**
 * The three reasons `intro_not_admitted` may carry, spelled as the wire spells them.
 *
 * Written down rather than read off the contract because a copy table is keyed by it and
 * transport does not reach `components/`. The error envelope's `details` is untyped on the
 * wire, so there is no generated union to hold this equal to — what holds it is the commit's
 * route-walked refusal tests, which send each one.
 */
export const INTRO_REFUSAL_REASONS = ['too_long', 'multiline', 'contains_contact'] as const;

export type IntroRefusalReason = (typeof INTRO_REFUSAL_REASONS)[number];

/** The reasons a client can read off the string itself, before anything is sent. */
export type IntroShapeRefusal = Exclude<IntroRefusalReason, 'contains_contact'>;

export type IntroStanding =
  /** Nothing written, or nothing but whitespace. The commit carries no line. */
  | { readonly kind: 'blank' }
  /** A line the shape rules admit. `line` is trimmed — what the server would keep. */
  | { readonly kind: 'written'; readonly line: string }
  /** A line the server would refuse on shape alone. The step does not let it past. */
  | { readonly kind: 'refused'; readonly reason: IntroShapeRefusal };

const CODE_INTRO_NOT_ADMITTED = 'intro_not_admitted';

/** Every line-break the server's `splitlines` would split on, near enough — see the note. */
const LINE_BREAK = /[\n\r\u2028\u2029]/;

/** The length the cap is read against — code points, as the server counts. */
export function introLength(line: string): number {
  return Array.from(line).length;
}

/**
 * Where a written line stands, read off the draft.
 *
 * **Trimmed first**, because the server trims first: a return pressed after the last word is
 * not a second line, and a line at the cap wrapped in a space is not over it. Where a
 * line breaks both rules, the length is named — it is the one that stays true after the other
 * is fixed.
 */
export function introStanding(written: string): IntroStanding {
  const line = written.trim();
  if (line === '') return { kind: 'blank' };
  if (introLength(line) > INTRO_CAP) return { kind: 'refused', reason: 'too_long' };
  if (LINE_BREAK.test(line)) return { kind: 'refused', reason: 'multiline' };
  return { kind: 'written', line };
}

/**
 * The line the commit carries, or nothing.
 *
 * **Nothing and never the empty string.** The wire reads a blank and an absence as the same
 * answer, and the app sends the one that cannot be read as a line.
 *
 * **A line the step would have refused is sent as it stands.** The step shuts *Next* on it,
 * so no walk produces one — and if a draft holds one anyway, the server's refusal names the
 * reason and the screen offers the way back. Dropping it here would commit a profile without
 * a line the player never agreed to lose.
 */
export function introToSend(written: string): string | undefined {
  const line = written.trim();
  return line === '' ? undefined : line;
}

/**
 * The intro's refusal, read off a failed commit — or `undefined` where the failure is not
 * the intro's at all.
 *
 * Read off the **code** and then off `details.reason`, never off the message. The two are
 * answered together because they are two different absences: no code, or another code, is
 * *not this refusal*; the code with a `reason` this build has no words for — a fourth one
 * added on the server — is *this refusal, unreadable*, answered with the code recognised and
 * the reason `undefined`, so the screen still sends the player back to the intro and says
 * the gap.
 */
export interface IntroRefusal {
  readonly reason: IntroRefusalReason | undefined;
}

export function introRefusal(error: AppError): IntroRefusal | undefined {
  if (error.code !== CODE_INTRO_NOT_ADMITTED) return undefined;
  const reason = error.details?.reason;
  return { reason: INTRO_REFUSAL_REASONS.find((known) => known === reason) };
}

/**
 * The intro's rules, with no renderer, no store and no wire.
 *
 * Two of the three refusals are shape and a client can see them coming; the third is the
 * backend's pattern and this side never guesses at it. What is pinned here is that the
 * line the commit carries is exactly the line the server would keep — trimmed, or nothing —
 * and that the reason a refusal names is read off the code and never off the message.
 */

import { AppError, networkUnavailable } from '@/shared/errors';

import {
  INTRO_CAP,
  INTRO_REFUSAL_REASONS,
  introLength,
  introRefusal,
  introStanding,
  introToSend,
} from './intro';

/** A refusal off the wire, as `mapErrorResponse` would have built it. */
function refusal(code: string, details?: Record<string, unknown>): AppError {
  return new AppError('validation', 'requires-user-correction', 'diagnostic', {
    code,
    status: 400,
    ...(details === undefined ? {} : { details }),
  });
}

describe('what a written line stands as', () => {
  it('is blank when nothing was typed, and when only whitespace was', () => {
    // A player who skips sends nothing and has no intro rather than an empty one; a player
    // who typed a space and thought better of it is the same player.
    expect(introStanding('')).toEqual({ kind: 'blank' });
    expect(introStanding('   \t ')).toEqual({ kind: 'blank' });
  });

  it('is written, trimmed, when there is a line', () => {
    expect(introStanding('  Moved from Wrocław in May. Needs opponents.  ')).toEqual({
      kind: 'written',
      line: 'Moved from Wrocław in May. Needs opponents.',
    });
  });

  it('admits exactly the cap and refuses one over it, counting after trimming', () => {
    const atTheCap = 'a'.repeat(INTRO_CAP);

    expect(introStanding(atTheCap)).toEqual({ kind: 'written', line: atTheCap });
    // The spaces around it are not part of the line — the server trims before it counts,
    // and a client that refused a hundred characters wrapped in a space would be stricter
    // than the rule it is pre-empting.
    expect(introStanding(`  ${atTheCap}  `)).toEqual({ kind: 'written', line: atTheCap });
    expect(introStanding(`${atTheCap}b`)).toEqual({ kind: 'refused', reason: 'too_long' });
  });

  it('counts characters the way the server does, so an emoji is one and not two', () => {
    // Python's `len` counts code points; a JavaScript string's `.length` counts UTF-16
    // units, on which one emoji is two. A line of a hundred emoji is at the cap, not over it.
    const emoji = '🎾'.repeat(INTRO_CAP);

    expect(introLength(emoji)).toBe(INTRO_CAP);
    expect(introStanding(emoji).kind).toBe('written');
  });

  it('refuses a line break wherever it falls', () => {
    expect(introStanding('Two games in.\nStill learning the city.')).toEqual({
      kind: 'refused',
      reason: 'multiline',
    });
    expect(introStanding('Will travel\r\nfor a hard game.')).toEqual({
      kind: 'refused',
      reason: 'multiline',
    });
  });

  it('does not refuse a line break that trimming removes', () => {
    // A return pressed after the last word is not a second line.
    expect(introStanding('Will travel for a hard game.\n')).toEqual({
      kind: 'written',
      line: 'Will travel for a hard game.',
    });
  });

  it('names the length ahead of the line break where a line breaks both', () => {
    // Either sentence would be true; the one that stays true after the other is fixed is
    // the length, so it is the one said first.
    expect(introStanding(`${'a'.repeat(INTRO_CAP + 1)}\nb`)).toEqual({
      kind: 'refused',
      reason: 'too_long',
    });
  });
});

describe('what the commit carries', () => {
  it('is the trimmed line where one was written', () => {
    expect(introToSend('  Will travel for a hard game. ')).toBe('Will travel for a hard game.');
  });

  it('is nothing where the line is blank', () => {
    // Nothing, and never the empty string: the wire says a blank and an absence are the
    // same answer, and the app sends the one that cannot be mistaken for a line.
    expect(introToSend('')).toBeUndefined();
    expect(introToSend('   ')).toBeUndefined();
  });

  it('carries a line the step would have refused, because the server is the authority', () => {
    // The step shuts *Next* on it, so a player cannot walk past one — and if a draft holds
    // one anyway, sending it gets the same refusal the step would have pre-empted, with the
    // way back. Silently dropping it would commit a profile with a line the player never
    // agreed to lose.
    const long = 'a'.repeat(INTRO_CAP + 1);

    expect(introToSend(long)).toBe(long);
  });
});

describe('the refusal a failed commit carries', () => {
  it('reads each of the three reasons off `intro_not_admitted`', () => {
    for (const reason of INTRO_REFUSAL_REASONS) {
      expect(introRefusal(refusal('intro_not_admitted', { reason }))).toEqual({ reason });
    }
  });

  it('is still the intro’s, with no reason, for a reason this build has no words for', () => {
    // A fourth reason added on the server arrives here as a code the app knows with a
    // detail it does not. Two absences, told apart: the refusal is the intro's, and what it
    // says is the gap's.
    expect(introRefusal(refusal('intro_not_admitted', { reason: 'profanity' }))).toEqual({
      reason: undefined,
    });
    expect(introRefusal(refusal('intro_not_admitted'))).toEqual({ reason: undefined });
  });

  it('is nothing for a code that is not the intro’s, whatever its details say', () => {
    expect(introRefusal(refusal('weekly_hours_empty', { reason: 'too_long' }))).toBeUndefined();
    expect(introRefusal(networkUnavailable())).toBeUndefined();
  });
});

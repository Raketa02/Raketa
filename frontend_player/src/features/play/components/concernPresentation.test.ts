/**
 * The concerns — the one table in the deck that is allowed to grade, because the judgement
 * arrived from the engine ranked.
 *
 * What is asserted is that the two directions of an intent mismatch are two sentences, that
 * the tag concerns quote the pair that clashed, and that a concern with no pair behind it is
 * dropped rather than generalised into a claim the client is making.
 */

import type { Evidence } from '../domain/evidence';

import { concernLine } from './concernPresentation';

const INTENT = (myMode: 'COMPETITIVE' | 'FOR_FUN'): Evidence => ({
  kind: 'intent_alignment',
  myMode,
  theirIntent: myMode === 'COMPETITIVE' ? 'FOR_FUN' : 'COMPETITIVE',
  aligned: false,
});

describe('a concern about the kind of evening', () => {
  it('is two sentences, because both directions fire and are priced differently', () => {
    // #230: one wording would state one player's mismatch as the other's.
    expect(concernLine(INTENT('COMPETITIVE'))).toBe("They're here for a fun game, and you're not");
    expect(concernLine(INTENT('FOR_FUN'))).toBe("They're here to compete, and you're not");
  });
});

describe('a concern about the tags', () => {
  it('names the pair that clashed, and where the two of them meet', () => {
    expect(
      concernLine({
        kind: 'playing_style',
        matched: [],
        matchedInFull: true,
        complementary: [],
        clashing: [{ a: 'PLAYS_TO_WIN', b: 'LAUGHS_OFF_MISTAKES' }],
      }),
    ).toBe('Plays to win against Laughs off mistakes on court');

    expect(
      concernLine({
        kind: 'social_vibe',
        matched: [],
        matchedInFull: true,
        complementary: [],
        clashing: [{ a: 'STAYS_FOR_A_DRINK', b: 'STRAIGHT_HOME_AFTER' }],
      }),
    ).toBe('Stays for a drink against Straight home after around the game');
  });

  it('is dropped when there is no pair to quote', () => {
    // A term can be a concern with nothing clashing — its measured zero. "You clash around
    // the game" with no pair behind it would be the client making the graded claim §7
    // reserves for the engine.
    expect(
      concernLine({
        kind: 'social_vibe',
        matched: [],
        matchedInFull: true,
        complementary: [],
        clashing: [],
      }),
    ).toBeUndefined();
  });
});

describe('the six that quote nothing', () => {
  it('states the harm and names nobody as at fault', () => {
    expect(
      concernLine({ kind: 'level_fit', myMu: 2.7, theirMu: 4.1, delta: 1.4, direction: 'ABOVE' }),
    ).toBe('A wide level gap — the game may be one-sided');
    expect(
      concernLine({
        kind: 'predicted_balance',
        pct: 41,
        mySigma: 0.6,
        theirSigma: 0.4,
        confidence: 38,
      }),
    ).toBe('Forecast to be uneven');
    expect(concernLine({ kind: 'reliability', score: 42, floorBreached: true })).toBe(
      'Their record is thin on turning up',
    );
    expect(concernLine({ kind: 'availability_overlap', sharedCount: 1, nextSlot: null })).toBe(
      'Almost none of your week is theirs',
    );
    expect(
      concernLine({
        kind: 'distance',
        km: 44,
        areaCode: 'A+050612+0019938',
        outsideTheirRadius: true,
      }),
    ).toBe('A long way out');
  });

  it('says nothing about when a record was last written', () => {
    // ADR-0106 §5's recency refusal reaches the concern as well as the degraded line.
    const line = concernLine({ kind: 'reliability', score: 42, floorBreached: true }) ?? '';

    expect(line).not.toMatch(/recent|lately|last seen|month|week/i);
  });
});

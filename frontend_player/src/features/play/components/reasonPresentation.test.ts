/**
 * The reason lines, without a renderer.
 *
 * Copy changes; the **register** does not, and that is most of what these hold. A line states
 * its evidence's own facts and never grades them, so the assertions that matter are the ones
 * that would catch a grading word creeping in, a mismatch being reported as a reason, and a
 * client thresholding a value it was handed.
 */

import type {
  AvailabilityOverlapEvidence,
  IntentAlignmentEvidence,
  PlayingStyleEvidence,
  SocialVibeEvidence,
} from '../domain/evidence';

import {
  availabilityOverlapReason,
  distanceReason,
  intentAlignmentReason,
  levelFitReason,
  playingStyleReason,
  predictedBalanceReason,
  reasonLine,
  reliabilityReason,
  socialVibeReason,
} from './reasonPresentation';

const OVERLAP = (over: Partial<AvailabilityOverlapEvidence>): AvailabilityOverlapEvidence => ({
  kind: 'availability_overlap',
  sharedCount: 3,
  nextSlot: { day: 2, part: 'evening' },
  ...over,
});

const TAGS = (over: Partial<PlayingStyleEvidence>): PlayingStyleEvidence => ({
  kind: 'playing_style',
  matched: [],
  matchedInFull: true,
  complementary: [],
  clashing: [],
  ...over,
});

const VIBE = (over: Partial<SocialVibeEvidence>): SocialVibeEvidence => ({
  kind: 'social_vibe',
  matched: [],
  matchedInFull: true,
  complementary: [],
  clashing: [],
  ...over,
});

const INTENT = (over: Partial<IntentAlignmentEvidence>): IntentAlignmentEvidence => ({
  kind: 'intent_alignment',
  myMode: 'COMPETITIVE',
  theirIntent: 'COMPETITIVE',
  aligned: true,
  ...over,
});

describe('a level gap', () => {
  it('states the gap and which way, in the level format', () => {
    // Two decimals and a decimal comma, §B16 — the same shape the level row prints.
    expect(
      levelFitReason({
        kind: 'level_fit',
        myMu: 2.71,
        theirMu: 3.02,
        delta: 0.31,
        direction: 'ABOVE',
      }),
    ).toBe('0,31 above you');
    expect(
      levelFitReason({
        kind: 'level_fit',
        myMu: 2.71,
        theirMu: 2.4,
        delta: 0.31,
        direction: 'BELOW',
      }),
    ).toBe('0,31 below you');
  });

  it('says level with you rather than a gap of zero', () => {
    expect(
      levelFitReason({
        kind: 'level_fit',
        myMu: 2.71,
        theirMu: 2.71,
        delta: 0,
        direction: 'LEVEL',
      }),
    ).toBe('Level with you');
  });
});

describe('the forecast', () => {
  it('states the platform’s caveat in the same breath as the claim', () => {
    // §F1 rule 4's fact · mechanism, and the only place `confidence` is drawn at all.
    expect(
      predictedBalanceReason({
        kind: 'predicted_balance',
        pct: 82,
        mySigma: 0.62,
        theirSigma: 0.4,
        confidence: 41,
      }),
    ).toBe('Forecast 82% even · 41% sure');
  });

  it('never prints either sigma', () => {
    const line = predictedBalanceReason({
      kind: 'predicted_balance',
      pct: 82,
      mySigma: 0.62,
      theirSigma: 0.4,
      confidence: 41,
    });

    // The candidate's σ reaches a screen exactly once, as the likely range on the card.
    expect(line).not.toMatch(/0,62|0,40/);
  });
});

describe('the kind of evening', () => {
  it('says so when both are after the same one', () => {
    expect(intentAlignmentReason(INTENT({}))).toBe("They're here to compete too");
    expect(intentAlignmentReason(INTENT({ myMode: 'FOR_FUN', theirIntent: 'FOR_FUN' }))).toBe(
      "They're here for a fun game too",
    );
  });

  it('reads a candidate who has not chosen as either kind, in both modes', () => {
    for (const myMode of ['COMPETITIVE', 'FOR_FUN'] as const) {
      expect(intentAlignmentReason(INTENT({ myMode, theirIntent: 'NO_PREFERENCE' }))).toBe(
        "They'll play either kind of evening",
      );
    }
  });

  it('is not a reason at all when the two disagree, in either direction', () => {
    // #230 priced both directions and both fire, so the fact reaches the player as a concern
    // — one sentence per direction, because a single wording would state one player's
    // mismatch as the other's.
    expect(
      intentAlignmentReason(
        INTENT({ myMode: 'COMPETITIVE', theirIntent: 'FOR_FUN', aligned: false }),
      ),
    ).toBeUndefined();
    expect(
      intentAlignmentReason(
        INTENT({ myMode: 'FOR_FUN', theirIntent: 'COMPETITIVE', aligned: false }),
      ),
    ).toBeUndefined();
  });

  it('reads the mode off the evidence, never off a search envelope', () => {
    // The deck's envelope carries no mode and its candidates carry one, and they correctly
    // disagree — a renderer taking the envelope would say nothing on the deck.
    expect(intentAlignmentReason(INTENT({ myMode: 'FOR_FUN', theirIntent: 'FOR_FUN' }))).toBe(
      "They're here for a fun game too",
    );
  });
});

describe('their record', () => {
  it('prints the published score and never the breach beside it', () => {
    // The breach is `RELIABILITY_FLOOR_BREACH`'s sentence; printed twice, one dock reads as
    // two.
    expect(reliabilityReason({ kind: 'reliability', score: 74, floorBreached: true })).toBe(
      'Player Score 74',
    );
  });
});

describe('when you both play', () => {
  it('counts the shared cells and names the next one', () => {
    expect(availabilityOverlapReason(OVERLAP({}))).toBe(
      '3 slots you both ticked · next Tue evening',
    );
  });

  it('stops at the count when there is no next cell', () => {
    expect(availabilityOverlapReason(OVERLAP({ nextSlot: null }))).toBe('3 slots you both ticked');
  });

  it('hardcodes no plural', () => {
    // §J4's gap is the map's fog; what this file owes is that no sentence assumes one.
    expect(availabilityOverlapReason(OVERLAP({ sharedCount: 1, nextSlot: null }))).toBe(
      '1 slot you both ticked',
    );
  });

  it('says a zero would have to be bent around, and blames nobody', () => {
    const line = availabilityOverlapReason(OVERLAP({ sharedCount: 0, nextSlot: null }));

    expect(line).toBe('No shared slots — one of you would have to bend');
    expect(line).not.toMatch(/unavailable|never free/i);
  });
});

describe('the two tag terms', () => {
  it('leads with what they both hold, in the promoted words', () => {
    expect(playingStyleReason(TAGS({ matched: ['PLAYS_TO_WIN', 'QUIET_AND_FOCUSED'] }))).toBe(
      'Both of you: Plays to win, Quiet and focused',
    );
  });

  it('never carries the chip’s emoji into a sentence', () => {
    const line = playingStyleReason(TAGS({ matched: ['PLAYS_TO_WIN'] })) ?? '';

    expect(line).toBe('Both of you: Plays to win');
    expect(line).not.toMatch(/🏆/);
  });

  it('falls to the complementary pair when nothing is shared', () => {
    expect(
      socialVibeReason(VIBE({ complementary: [{ a: 'STAYS_FOR_A_DRINK', b: 'SHARES_A_LIFT' }] })),
    ).toBe('Stays for a drink meets Shares a lift');
  });

  it('is not a reason when only clashes fired', () => {
    // A clash is a graded claim, and the engine is the only thing entitled to make it.
    expect(
      playingStyleReason(TAGS({ clashing: [{ a: 'PLAYS_TO_WIN', b: 'LAUGHS_OFF_MISTAKES' }] })),
    ).toBeUndefined();
  });

  it('states the measured zero as different rather than as absent, per term', () => {
    // The term's zero is a real clash, never an absence of relationship — and it is not the
    // same state as the term standing down.
    expect(playingStyleReason(TAGS({}))).toBe('Different on court, not incompatible');
    expect(socialVibeReason(VIBE({}))).toBe('Different around the game, not incompatible');
  });
});

describe('how far', () => {
  it('states the distance', () => {
    expect(
      distanceReason({
        kind: 'distance',
        km: 7,
        areaCode: 'A+050612+0019938',
        outsideTheirRadius: false,
      }),
    ).toBe('7 km away');
  });

  it('says when the searcher is outside the ring they set, rather than removing them', () => {
    expect(
      distanceReason({
        kind: 'distance',
        km: 24,
        areaCode: 'A+050612+0019938',
        outsideTheirRadius: true,
      }),
    ).toBe('24 km away — outside the ring they set');
  });

  it('never prints the area code', () => {
    const line = distanceReason({
      kind: 'distance',
      km: 7,
      areaCode: 'A+050612+0019938',
      outsideTheirRadius: false,
    });

    expect(line).not.toMatch(/A\+/);
  });
});

describe('the register, across every line this build can write', () => {
  it('grades nothing', () => {
    // §4: no *well*, no *strongly*, no *good*. The grading vocabulary is `concerns[]`', which
    // is the engine's judgement and arrives ranked.
    const everyLine = [
      levelFitReason({ kind: 'level_fit', myMu: 2.7, theirMu: 3, delta: 0.31, direction: 'ABOVE' }),
      levelFitReason({ kind: 'level_fit', myMu: 2.7, theirMu: 2.7, delta: 0, direction: 'LEVEL' }),
      predictedBalanceReason({
        kind: 'predicted_balance',
        pct: 82,
        mySigma: 0.6,
        theirSigma: 0.4,
        confidence: 41,
      }),
      intentAlignmentReason(INTENT({})),
      intentAlignmentReason(INTENT({ theirIntent: 'NO_PREFERENCE' })),
      reliabilityReason({ kind: 'reliability', score: 74, floorBreached: false }),
      availabilityOverlapReason(OVERLAP({})),
      availabilityOverlapReason(OVERLAP({ sharedCount: 0, nextSlot: null })),
      playingStyleReason(TAGS({ matched: ['PLAYS_TO_WIN'] })),
      playingStyleReason(TAGS({})),
      socialVibeReason(VIBE({})),
      distanceReason({ kind: 'distance', km: 7, areaCode: 'A', outsideTheirRadius: false }),
    ];

    for (const line of everyLine) {
      expect(line).toBeDefined();
      expect(line).not.toMatch(
        /\b(good|great|excellent|poor|bad|strong(ly)?|well|perfect|ideal)\b/i,
      );
    }
  });
});

describe('the one entry point', () => {
  it('dispatches on kind, so a surface never branches on a term', () => {
    expect(reasonLine(OVERLAP({ sharedCount: 2, nextSlot: null }))).toBe('2 slots you both ticked');
    expect(reasonLine({ kind: 'distance', km: 3, areaCode: 'A', outsideTheirRadius: false })).toBe(
      '3 km away',
    );
  });

  it('says nothing for the evidence that is not a reason', () => {
    expect(reasonLine(INTENT({ theirIntent: 'FOR_FUN', aligned: false }))).toBeUndefined();
  });
});

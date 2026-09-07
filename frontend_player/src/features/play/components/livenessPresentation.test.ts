/**
 * Why this person moved, and why they are on the list at all.
 *
 * The assertion that matters is the un-datable wording: `RECENT_ACTIVITY` is the sanctioned
 * crossing and *"active today"* is the refused one, so the line says *around this week* and
 * never a timestamp, a day or a green dot.
 */

import { LIVENESS_REASONS } from '../domain/vocabulary';

import { WHAT_ELSE_MOVED_YOU_HERE, inclusionLine, livenessLine } from './livenessPresentation';

describe('the ten codes', () => {
  it('gives each its own words', () => {
    const lines = LIVENESS_REASONS.map(livenessLine);

    expect(lines.every((line) => line.length > 0)).toBe(true);
    expect(new Set(lines).size).toBe(LIVENESS_REASONS.length);
  });

  it('dates nobody, anywhere in the vocabulary', () => {
    // ADR-0106 §5. *Around this week* is a reason code's reading; *active today* is a fact
    // about a person the platform withholds.
    for (const line of LIVENESS_REASONS.map(livenessLine)) {
      expect(line).not.toMatch(/today|yesterday|hour|minute|online|\d/i);
    }
  });

  it('reads the three challenge loads as facts about their inbox, not about them', () => {
    expect(livenessLine('CHALLENGE_LOAD_SOME')).toBe('A few challenges waiting on them');
    expect(livenessLine('CHALLENGE_LOAD_FULL')).toBe('A full inbox — they may be slow to answer');
  });
});

describe('why they are in the list at all', () => {
  it('says the one thing that admits somebody', () => {
    // A union of one, and it *admits* — the two reasons that merely reorder stay in the store.
    expect(inclusionLine('INTEREST_LIFT')).toBe('They already said yes to you');
  });

  it('heads the sheet’s zone without claiming the codes moved the Fit', () => {
    // Liveness moves the order, not the number, and the heading has to survive that.
    expect(WHAT_ELSE_MOVED_YOU_HERE).toBe('What else moved you here');
  });
});

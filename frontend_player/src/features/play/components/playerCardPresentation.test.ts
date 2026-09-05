/**
 * The two lines a card prints about the player it draws.
 *
 * The level row's assertion is the **word**: `likely` names the μ ± σ range, and the band
 * keeps its own name, because a card that called the range a band would name a band that
 * disagrees with the number beside it.
 *
 * The meta line — the one sentence a card is licensed to write from an `area_code`.
 *
 * The assertions are the two refusals: **the code is never printed**, because it is a
 * coordinate string and `areas.py` refuses in writing to make it a name; and **nothing is
 * said about activity**, which is the slot #218 refused.
 *
 * The **Social tag row**'s words join them, and the assertion there is the split between the
 * two registers: the chip carries a glyph and a per-tag marker, the spoken clause carries
 * neither and groups instead ([#311](https://github.com/Raketa02/Raketa/issues/311)).
 */

import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import {
  CANDIDATE_ACTION_WORD,
  candidateTag,
  levelRow,
  metaLine,
  socialTagChip,
  socialTagClauses,
} from './playerCardPresentation';

import { livenessLine } from './livenessPresentation';

const HERE = 'A+050612+0019938';
const ELSEWHERE = 'A+050614+0019902';

describe('the level row', () => {
  it('states the level, the band and the likely range, in that order', () => {
    expect(levelRow({ level: 2.71, band: 'Established', range: { low: 2.55, high: 2.87 } })).toBe(
      '2,71 · Established · likely 2,55 – 2,87',
    );
  });

  it('never calls the range a band', () => {
    // The four bands are New · Developing · Established · Advanced; `2,55–2,87` is μ ± σ, and
    // the prototype spent the domain's word on it.
    const row = levelRow({ level: 2.71, band: 'Established', range: { low: 2.55, high: 2.87 } });

    expect(row).not.toMatch(/band/i);
    expect(row).toMatch(/likely/);
  });

  it('draws the band’s published name and never its edges', () => {
    // The band's numeric edges are not on the card: the only thing that would draw them is the
    // band bar, which is drawn from the player record sheet.
    expect(levelRow({ level: 4.02, band: 'Advanced', range: { low: 3.8, high: 4.24 } })).toBe(
      '4,02 · Advanced · likely 3,80 – 4,24',
    );
  });
});

describe('the meta line', () => {
  it('is the distance alone when the two areas differ', () => {
    expect(metaLine({ km: 7, theirAreaCode: ELSEWHERE, myAreaCode: HERE })).toBe('7 km');
  });

  it('says they are in your area when the two codes match', () => {
    // A comparison between two codes is exactly what ADR-0021 licenses a client to compute.
    expect(metaLine({ km: 2, theirAreaCode: HERE, myAreaCode: HERE })).toBe('In your area · 2 km');
  });

  it('never prints the code itself, in either branch', () => {
    const lines = [
      metaLine({ km: 7, theirAreaCode: ELSEWHERE, myAreaCode: HERE }),
      metaLine({ km: 2, theirAreaCode: HERE, myAreaCode: HERE }),
    ];

    for (const line of lines) expect(line).not.toMatch(/A\+\d/);
  });

  it('says nothing about when they were last here', () => {
    // `active {x}` is the other slot with nothing behind it, and it is the one ADR-0106 §5
    // withholds rather than the one nobody has built.
    const line = metaLine({ km: 7, theirAreaCode: ELSEWHERE, myAreaCode: HERE });

    expect(line).not.toMatch(/active|today|online|ago/i);
  });
});

describe('the tag beside the handle', () => {
  it('says nothing at all where neither fact is true', () => {
    // The row is the identity row and not a tag rail: most people on a list are neither the
    // best match nor somebody who already said yes, and a tag drawn for them would be a word
    // that means *nothing in particular*.
    expect(candidateTag({ bestMatch: false })).toBeUndefined();
  });

  it('marks the best match in coral', () => {
    expect(candidateTag({ bestMatch: true })).toEqual({ label: 'Best match', variant: 'hot' });
  });

  it('says the interest lift in volt, and it replaces best match where both apply', () => {
    // *"because it's the stronger fact"* — the coral one is about where somebody sits in a
    // list this player is reading, and the volt one is about a decision somebody else made.
    expect(candidateTag({ inclusionReason: 'INTEREST_LIFT', bestMatch: false })).toEqual({
      label: 'Wants to play you',
      variant: 'volt',
    });
    expect(candidateTag({ inclusionReason: 'INTEREST_LIFT', bestMatch: true })).toEqual({
      label: 'Wants to play you',
      variant: 'volt',
    });
  });

  it('takes the admitting code’s words from its liveness twin, which is one tag and not two', () => {
    // §10: `INTEREST_LIFT` and `INTEREST_RECEIVED` fire for the same person and are two facts
    // with ONE tag. The tag is bound to the admitting code; the words are the twin's, and the
    // twin's own sentence can only reach a card as the reason fallback, which the competitive
    // card never takes.
    expect(candidateTag({ inclusionReason: 'INTEREST_LIFT', bestMatch: false })?.label).toBe(
      livenessLine('INTEREST_RECEIVED'),
    );
  });
});

describe('what a card’s primary button says', () => {
  it('names where the add goes, which is the one wording of the three that is always true', () => {
    // *Add to the four* is wrong on a squash court, and *Add — this is the match* is a claim
    // the card is not making. The destination is true at every seat count and in both modes.
    expect(CANDIDATE_ACTION_WORD.ADD_TO_COURT).toBe('Add to the court');
    expect(CANDIDATE_ACTION_WORD.CHALLENGE).toBe('Challenge');
  });
});

describe('the social tag row’s words', () => {
  const shared = (id: SocialTagId) => ({ id, shared: true });
  const theirs = (id: SocialTagId) => ({ id, shared: false });

  it('draws the tag with its glyph, and the marker only where it is shared', () => {
    expect(socialTagChip(shared('PLAYS_TO_WIN'))).toBe('🏆 Plays to win · you too');
    expect(socialTagChip(theirs('PLAYS_TO_WIN'))).toBe('🏆 Plays to win');
  });

  it('speaks the shared ones under one clause rather than marking each of them', () => {
    // A listener hearing *you too* six times is being read a table, not a card.
    expect(
      socialTagClauses({
        kind: 'shared',
        tags: [shared('PLAYS_TO_WIN'), theirs('STAYS_FOR_A_DRINK'), shared('QUIET_AND_FOCUSED')],
      }),
    ).toEqual([
      'Tags you share: Plays to win, Quiet and focused',
      'Their other tags: Stays for a drink',
    ]);
  });

  it('omits a clause with nobody in it rather than emptying it', () => {
    expect(socialTagClauses({ kind: 'shared', tags: [shared('PLAYS_TO_WIN')] })).toEqual([
      'Tags you share: Plays to win',
    ]);
    // The narrowed-match case: something matched, and none of it survived into their tags.
    expect(socialTagClauses({ kind: 'shared', tags: [theirs('PLAYS_TO_WIN')] })).toEqual([
      'Their other tags: Plays to win',
    ]);
  });

  it('says whose fact it is when nothing compared them', () => {
    expect(
      socialTagClauses({ kind: 'unknown', tags: ['PLAYS_TO_WIN', 'WARMS_UP_PROPERLY'] }),
    ).toEqual(['Their tags: Plays to win, Warms up properly']);
  });

  it('carries the one claim the row makes, and nothing at all where there is none', () => {
    expect(socialTagClauses({ kind: 'none-in-common' })).toEqual(['No tags in common']);
    expect(socialTagClauses({ kind: 'hidden' })).toEqual([]);
  });

  /** Prose does not carry glyphs — `socialTagPresentation`'s own split, read from this side. */
  it('speaks the words alone, where the chip is drawn with its emoji', () => {
    expect(socialTagClauses({ kind: 'unknown', tags: ['PLAYS_TO_WIN'] })[0]).not.toContain('🏆');
  });
});

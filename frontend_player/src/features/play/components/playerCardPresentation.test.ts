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
 * The **Social tag row**'s spoken clauses join them, and the assertion there is one half of a
 * split: the clause carries neither the glyph nor the per-tag marker and groups the shared
 * ones instead ([#311](https://github.com/Raketa02/Raketa/issues/311)). The other half — what
 * the chip is *drawn* with — moved to `shared/vocabulary/socialTagPresentation.test.ts` with
 * the row itself, and is asserted there against the same two registers.
 */

import { levelRow } from '@/shared/formatting/levelRow';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import {
  CANDIDATE_ACTION_WORD,
  candidateTag,
  countedGamesReading,
  lastFiveReading,
  metaLine,
  recordClauses,
  socialTagClauses,
  stakeClauses,
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
    expect(metaLine({ km: 7.2, theirAreaCode: ELSEWHERE, myAreaCode: HERE })).toBe('7,2 km');
  });

  it('says they are in your area when the two codes match', () => {
    // A comparison between two codes is exactly what ADR-0021 licenses a client to compute.
    expect(metaLine({ km: 1.9, theirAreaCode: HERE, myAreaCode: HERE })).toBe(
      'In your area · 1,9 km',
    );
  });

  /**
   * **One decimal, everywhere** (ADR-0174 §2). The distance is the spot-to-spot number the server
   * serves to one place, and the card prints it through the one formatter — so somebody in the
   * reader's own cell reads *In your area · 0,6 km* rather than a whole kilometre, and a served
   * whole number still carries its decimal.
   */
  it('prints the distance to one decimal, never a whole kilometre', () => {
    expect(metaLine({ km: 0.6, theirAreaCode: HERE, myAreaCode: HERE })).toBe(
      'In your area · 0,6 km',
    );
    expect(metaLine({ km: 4, theirAreaCode: ELSEWHERE, myAreaCode: HERE })).toBe('4,0 km');
  });

  it('never prints the code itself, in either branch', () => {
    const lines = [
      metaLine({ km: 7.2, theirAreaCode: ELSEWHERE, myAreaCode: HERE }),
      metaLine({ km: 1.9, theirAreaCode: HERE, myAreaCode: HERE }),
    ];

    for (const line of lines) expect(line).not.toMatch(/A\+\d/);
  });

  it('says nothing about when they were last here', () => {
    // `active {x}` is the other slot with nothing behind it, and it is the one ADR-0106 §5
    // withholds rather than the one nobody has built.
    const line = metaLine({ km: 7.2, theirAreaCode: ELSEWHERE, myAreaCode: HERE });

    expect(line).not.toMatch(/active|today|online|ago/i);
  });
});

describe('the tag beside the handle', () => {
  it('says nothing at all where none of the three facts is true', () => {
    // The row is the identity row and not a tag rail: most people on a list are neither the
    // best match nor anybody a yes has passed between, and a tag drawn for them would be a
    // word that means *nothing in particular*.
    expect(candidateTag({ saidYes: false, bestMatch: false })).toBeUndefined();
  });

  it('marks the best match in coral', () => {
    expect(candidateTag({ saidYes: false, bestMatch: true })).toEqual({
      kind: 'best-match',
      label: 'Best match',
      variant: 'hot',
    });
  });

  it('says the interest lift in volt, and it replaces best match where both apply', () => {
    // *"because it's the stronger fact"* — the coral one is about where somebody sits in a
    // list this player is reading, and the volt one is about a decision somebody else made.
    const wants = { kind: 'wants-to-play-you', label: 'Wants to play you', variant: 'volt' };

    expect(
      candidateTag({ inclusionReason: 'INTEREST_LIFT', saidYes: false, bestMatch: false }),
    ).toEqual(wants);
    expect(
      candidateTag({ inclusionReason: 'INTEREST_LIFT', saidYes: false, bestMatch: true }),
    ).toEqual(wants);
  });

  /**
   * ADR-0169 §8: an outgoing yes is a tag only — the reader's own act, off their own list, and
   * a fact about a person rather than about a list, so it outranks the coral tag as the volt
   * one does. It is **not** volt: volt is *they want you*, and a border travels with that word
   * alone.
   */
  it('says the reader’s own yes as a plain tag, over best match and never over the lift', () => {
    const said = { kind: 'you-said-yes', label: 'You said yes', variant: 'base' };

    expect(candidateTag({ saidYes: true, bestMatch: false })).toEqual(said);
    expect(candidateTag({ saidYes: true, bestMatch: true })).toEqual(said);
    // Both true is a mutual, and a mutual is not on the list; should one ever be, *Wants to
    // play you* wins.
    expect(
      candidateTag({ inclusionReason: 'INTEREST_LIFT', saidYes: true, bestMatch: false })?.kind,
    ).toBe('wants-to-play-you');
  });

  it('takes the admitting code’s words from its liveness twin, which is one tag and not two', () => {
    // §10: `INTEREST_LIFT` and `INTEREST_RECEIVED` fire for the same person and are two facts
    // with ONE tag. The tag is bound to the admitting code; the words are the twin's, and the
    // twin's own sentence can only reach a card as the reason fallback, which the competitive
    // card never takes.
    expect(
      candidateTag({ inclusionReason: 'INTEREST_LIFT', saidYes: false, bestMatch: false })?.label,
    ).toBe(livenessLine('INTEREST_RECEIVED'));
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

/**
 * **The three record blocks' words**, and the two readings a drawing cannot carry.
 *
 * What is asserted here is what a *listener* gets: the squares are fill and the count has no
 * unit on it, so both need a sentence, and the Player Score needs the scale beside it because
 * it is the second out-of-a-hundred figure on the card
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 */
describe('the record block’s words', () => {
  it('states what a Player Score is out of, because Fit is already the other hundred', () => {
    expect(recordClauses({ playerScore: 74 })).toEqual(['Player Score 74 out of 100']);
  });

  it('counts the run rather than reading it out square by square', () => {
    expect(lastFiveReading(['WIN', 'LOSS', 'WIN', 'WIN', 'LOSS'])).toBe('3 of the last 5 won');
  });

  it('counts it against its own length, so the words do not pad what the drawing will not', () => {
    // Fewer than five is a real answer and the gap is the honest statement — *of the last 5*
    // over three results would be the padding, one register over.
    expect(lastFiveReading(['WIN', 'WIN', 'LOSS'])).toBe('2 of the last 3 won');
    expect(lastFiveReading(['LOSS'])).toBe('0 of the last 1 won');
  });

  it('names what the count is a count of, through the one pluralisation helper', () => {
    expect(countedGamesReading(29)).toBe('29 counted games');
    expect(countedGamesReading(1)).toBe('1 counted game');
  });

  it('says one clause per block drawn, in the order the blocks are drawn', () => {
    expect(recordClauses({ playerScore: 74, lastFive: ['WIN', 'LOSS'], countedGames: 29 })).toEqual(
      ['Player Score 74 out of 100', '1 of the last 2 won', '29 counted games'],
    );
  });

  it('says nothing for a block that is hidden, which is every block for a new player', () => {
    expect(recordClauses({})).toEqual([]);
    expect(recordClauses({ countedGames: 3 })).toEqual(['3 counted games']);
  });
});

describe('the stake boxes’ words', () => {
  it('says both or neither, because one figure is half a symmetrical fact', () => {
    expect(stakeClauses({ winDelta: 0.08, lossDelta: -0.05 })).toEqual([
      'Win, counted +0,08',
      'Lose, counted \u22120,05',
    ]);
  });
});

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
  countedGamesReading,
  lastFiveReading,
  levelRow,
  metaLine,
  ON_COURT_CLAUSE,
  ON_COURT_MARK,
  recordClauses,
  socialTagChip,
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

describe('the ON COURT mark’s words', () => {
  it('carries no figure in either register', () => {
    // ADR-0133's clause survives ADR-0138 untouched — the confidence never crosses on any
    // route — so there is nothing here to print a number from and nothing here that prints
    // one. Asserted on the strings, because the card beside them draws a Fit and a forecast
    // and a *no percentages on the card* assertion would be about those instead.
    expect(ON_COURT_MARK).not.toMatch(/\d/);
    expect(ON_COURT_CLAUSE).not.toMatch(/\d/);
  });

  it('leads with the photograph when it is spoken, and not when it is drawn', () => {
    // Two words over somebody's picture are plainly about the picture; a clause in a run of
    // sentences is not, and *on court* between a Level and a forecast is one comma away from
    // activity recency — which no card carries at any granularity.
    expect(ON_COURT_MARK).toBe('On court');
    expect(ON_COURT_CLAUSE.startsWith('Photo')).toBe(true);
  });

  it('is sentence case, because the capitals are the panel’s treatment', () => {
    // The Sport beneath it is uppercased by the same style rather than by its own string.
    // A pre-shouted constant would be the one place in this deck where a style decision is
    // spelled into the copy.
    expect(ON_COURT_MARK).not.toBe(ON_COURT_MARK.toUpperCase());
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

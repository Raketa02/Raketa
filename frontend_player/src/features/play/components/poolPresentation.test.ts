/**
 * Everything the pool says that no other surface does — the ladder's sentences, and the
 * standing statement a taken rung leaves in the header.
 *
 * Three refusals are asserted, and each is a way the ladder could quietly stop being honest:
 * **the count is never a delta**, **the rung's letter is never printed**, and **a sentence
 * that would say *widen* is never addressed to somebody who cannot**.
 */

import {
  awaitingBalanceLine,
  poolLadderTitle,
  poolSeatedLine,
  seatedNamesLine,
  rungCount,
  takenRungLine,
  terminalReachLine,
  zeroRungLine,
} from './poolPresentation';

describe('what the list is worth', () => {
  it('counts the people who cleared the bar, and says where', () => {
    expect(poolLadderTitle({ rows: 4, radiusKmUsed: 12 })).toBe('4 people clear the bar at 12 km.');
    expect(poolLadderTitle({ rows: 1, radiusKmUsed: 12 })).toBe(
      '1 person clears the bar at 12 km.',
    );
  });

  it('says nobody rather than nought', () => {
    expect(poolLadderTitle({ rows: 0, radiusKmUsed: 15 })).toBe('Nobody clears the bar at 15 km.');
  });
});

describe('a priced rung', () => {
  const offer = {
    ask: 'RADIUS',
    candidatesAboveFloor: 9,
    window: 'THIS_WEEK',
    radiusKm: 22,
  } as const;

  /**
   * `candidates_above_floor` is *the total who would clear the floor at this rung*, never a
   * delta against the rows on screen: *"the trigger asks is this list short, in rows shown; a
   * rung asks would widening add anybody, in people above the floor — those are two
   * populations."* It is also the only reason rung A, whose set is not a superset, can be
   * priced honestly at all.
   */
  it('prints the total to choose from, and never a number more', () => {
    expect(rungCount(offer, 'THIS_WEEK')).toBe('9 to choose from');
    expect(rungCount(offer, 'THIS_WEEK')).not.toMatch(/\+|more|extra/);
  });

  /** A challenge sliding from the weekend to the week is part of what widening costs. */
  it('names the window when this rung would move it', () => {
    expect(rungCount(offer, 'WEEKEND')).toBe('9 to choose from · This week');
  });

  it('says nothing about a window it cannot read', () => {
    expect(rungCount({ ...offer, window: null }, 'WEEKEND')).toBe('9 to choose from');
  });
});

describe('a rung priced at nobody', () => {
  it('states the reach as a fact rather than offering it as an act', () => {
    expect(zeroRungLine({ ask: 'RADIUS', radiusKm: 32 })).toBe(
      'Even at 32 km, nobody clears the bar.',
    );
    expect(zeroRungLine({ ask: 'TIMES' })).toBe('Even outside your week, nobody clears the bar.');
  });
});

describe('the terminal sentence', () => {
  const reach = { radiusKmUsed: 15, playersInRange: 6 };

  it('states the ceiling as a fact where the slider hit it', () => {
    const said = terminalReachLine({ ...reach, radiusClamp: true, tookRadiusFrom: undefined });

    expect(said).toContain('15 km');
    expect(said).toContain('as wide as the app goes');
    // Never an instruction somebody at their own ceiling cannot carry out.
    expect(said).not.toMatch(/widen/i);
  });

  it('names the profile the widening did not touch, after a radius rung', () => {
    const said = terminalReachLine({
      radiusKmUsed: 30,
      playersInRange: 6,
      radiusClamp: false,
      tookRadiusFrom: 15,
    });

    expect(said).toContain('your profile still asks for 15 km');
  });

  it('otherwise says what moves the pool, which is other people', () => {
    const said = terminalReachLine({ ...reach, radiusClamp: false, tookRadiusFrom: undefined });

    expect(said).toContain('6 players are in range');
    expect(said).toContain('declare their weeks');
  });
});

describe('the standing statement a taken rung leaves', () => {
  it('names the widened radius and the profile that did not change', () => {
    expect(takenRungLine({ ask: 'RADIUS', radiusKm: 22, profileRadiusKm: 15 })).toBe(
      'Searching 22 km for this search. Your profile still asks for 15 km.',
    );
  });

  it('says the week moved without naming a cell nobody ticked', () => {
    expect(takenRungLine({ ask: 'TIMES', profileRadiusKm: 15 })).toBe(
      'Searching outside your week for this search. Your profile is unchanged.',
    );
  });

  /**
   * Letters rather than numbers precisely so nobody lines them up against a struck rung, and
   * printing either spelling would publish an engine-internal ordering.
   */
  it('never prints the rung', () => {
    const said = [
      takenRungLine({ ask: 'RADIUS', radiusKm: 22, profileRadiusKm: 15 }),
      takenRungLine({ ask: 'TIMES', profileRadiusKm: 15 }),
      zeroRungLine({ ask: 'RADIUS', radiusKm: 32 }),
    ];

    for (const line of said) expect(line).not.toMatch(/\brung\b|\b[ABC]\b/);
  });
});

/**
 * The header — **what the card at the top of *Pick players* says about the court being filled**
 * ([#297](https://github.com/Raketa02/Raketa/issues/297)).
 *
 * Two things are asserted that are easy to get wrong on the way past. The handles are printed
 * **whole**, which is the pool's half of `the-play-components.md` §5 — the 46pt seat label is
 * allowed to cut a 64-character handle to four characters *because* this line exists. And the
 * sentence promising a balance is written for the **shape of the court on screen**: a singles
 * court has no far side to fill, and squash draws both players on the same half of the picture.
 */
describe('the header', () => {
  it('counts the seats that are filled, through every state the card has', () => {
    // The four the header goes through as somebody fills a doubles court, and the two a
    // singles court has. *Seated* is a participle, so nothing here inflects with the count.
    expect(poolSeatedLine({ filled: 1, seats: 4 })).toBe('1 of 4 seated');
    expect(poolSeatedLine({ filled: 2, seats: 4 })).toBe('2 of 4 seated');
    expect(poolSeatedLine({ filled: 3, seats: 4 })).toBe('3 of 4 seated');
    expect(poolSeatedLine({ filled: 4, seats: 4 })).toBe('4 of 4 seated');
    expect(poolSeatedLine({ filled: 1, seats: 2 })).toBe('1 of 2 seated');
    expect(poolSeatedLine({ filled: 2, seats: 2 })).toBe('2 of 2 seated');
  });

  it('prints every handle whole, in seat order, and never cuts one', () => {
    const long = 'marekwiśniewski-plays-every-tuesday-and-most-saturdays-in-warsaw';

    expect(seatedNamesLine(['You', 'Karol', 'Magda', 'Ania'])).toBe('You · Karol · Magda · Ania');
    expect(seatedNamesLine(['You', long])).toContain(long);
  });

  it('passes the unknown through rather than tidying it away', () => {
    // The screen hands in whatever `playerName()` answered, and a withheld row answers `?` —
    // the same character the seat itself draws. What is asserted here is only that this line
    // does not drop or replace it; deriving it is the screen's, and is tested there.
    expect(seatedNamesLine(['You', '?'])).toBe('You · ?');
  });

  it('promises the balance against the half that is actually empty', () => {
    expect(awaitingBalanceLine(4)).toBe(
      'Add somebody to their side and a running balance appears here.',
    );
    expect(awaitingBalanceLine(2)).toBe('Add your opponent and a running balance appears here.');
  });

  /**
   * *Their side* rather than the prototype's *far side*, and the words are `SIDE`'s: this app
   * has one spelling of that half, and a second one written out here is how the two drift with
   * nothing to catch it. Both Sports this branch can reach do have a far side — only padel and
   * badminton have four seats — so the refusal is about the vocabulary, not the geometry.
   */
  it('never says far side, in either court shape', () => {
    for (const seats of [2, 4]) expect(awaitingBalanceLine(seats)).not.toMatch(/far side/i);
  });
});

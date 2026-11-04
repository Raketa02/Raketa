/**
 * **The wire boundary**, and the four things it must not get wrong.
 *
 * The sheet reads none of these fields twice, so every claim below is one this mapper is the
 * only place to make — and three of them are absences, which is where a mapper quietly turns
 * *we have nothing to say* into a nought.
 */

import {
  FILTER_OFF,
  HIDDEN_BY_A_HIGH_FILTER,
  MARTA_FILTER,
  SERGIO_RELIABILITY,
  servedReliability,
} from '@/test-support/playerRecord';
import type { Wire } from '@/test-support/transport';

import { toPlayerRecord } from './playerRecordMappers';

const PHOTO = 'https://photos.example/one.jpg';

function response(over: Partial<Wire['PlayerRecordResponse']> = {}): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    nickname: 'bea_k',
    area_code: 'A+050612+0019938',
    social_tags: ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN'],
    sports: [
      { sport: 'PADEL', level: 2.75, band: 'Established' },
      { sport: 'SQUASH', level: 2.9, band: 'Established' },
    ],
    reliability: servedReliability(),
    ...over,
  };
}

function skill(over: Partial<Wire['SkillPanelSchema']> = {}): Wire['SkillPanelSchema'] {
  return {
    sport: 'PADEL',
    level: 2.75,
    band: 'Established',
    confidence: 77,
    counted_games: 21,
    likely_range: { low: 2.47, high: 3.03 },
    last_five: ['WIN', 'WIN', 'LOSS'],
    ...over,
  };
}

describe('the record, off the wire', () => {
  it('takes `is_self` from the server rather than comparing anything', () => {
    expect(toPlayerRecord(response({ is_self: true })).isSelf).toBe(true);
    expect(toPlayerRecord(response()).isSelf).toBe(false);
  });

  it('keeps the sports in the order they were served', () => {
    expect(toPlayerRecord(response()).sports).toEqual([
      { sport: 'padel', level: 2.75 },
      { sport: 'squash', level: 2.9 },
    ]);
  });

  it('drops a sport this build has never heard of rather than drawing a pill with no name', () => {
    const served = response({
      sports: [
        { sport: 'PICKLEBALL' as Wire['Sport'], level: 3.1, band: 'Established' },
        { sport: 'PADEL', level: 2.75, band: 'Established' },
      ],
    });

    expect(toPlayerRecord(served).sports).toEqual([{ sport: 'padel', level: 2.75 }]);
  });

  it('carries the intro verbatim where they wrote one, and omits it where they did not', () => {
    // Their own words, untouched — never trimmed, never shortened, never an empty string
    // standing in for none (ADR-0170 §3).
    expect(toPlayerRecord(response({ intro: 'Will travel for a hard game.' })).intro).toBe(
      'Will travel for a hard game.',
    );
    expect(toPlayerRecord(response())).not.toHaveProperty('intro');
  });

  it('drops a Social tag this build cannot name, and keeps the rest in served order', () => {
    const served = response({ social_tags: ['STAYS_FOR_A_DRINK', 'SINGS_IN_THE_CAR'] });

    expect(toPlayerRecord(served).socialTags).toEqual(['STAYS_FOR_A_DRINK']);
  });
});

/**
 * **The reader's own block, and only where there is somebody to block** (#587, ADR-0193 §3).
 *
 * `blocked_by_you` answers one direction — the reader's block of the subject, never theirs of the
 * reader. The sheet draws *Unblock* for `true`, *Block* for `false`, and neither where it is absent
 * — so the two cases that draw no row are folded to an absence here: your own record, whatever the
 * wire says, and a record whose blocks the server could not read.
 */
describe('your own block', () => {
  it('carries whether the reader blocked the subject, both ways', () => {
    expect(toPlayerRecord(response({ blocked_by_you: true })).blockedByYou).toBe(true);
    expect(toPlayerRecord(response({ blocked_by_you: false })).blockedByYou).toBe(false);
  });

  it('is absent on your own record, so no row can be drawn there', () => {
    const own = toPlayerRecord(response({ is_self: true, blocked_by_you: false }));

    expect('blockedByYou' in own).toBe(false);
  });

  it('is absent where the server could not read the blocks, rather than guessed', () => {
    expect('blockedByYou' in toPlayerRecord(response())).toBe(false);
  });
});

/**
 * **The mark is folded here and nowhere else.**
 *
 * Three answers reach this route — checked and passed, checked and flagged, and nobody
 * looked — and two of them draw identically. Collapsing them at the boundary is what makes a
 * second reading of the verdict unrepresentable rather than merely absent: no component can
 * tell a reader that a stranger's photograph was doubted, because no component is handed the
 * code (ADR-0138).
 */
describe('the ON COURT mark', () => {
  it('is worn only where a photograph passed', () => {
    expect(toPlayerRecord(response({ photo_url: PHOTO, review: 'allowed' })).onCourt).toBe(true);
  });

  it('is not worn where the check flagged it, and says nothing about that either way', () => {
    const flagged = toPlayerRecord(response({ photo_url: PHOTO, review: 'flagged' }));
    const unchecked = toPlayerRecord(response({ photo_url: PHOTO }));

    expect(flagged.onCourt).toBe(false);
    expect(flagged).toEqual(unchecked);
  });

  it('is not worn over a poster, which has nothing to have passed', () => {
    expect(toPlayerRecord(response({ review: 'allowed' })).onCourt).toBe(false);
  });

  it('is not worn on a verdict this build has never seen', () => {
    const served = response({ photo_url: PHOTO, review: 'unreadable' as Wire['OnCourtVerdict'] });

    expect(toPlayerRecord(served).onCourt).toBe(false);
  });
});

describe('the skill panel', () => {
  it('carries the resolved sport, not the one that was asked for', () => {
    const served = response({ skill: skill({ sport: 'SQUASH' }) });

    expect(toPlayerRecord(served).skill?.sport).toBe('squash');
  });

  it('is absent where nothing resolved, and no panel of noughts stands in for it', () => {
    expect(toPlayerRecord(response({ sports: [] })).skill).toBeUndefined();
  });

  it('is absent where the resolved sport is one this build cannot name', () => {
    const served = response({ skill: skill({ sport: 'PICKLEBALL' as Wire['Sport'] }) });

    expect(toPlayerRecord(served).skill).toBeUndefined();
  });

  it('keeps the run oldest to newest and never pads it', () => {
    const served = response({ skill: skill({ last_five: ['LOSS', 'WIN'] }) });

    expect(toPlayerRecord(served).skill?.lastFive).toEqual(['LOSS', 'WIN']);
  });

  /**
   * The run's **length is a claim**, so a run half read is a run that cannot be drawn: dropping
   * the unreadable one would say one counted game fewer than the platform has. The whole field
   * goes, and the Level, the confidence and the counted figure beside it go on printing.
   */
  it('drops the whole run when one outcome cannot be read, and keeps everything beside it', () => {
    const served = response({
      skill: skill({ last_five: ['WIN', 'RETIRED' as Wire['GameOutcome'], 'WIN'] }),
    });
    const read = toPlayerRecord(served).skill;

    expect(read?.lastFive).toBeUndefined();
    expect(read?.countedGames).toBe(21);
  });

  it('draws an empty run as an empty run rather than as an absence', () => {
    const served = response({ skill: skill({ last_five: [] }) });

    expect(toPlayerRecord(served).skill?.lastFive).toEqual([]);
  });
});

/**
 * **Player reliability is points, and it is always there** (#660, ADR-0195 §1). Everyone starts
 * at 100, so the block crosses for a player nothing has happened to as for anybody — `100`,
 * *New*, every count nought — and the one thing this boundary still narrows is the band's code.
 */
describe('what the platform watched', () => {
  it('carries the figure, the band, New and the four counts, field for field', () => {
    const served = response({ reliability: SERGIO_RELIABILITY });

    expect(toPlayerRecord(served).reliability).toEqual({
      playerScore: 75,
      band: 'HIGH',
      isNew: false,
      counts: { turnedUp: 12, turnedUpOf: 13, late: 1, kept: 13, keptOf: 14, leftInDispute: 0 },
    });
  });

  it('carries a player nothing has happened to as 100 and New, with every count at nought', () => {
    const served = response({ reliability: servedReliability() });

    expect(toPlayerRecord(served).reliability).toEqual({
      playerScore: 100,
      band: 'VERY_HIGH',
      isNew: true,
      counts: { turnedUp: 0, turnedUpOf: 0, late: 0, kept: 0, keptOf: 0, leftInDispute: 0 },
    });
  });

  /**
   * **The figure without its word, rather than a guessed word.** A band this build cannot name
   * — one added after this phone was installed — drops the word and keeps the points: the figure
   * is still the server's and still true, and a client mapping it onto a band of its own would
   * be the thresholds this feature gave up.
   */
  it('drops a band this build has no words for, and keeps the figure and the counts', () => {
    const served = response({
      reliability: servedReliability({
        player_score: 42,
        band: 'SHAKY' as Wire['ReliabilityBand'],
        is_new: false,
        late: 3,
      }),
    });
    const read = toPlayerRecord(served).reliability;

    expect(read).not.toHaveProperty('band');
    expect(read.playerScore).toBe(42);
    expect(read.counts.late).toBe(3);
  });
});

/**
 * **The filter, on your own record** (#662, ADR-0195 §6) — two facts off one wire object: the
 * player's own switch with what it hides, and the figure that deals them with everyone again
 * where somebody else's filter keeps them off a court. Each is its own absence.
 */
describe('the reliability filter', () => {
  it('is absent on everybody else’s record, both halves', () => {
    const read = toPlayerRecord(response()).reliability;

    expect(read).not.toHaveProperty('filter');
    expect(read).not.toHaveProperty('backWithEveryone');
  });

  it('carries a filter that is off with no minimum, and the counts as served', () => {
    const served = response({
      is_self: true,
      reliability: servedReliability({ filter: FILTER_OFF }),
    });

    expect(toPlayerRecord(served).reliability.filter).toEqual({ hides: 0, of: 11 });
    expect(toPlayerRecord(served).reliability).not.toHaveProperty('backWithEveryone');
  });

  it('carries the saved minimum and what it hides', () => {
    const served = response({
      is_self: true,
      reliability: servedReliability({ filter: MARTA_FILTER }),
    });

    expect(toPlayerRecord(served).reliability.filter).toEqual({
      minimum: 'HIGH',
      hides: 2,
      of: 11,
    });
  });

  it('carries the figure back where somebody’s filter hides the reader, beside their own switch', () => {
    const served = response({
      is_self: true,
      reliability: servedReliability({ filter: HIDDEN_BY_A_HIGH_FILTER }),
    });
    const read = toPlayerRecord(served).reliability;

    expect(read.filter).toEqual({ hides: 0, of: 11 });
    expect(read.backWithEveryone).toEqual({ band: 'HIGH', points: 75 });
  });

  /**
   * **A switch is never drawn standing at Off over a filter that is on.** A minimum this build
   * cannot name — a band the route began to offer after this phone was installed — takes the
   * switch and its line with it; the figure back is a different fact and stays.
   */
  it('drops the switch for a minimum this build cannot name, and keeps the figure back', () => {
    const served = response({
      is_self: true,
      reliability: servedReliability({
        filter: {
          ...HIDDEN_BY_A_HIGH_FILTER,
          minimum: 'VERY_HIGH' as Wire['ReliabilityFilterSchema']['minimum'],
          hides: 5,
        },
      }),
    });
    const read = toPlayerRecord(served).reliability;

    expect(read).not.toHaveProperty('filter');
    expect(read.backWithEveryone).toEqual({ band: 'HIGH', points: 75 });
  });

  /** The sentence names the band, so a band with no word is no sentence rather than a blank. */
  it('drops the figure back where its band has no word on this build, and keeps the switch', () => {
    const served = response({
      is_self: true,
      reliability: servedReliability({
        filter: {
          ...MARTA_FILTER,
          back_with_everyone: { band: 'SHAKY' as Wire['ReliabilityBand'], points: 60 },
        },
      }),
    });
    const read = toPlayerRecord(served).reliability;

    expect(read.filter).toEqual({ minimum: 'HIGH', hides: 2, of: 11 });
    expect(read).not.toHaveProperty('backWithEveryone');
  });
});

/**
 * **A different absence, asking a different question.** Somebody rated in nothing may have
 * played all week, and somebody rated in four sports may never have had a game counted — so
 * this moves with neither the skill panel nor the counts above it.
 */
describe('how widely they spread their games', () => {
  it('carries the raw pair, and never a share computed at the boundary', () => {
    const served = response({ variety: { distinct_opponents: 14, times_on_court: 20 } });

    expect(toPlayerRecord(served).variety).toEqual({ distinctOpponents: 14, timesOnCourt: 20 });
  });

  it('is absent where no counted game was ever recorded, and never `0 of 0`', () => {
    expect(toPlayerRecord(response()).variety).toBeUndefined();
  });
});

/**
 * **What other players said — one figure, for every reader.**
 *
 * The band a subject used to be answered with is retired ([#468](https://github.com/Raketa02/Raketa/issues/468),
 * ADR-0179 §5): the wire carries `sportsmanship` whoever is asking, and the mapper reads it
 * whoever is asking. `Opinion` is the figure and its count and nothing else
 * ([#473](https://github.com/Raketa02/Raketa/issues/473)) — no arm, no discriminator — so what
 * this suite holds is that a self read is mapped exactly as a stranger's is.
 */
describe('what other players said', () => {
  const SAID = { average: 4.7, raters: 17 };

  it('carries the average and the count of people it rests on', () => {
    expect(toPlayerRecord(response({ sportsmanship: SAID })).opinion).toEqual({
      average: 4.7,
      raters: 17,
    });
  });

  it('answers your own record with the same figure, since the band was retired', () => {
    const served = response({ is_self: true, sportsmanship: SAID });

    expect(toPlayerRecord(served).opinion).toEqual({ average: 4.7, raters: 17 });
  });

  it('is absent where nobody has said anything, and never at nought', () => {
    expect(toPlayerRecord(response()).opinion).toBeUndefined();
    expect(toPlayerRecord(response({ is_self: true })).opinion).toBeUndefined();
  });
});

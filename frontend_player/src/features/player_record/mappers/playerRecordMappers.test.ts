/**
 * **The wire boundary**, and the four things it must not get wrong.
 *
 * The sheet reads none of these fields twice, so every claim below is one this mapper is the
 * only place to make — and three of them are absences, which is where a mapper quietly turns
 * *we have nothing to say* into a nought.
 */

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

  it('drops a Social tag this build cannot name, and keeps the rest in served order', () => {
    const served = response({ social_tags: ['STAYS_FOR_A_DRINK', 'SINGS_IN_THE_CAR'] });

    expect(toPlayerRecord(served).socialTags).toEqual(['STAYS_FOR_A_DRINK']);
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
 * **Nothing is ever a nought here.** *We have not seen enough* and *they are bad at this* are
 * different facts, and a mapper defaulting one to the other is where the difference is lost.
 */
describe('what the platform watched', () => {
  it('carries the figure the matcher acts on', () => {
    const served = response({
      reliability: {
        player_score: 93,
        strands: [{ strand: 'SHOWS_UP', good: 9, opportunities: 9, pct: 100 }],
      },
    });

    expect(toPlayerRecord(served).playerScore).toBe(93);
  });

  it('leaves it absent where nothing has ever fallen due, and never at nought', () => {
    expect(toPlayerRecord(response()).playerScore).toBeUndefined();
  });
});

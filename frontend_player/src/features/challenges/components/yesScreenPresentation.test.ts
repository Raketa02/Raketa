/**
 * **What the yes screen says, on its own.** The spoken sentence is the one thing a listener gets
 * of the picture, so both faces' are pinned here: whole handles, never the initials, *an empty
 * seat* where one is after a challenge — and after a mutual only *you and them*, with no
 * *against* and no empty seat in it, whatever the sport.
 */

import {
  CHALLENGE_WORD,
  LATER,
  MATCHED_WORD,
  VS,
  YES_SENTENCE,
  YES_WORD,
  matchedAnnouncement,
  yesAnnouncement,
} from './yesScreenPresentation';

describe('the spoken sentence', () => {
  it('names both people on a singles court, whole', () => {
    expect(
      yesAnnouncement({
        yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }],
        theirs: [{ kind: 'person', playerId: 'ewa', nickname: 'Ewa.M' }],
      }),
    ).toBe('Challenge! You against Ewa.M');
  });

  it('names a partner and both opponents on a doubles court', () => {
    expect(
      yesAnnouncement({
        yours: [
          { kind: 'person', playerId: 'me', nickname: 'Tomek.K' },
          { kind: 'person', playerId: 'ola', nickname: 'Ola.N' },
        ],
        theirs: [
          { kind: 'person', playerId: 'kuba', nickname: 'Kuba.W' },
          { kind: 'person', playerId: 'zofia', nickname: 'Zofia.B' },
        ],
      }),
    ).toBe('Challenge! You and Ola.N against Kuba.W and Zofia.B');
  });

  it('says an empty seat where one is, on either side', () => {
    expect(
      yesAnnouncement({
        yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }, { kind: 'empty' }],
        theirs: [{ kind: 'person', playerId: 'kuba', nickname: 'Kuba.W' }, { kind: 'empty' }],
      }),
    ).toBe('Challenge! You and an empty seat against Kuba.W and an empty seat');
  });

  it('never carries the initials, and names a seat the record cannot as nobody', () => {
    const spoken = yesAnnouncement({
      yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }],
      theirs: [{ kind: 'person', playerId: 'gone' }],
    });

    expect(spoken).toBe('Challenge! You against ?');
    expect(spoken).not.toMatch(/\bTK\b/);
  });
});

/**
 * **The mutual's sentence says only *you two*** (ADR-0167 §4): in tennis the two are opponents,
 * in padel partners with a side to fill, and both are true of the two people — so the sentence
 * never says *against*, never names an empty seat, and never calls the thing a game or a court.
 */
describe('the spoken sentence after a mutual', () => {
  it('names the two of you, whole, and nothing about the court', () => {
    expect(
      matchedAnnouncement({
        yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }],
        theirs: [{ kind: 'person', playerId: 'marek', nickname: 'Marek.P' }],
      }),
    ).toBe('Matched! You and Marek.P');
  });

  it('never says against, never an empty seat, and never the initials', () => {
    const spoken = matchedAnnouncement({
      yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }],
      theirs: [{ kind: 'person', playerId: 'marek', nickname: 'Marek.P' }],
    });

    expect(spoken).not.toMatch(/against|empty seat|\bvs\b|\bgame\b|\bcourt\b/i);
    expect(spoken).not.toMatch(/\bTK\b|\bMP\b/);
  });

  it('names everybody who has said yes on a court that has grown', () => {
    expect(
      matchedAnnouncement({
        yours: [{ kind: 'person', playerId: 'me', nickname: 'Tomek.K' }],
        theirs: [
          { kind: 'person', playerId: 'marek', nickname: 'Marek.P' },
          { kind: 'person', playerId: 'kuba', nickname: 'Kuba.W' },
        ],
      }),
    ).toBe('Matched! You and Marek.P and Kuba.W');
  });
});

describe('the words the mock draws', () => {
  it('are the two words, the small vs, and the two doors', () => {
    expect(CHALLENGE_WORD).toBe('Challenge!');
    expect(MATCHED_WORD).toBe('Matched!');
    expect(VS).toBe('vs');
    expect(LATER).toBe('Later');
  });

  /** One word and one sentence per face, keyed by the same union the route checks. */
  it('key one word and one sentence to each face of the screen', () => {
    expect(YES_WORD).toEqual({ challenge: CHALLENGE_WORD, mutual: MATCHED_WORD });
    expect(YES_SENTENCE).toEqual({ challenge: yesAnnouncement, mutual: matchedAnnouncement });
  });
});

/**
 * **What the yes screen says, on its own.** The spoken sentence is the one thing a listener gets
 * of the picture, so it is pinned here: whole handles, never the initials, and *an empty seat*
 * where one is.
 */

import { CHALLENGE_WORD, LATER, VS, yesAnnouncement } from './yesScreenPresentation';

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

describe('the words the mock draws', () => {
  it('are the one word, the small vs, and the two doors', () => {
    expect(CHALLENGE_WORD).toBe('Challenge!');
    expect(VS).toBe('vs');
    expect(LATER).toBe('Later');
  });
});

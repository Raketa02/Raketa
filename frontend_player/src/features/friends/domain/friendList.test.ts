import { playedWithShown, type PlayedWithPerson } from './friendList';

const person = (
  playerId: string,
  relation: PlayedWithPerson['relation'],
  nickname: string | null = playerId,
): PlayedWithPerson => ({ playerId, relation, ...(nickname === null ? {} : { nickname }) });

describe('playedWithShown — who PLAYED WITH lists, or nobody', () => {
  it('lists the others in the order they came, each with where you stand', () => {
    const shown = playedWithShown([
      person('ewa', 'FRIEND'),
      person('magda', 'NONE'),
      person('ania', 'SENT'),
    ]);
    expect(shown.map((one) => [one.playerId, one.relation])).toEqual([
      ['ewa', 'FRIEND'],
      ['magda', 'NONE'],
      ['ania', 'SENT'],
    ]);
  });

  it('lists nobody once every one of them is your friend: the card is hidden', () => {
    expect(playedWithShown([person('ewa', 'FRIEND'), person('magda', 'FRIEND')])).toEqual([]);
  });

  it('lists nobody for a reader not on the game, whose read names nobody', () => {
    expect(playedWithShown([])).toEqual([]);
  });

  // An account that can no longer be named can be neither drawn nor asked.
  it('leaves off somebody who can no longer be named, and hides on the rest', () => {
    expect(playedWithShown([person('gone', 'NONE', null), person('ewa', 'FRIEND')])).toEqual([]);
    expect(
      playedWithShown([person('gone', 'NONE', null), person('magda', 'ASKED_YOU')]).map(
        (one) => one.playerId,
      ),
    ).toEqual(['magda']);
  });
});

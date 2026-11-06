import { toAskRequest } from './friendsMappers';

describe('toAskRequest', () => {
  it('names the group and the sport the screen showed', () => {
    expect(toAskRequest('p-1', { from: 'MEMBERS', groupId: 'g-1', sport: 'padel' })).toEqual({
      player_id: 'p-1',
      made_from: 'MEMBERS',
      group_id: 'g-1',
      sport: 'PADEL',
    });
  });

  it('leaves both off where the screen showed neither', () => {
    expect(toAskRequest('p-1', { from: 'RECORD' })).toEqual({
      player_id: 'p-1',
      made_from: 'RECORD',
    });
  });
});

import { parseGameDetailsParams } from './gameDetailsParams';

const GROUP = 'a0000000-0000-4000-8000-000000000011';
const PROPOSAL = 'c0000000-0000-4000-8000-000000000001';

describe('a game’s details route params', () => {
  it('reads the group, the game, the sport and the kind', () => {
    expect(
      parseGameDetailsParams({
        groupId: GROUP,
        proposalId: PROPOSAL,
        sport: 'padel',
        kind: 'forFun',
      }),
    ).toEqual({ groupId: GROUP, proposalId: PROPOSAL, sport: 'padel', kind: 'forFun' });
  });

  it.each([
    ['a game id that is not one', { proposalId: 'nope' }],
    ['a sport this build cannot name', { sport: 'golf' }],
    ['a kind that is not a segment', { kind: 'FOR_FUN' }],
    ['a missing group', { groupId: undefined }],
  ])('refuses %s', (_case, override) => {
    expect(
      parseGameDetailsParams({
        groupId: GROUP,
        proposalId: PROPOSAL,
        sport: 'padel',
        kind: 'competitive',
        ...override,
      }),
    ).toBeUndefined();
  });
});

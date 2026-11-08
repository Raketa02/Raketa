import { movesTheFaces, recordAskedWhere, recordFootOf, rowEndOf } from './friendship';
import type { FriendRelation } from './vocabulary';

describe('rowEndOf — the right-hand end of a Members row', () => {
  it.each<[FriendRelation, ReturnType<typeof rowEndOf>]>([
    ['NONE', { kind: 'pill', act: 'ask' }],
    ['ASKED_YOU', { kind: 'pill', act: 'accept' }],
    ['SENT', { kind: 'tag', tag: 'sent' }],
    ['FRIEND', { kind: 'tag', tag: 'friend' }],
  ])('%s', (relation, end) => {
    expect(rowEndOf(relation)).toEqual(end);
  });
});

describe('recordFootOf — the record’s two buttons', () => {
  it('draws nothing on your own record', () => {
    expect(recordFootOf({ isSelf: true, relation: 'NONE', canAddFriend: false })).toEqual({
      kind: 'nothing',
    });
  });

  it.each<[FriendRelation, string]>([
    ['SENT', 'sent'],
    ['ASKED_YOU', 'accept'],
    ['FRIEND', 'friend'],
  ])('puts the %s button beside Block', (relation, button) => {
    expect(recordFootOf({ isSelf: false, relation, canAddFriend: false })).toEqual({
      kind: 'pair',
      button,
    });
  });

  it('puts Add friend beside Block where the record says a request may be sent', () => {
    expect(recordFootOf({ isSelf: false, relation: 'NONE', canAddFriend: true })).toEqual({
      kind: 'pair',
      button: 'ask',
    });
  });

  it('draws Block alone where nothing stands between you and no request may be sent', () => {
    expect(recordFootOf({ isSelf: false, relation: 'NONE', canAddFriend: false })).toEqual({
      kind: 'block',
    });
  });
});

describe('recordAskedWhere — where a request asked from the record is asked from', () => {
  it('is the record, with the group and the sport the caller opened it from', () => {
    expect(recordAskedWhere({ rankingSport: undefined, groupId: 'g-1', sport: 'padel' })).toEqual({
      from: 'RECORD',
      groupId: 'g-1',
      sport: 'padel',
    });
    expect(
      recordAskedWhere({ rankingSport: undefined, groupId: undefined, sport: undefined }),
    ).toEqual({ from: 'RECORD' });
  });

  it('is the ranking, with the page’s sport, where the record was opened on Rankings', () => {
    expect(
      recordAskedWhere({ rankingSport: 'squash', groupId: undefined, sport: 'squash' }),
    ).toEqual({
      from: 'RANKING',
      sport: 'squash',
    });
  });

  it('names no group with the ranking, whose page shows none', () => {
    expect(recordAskedWhere({ rankingSport: 'padel', groupId: 'g-1', sport: 'tennis' })).toEqual({
      from: 'RANKING',
      sport: 'padel',
    });
  });
});

describe('movesTheFaces — whether a friendship turned on or off', () => {
  it.each<[FriendRelation, FriendRelation, boolean]>([
    ['ASKED_YOU', 'FRIEND', true],
    ['NONE', 'FRIEND', true],
    ['FRIEND', 'NONE', true],
    ['NONE', 'SENT', false],
    ['SENT', 'NONE', false],
    ['FRIEND', 'FRIEND', false],
  ])('%s → %s', (before, after, moves) => {
    expect(movesTheFaces(before, after)).toBe(moves);
  });
});

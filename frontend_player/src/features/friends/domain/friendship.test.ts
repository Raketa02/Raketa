import {
  movesTheFaces,
  recordAskedWhere,
  recordFootOf,
  roundPressOf,
  rowEndOf,
  shownWhilePressed,
} from './friendship';
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

  it('is the row the record was opened from, with nothing else, where a Home row opened it (#801)', () => {
    expect(
      recordAskedWhere({
        rankingSport: undefined,
        groupId: undefined,
        sport: 'padel',
        foundIn: { from: 'NEW_PLAYERS' },
      }),
    ).toEqual({ from: 'NEW_PLAYERS' });
  });

  it('keeps Same competitive level’s sport, the card’s, over the record’s own (#802)', () => {
    expect(
      recordAskedWhere({
        rankingSport: undefined,
        groupId: undefined,
        sport: 'padel',
        foundIn: { from: 'SAME_LEVEL', sport: 'squash' },
      }),
    ).toEqual({ from: 'SAME_LEVEL', sport: 'squash' });
  });
});

describe('roundPressOf — what a tap on the round friend button does (#801)', () => {
  it.each<[FriendRelation, ReturnType<typeof roundPressOf>]>([
    ['NONE', 'ask'],
    ['SENT', 'requestSent'],
    ['FRIEND', 'remove'],
    ['ASKED_YOU', 'accept'],
  ])('%s', (relation, press) => {
    expect(roundPressOf(relation)).toBe(press);
  });
});

describe('shownWhilePressed — the relation the button draws while its write is out (#801)', () => {
  it('turns + to … and the envelope to ✓ at once', () => {
    expect(shownWhilePressed('NONE', 'ask')).toBe('SENT');
    expect(shownWhilePressed('ASKED_YOU', 'accept')).toBe('FRIEND');
  });

  it('keeps what the read said with nothing out', () => {
    expect(shownWhilePressed('SENT', undefined)).toBe('SENT');
    expect(shownWhilePressed('FRIEND', undefined)).toBe('FRIEND');
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

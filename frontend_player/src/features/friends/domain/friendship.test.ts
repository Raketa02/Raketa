import { movesTheFaces, recordFootOf, rowEndOf } from './friendship';
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
    expect(recordFootOf({ isSelf: true, relation: 'NONE', blockedByYou: false })).toEqual({
      kind: 'nothing',
    });
  });

  it('draws Unblock alone on somebody you blocked, whatever stands between you', () => {
    for (const relation of ['NONE', 'SENT', 'ASKED_YOU', 'FRIEND'] as const) {
      expect(recordFootOf({ isSelf: false, relation, blockedByYou: true })).toEqual({
        kind: 'unblock',
      });
    }
  });

  it.each<[FriendRelation, string]>([
    ['NONE', 'ask'],
    ['SENT', 'sent'],
    ['ASKED_YOU', 'accept'],
    ['FRIEND', 'friend'],
  ])('puts the %s button beside Block', (relation, button) => {
    expect(recordFootOf({ isSelf: false, relation, blockedByYou: false })).toEqual({
      kind: 'pair',
      button,
      block: true,
    });
  });

  it('draws the friend button alone where the blocks could not be read', () => {
    expect(recordFootOf({ isSelf: false, relation: 'NONE' })).toEqual({
      kind: 'pair',
      button: 'ask',
      block: false,
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

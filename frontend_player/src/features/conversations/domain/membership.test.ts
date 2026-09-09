/**
 * The one rule membership carries into a client: **a line names a member, or it names nobody.**
 *
 * `{name}` is filled from the members the row already holds and never from `values`, so an actor
 * the room cannot answer for has to land somewhere honest rather than in a gap the sentence
 * papers over.
 */

import { playerName } from '@/shared/formatting/playerName';

import { memberNamed, othersIn, type ConversationMember } from './membership';

const ME = 'me';
const TOMEK: ConversationMember = { playerId: 'tomek', nickname: 'tomek.p' };
const OLA: ConversationMember = { playerId: 'ola', nickname: 'ola.k' };
const GONE: ConversationMember = { playerId: 'gone' };

describe('who the row draws', () => {
  it('is everybody but the reader, in the order the fold answered them', () => {
    const members = [TOMEK, { playerId: ME, nickname: 'me_' }, OLA];

    expect(othersIn(members, ME)).toEqual([TOMEK, OLA]);
  });

  /** A room grows one acceptance at a time, and draws the members it has. */
  it('draws two for a doubles room whose line-up is still filling', () => {
    expect(othersIn([TOMEK, { playerId: ME }], ME)).toHaveLength(1);
  });
});

describe('who a sentence may name', () => {
  it('names a member by the whole handle they chose', () => {
    expect(playerName(memberNamed([TOMEK, OLA], 'ola'))).toBe('ola.k');
  });

  it('names nobody for an actor the room has no handle for', () => {
    expect(memberNamed([GONE], 'gone')).toEqual({ kind: 'unknown' });
  });

  it('names nobody for an actor who is not in the room, and for no actor at all', () => {
    expect(memberNamed([TOMEK], 'somebody-else')).toEqual({ kind: 'unknown' });
    expect(memberNamed([TOMEK], undefined)).toEqual({ kind: 'unknown' });
  });
});

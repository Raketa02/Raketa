/**
 * The one rule membership carries into a client: **a line names somebody the response named, or
 * it names nobody.**
 *
 * `{name}` is filled from the people the response names and never from `values`, so an actor
 * nobody can answer for has to land somewhere honest rather than in a gap the sentence papers
 * over — and the people accumulate with the pages, merged by id and never replaced.
 */

import { playerName } from '@/shared/formatting/playerName';

import {
  mergedPeople,
  othersIn,
  personNamed,
  type ConversationMember,
  type ConversationPerson,
} from './membership';

const ME = 'me';
const TOMEK: ConversationMember = { playerId: 'tomek', name: 'tomek.p' };
const OLA: ConversationMember = { playerId: 'ola', name: 'ola.k' };
const GONE: ConversationMember = { playerId: 'gone' };
/** Somebody a line names who was never a member — a *no* is not an accepted seat. */
const BO: ConversationPerson = { playerId: 'bo', name: 'bo' };

describe('who the row draws', () => {
  it('is everybody but the reader, in the order the fold answered them', () => {
    const members = [TOMEK, { playerId: ME, name: 'me_' }, OLA];

    expect(othersIn(members, ME)).toEqual([TOMEK, OLA]);
  });

  /** A room grows one acceptance at a time, and draws the members it has. */
  it('draws two for a doubles room whose line-up is still filling', () => {
    expect(othersIn([TOMEK, { playerId: ME }], ME)).toHaveLength(1);
  });
});

describe('who a sentence may name', () => {
  it('names a person by the whole handle they chose', () => {
    expect(playerName(personNamed([TOMEK, OLA], 'ola'))).toBe('ola.k');
  });

  /** The whole point of the second list: the departed are named, though they are not members. */
  it('names somebody the response named who is not on the court', () => {
    expect(playerName(personNamed([TOMEK, OLA, BO], 'bo'))).toBe('bo');
  });

  it('names nobody for an actor the platform has no handle for', () => {
    expect(personNamed([GONE], 'gone')).toEqual({ kind: 'unknown' });
  });

  it('names nobody for an actor the response did not name, and for no actor at all', () => {
    expect(personNamed([TOMEK], 'somebody-else')).toEqual({ kind: 'unknown' });
    expect(personNamed([TOMEK], undefined)).toEqual({ kind: 'unknown' });
  });
});

describe('the people accumulate with the pages', () => {
  /** A page backward names its own authors and actors, and the room's first read could not. */
  it('adds whoever a later page names', () => {
    expect(mergedPeople([[TOMEK, OLA], [BO]])).toEqual([TOMEK, OLA, BO]);
  });

  /**
   * One face per id, and **the first list's**: the pages are held newest first, and the newest
   * is the read the room is folded against — a later page names people, it never re-names one.
   */
  it('keeps one face per person, the first one held', () => {
    const renamed: ConversationPerson = { playerId: 'tomek', name: 'tomek.new' };

    expect(mergedPeople([[TOMEK], [renamed, BO]])).toEqual([TOMEK, BO]);
  });

  it('is nobody over no pages', () => {
    expect(mergedPeople([])).toEqual([]);
  });
});

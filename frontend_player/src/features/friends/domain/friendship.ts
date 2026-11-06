/**
 * **What a relation draws, and where a request was asked from**
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); the friends screens §1–§2; ADR-0202 §1).
 *
 * The rules a surface would otherwise spell in a ternary: which end a Members row ends in, and which
 * buttons the record's foot holds. Both are the server's relation read one way, so Members and the
 * record a row opens can never say two things about one person.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { AskedFrom, FriendRelation } from './vocabulary';

/**
 * **Where a request is asked from** — the screen, and the group and sport it showed, which the other
 * person's Home card names (*With you in Kazimierz crew · Padel 3,40*). The server keeps the group
 * only while the two share it, so naming one here claims nothing.
 */
export interface AskedWhere {
  readonly from: AskedFrom;
  readonly groupId?: string;
  readonly sport?: Sport;
}

/**
 * **The right-hand end of a Members row** (the screens §1; friends 1, 2): a pill that acts, or a tag
 * that says. Your own row ends in nothing — the caller draws none for it.
 */
export type RowEnd =
  | { readonly kind: 'pill'; readonly act: 'ask' | 'accept' }
  | { readonly kind: 'tag'; readonly tag: 'sent' | 'friend' };

export function rowEndOf(relation: FriendRelation): RowEnd {
  switch (relation) {
    case 'NONE':
      return { kind: 'pill', act: 'ask' };
    case 'ASKED_YOU':
      return { kind: 'pill', act: 'accept' };
    case 'SENT':
      return { kind: 'tag', tag: 'sent' };
    case 'FRIEND':
      return { kind: 'tag', tag: 'friend' };
  }
}

/** The record's left button, by relation: *Add friend*, *Request sent ▾*, *Accept*, *Friend ✓ ▾*. */
export type FriendButton = 'ask' | 'sent' | 'accept' | 'friend';

const BUTTON: Readonly<Record<FriendRelation, FriendButton>> = {
  NONE: 'ask',
  SENT: 'sent',
  ASKED_YOU: 'accept',
  FRIEND: 'friend',
};

/**
 * **The record's foot** (the screens §2; Q3, Q40):
 *
 * - `nothing` — your own record;
 * - `unblock` — somebody the reader blocked: *Unblock*, full width and alone, and never an offer to
 *   befriend them (the mechanics §3.5);
 * - `pair` — the friend button on the left and, where the blocks were read, *Block* on the right. A
 *   record whose blocks could not be read carries no `blockedByYou` and so no Block (`blocks`' rule:
 *   the row is the record's answer, never a guess) — the friend button stands alone there.
 */
export type RecordFoot =
  | { readonly kind: 'nothing' }
  | { readonly kind: 'unblock' }
  | { readonly kind: 'pair'; readonly button: FriendButton; readonly block: boolean };

export function recordFootOf(record: {
  readonly isSelf: boolean;
  readonly relation: FriendRelation;
  readonly blockedByYou?: boolean;
}): RecordFoot {
  if (record.isSelf) return { kind: 'nothing' };
  if (record.blockedByYou === true) return { kind: 'unblock' };
  return {
    kind: 'pair',
    button: BUTTON[record.relation],
    block: record.blockedByYou === false,
  };
}

/**
 * **Whether an act turned a friendship on or off** — and so every face's *friend* tag with it: an
 * accept, a crossed request, a removal. Asking and cancelling leave the faces as they were.
 */
export function movesTheFaces(before: FriendRelation, after: FriendRelation): boolean {
  return (before === 'FRIEND') !== (after === 'FRIEND');
}

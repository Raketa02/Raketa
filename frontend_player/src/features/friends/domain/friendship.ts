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
 *
 * **A request from the ranking carries the page's sport and no group** (#779; the rankings mechanics
 * §13.2): its card reads *Found you in the padel ranking*, so the sport is the ranking it names and
 * the server refuses one without it — the type says so, rather than a `422` on the day a caller
 * forgets.
 */
export type AskedWhere =
  | {
      readonly from: Exclude<AskedFrom, 'RANKING'>;
      readonly groupId?: string;
      readonly sport?: Sport;
    }
  | { readonly from: 'RANKING'; readonly sport: Sport };

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
 * **The record's foot** (the friends screens §2; the rankings screens §6; Q3, Q40; ADR-0203 §8–§9):
 *
 * - `nothing` — your own record;
 * - `pair` — the friend button on the left and *Block* on the right;
 * - `block` — *Block* alone: nothing stands between you, and the record says no request may be sent
 *   (`canAddFriend`). Since ADR-0204 §2 (#799) a record that opens is somebody you may ask, so the
 *   server answers `false` with `NONE` on no record it serves today; the foot still follows the
 *   record's own flag rather than a rule spelled again here.
 *
 * **There is no *Unblock* here** (#779): a record never opens between two people either of whom
 * blocked the other (#773), so *Block* is always *Block*, and Unblock lives in You › Blocked players.
 */
export type RecordFoot =
  | { readonly kind: 'nothing' }
  | { readonly kind: 'block' }
  | { readonly kind: 'pair'; readonly button: FriendButton };

export function recordFootOf(record: {
  readonly isSelf: boolean;
  readonly relation: FriendRelation;
  readonly canAddFriend: boolean;
}): RecordFoot {
  if (record.isSelf) return { kind: 'nothing' };
  if (record.relation === 'NONE' && !record.canAddFriend) return { kind: 'block' };
  return { kind: 'pair', button: BUTTON[record.relation] };
}

/**
 * **Where a request asked from the record is asked from** — the record, with the group and the sport
 * the caller opened it on; or **the ranking**, with the page's sport, where the caller is the Rankings
 * page (#779; the rankings screens §6, the mechanics §13.2). The page shows no group, so none is named
 * with it, and the sport is the ranking's, whatever sport the record is about.
 */
export function recordAskedWhere(opened: {
  /** The sport of the Rankings page the record was opened on — `undefined` everywhere else. */
  readonly rankingSport: Sport | undefined;
  readonly groupId: string | undefined;
  readonly sport: Sport | undefined;
}): AskedWhere {
  if (opened.rankingSport !== undefined) return { from: 'RANKING', sport: opened.rankingSport };
  return {
    from: 'RECORD',
    ...(opened.groupId === undefined ? {} : { groupId: opened.groupId }),
    ...(opened.sport === undefined ? {} : { sport: opened.sport }),
  };
}

/**
 * **Whether an act turned a friendship on or off** — and so every face's *friend* tag with it: an
 * accept, a crossed request, a removal. Asking and cancelling leave the faces as they were.
 */
export function movesTheFaces(before: FriendRelation, after: FriendRelation): boolean {
  return (before === 'FRIEND') !== (after === 'FRIEND');
}

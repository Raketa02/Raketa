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
      readonly from: Exclude<AskedFrom, 'RANKING' | 'NEW_PLAYERS'>;
      readonly groupId?: string;
      readonly sport?: Sport;
    }
  | { readonly from: 'RANKING'; readonly sport: Sport }
  | FoundIn;

/**
 * **A Home row a request was found in** (#801; the Home rows mechanics §12) — sent from the row's
 * round button, or from a record the row opened, so the other person's card says where they were
 * found. New in Raketa names nothing else: *Found you among new players*, whatever group or sport
 * the two share. The rows still to come (#802, #803) add theirs here.
 */
export type FoundIn = { readonly from: 'NEW_PLAYERS' };

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
 * with it, and the sport is the ranking's, whatever sport the record is about. **A record a Home row
 * opened keeps the row** (#801; the Home rows mechanics §12): *a request sent from a record keeps the
 * row the record was opened from*.
 */
export function recordAskedWhere(opened: {
  /** The sport of the Rankings page the record was opened on — `undefined` everywhere else. */
  readonly rankingSport: Sport | undefined;
  readonly groupId: string | undefined;
  readonly sport: Sport | undefined;
  /** The Home row the record was opened from — absent everywhere else. */
  readonly foundIn?: FoundIn | undefined;
}): AskedWhere {
  if (opened.foundIn !== undefined) return opened.foundIn;
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

/**
 * **What a tap on the round friend button does** (#801; the Home rows mechanics §11; Q29) — on every
 * card of the people rows, keyed by where the reader stands with the person:
 *
 * | Relation | Mark | A tap |
 * | --- | --- | --- |
 * | `NONE` | **+**, white | `ask` — a request at once |
 * | `SENT` | **…**, brown | `requestSent` — the *Request sent* sheet, with *Cancel request* |
 * | `FRIEND` | **✓**, green | `remove` — *Remove … as a friend?* |
 * | `ASKED_YOU` | the envelope, volt | `accept` — at once |
 */
export type RoundPress = 'ask' | 'requestSent' | 'remove' | 'accept';

const ROUND_PRESS: Readonly<Record<FriendRelation, RoundPress>> = {
  NONE: 'ask',
  SENT: 'requestSent',
  FRIEND: 'remove',
  ASKED_YOU: 'accept',
};

export function roundPressOf(relation: FriendRelation): RoundPress {
  return ROUND_PRESS[relation];
}

/** The two presses that write at once — each the step its button draws before the answer lands. */
export type ImmediatePress = Extract<RoundPress, 'ask' | 'accept'>;

const GUESSED: Readonly<Record<ImmediatePress, FriendRelation>> = {
  ask: 'SENT',
  accept: 'FRIEND',
};

/**
 * **The relation the button draws** (the Home rows screens §8.1): **+** turns to **…** and the
 * envelope to **✓** the moment it is pressed, while the write is out — and once it has settled, the
 * read under it says what the server did. A failed write is no longer out, so the read's own relation
 * is drawn again: *a failed write puts it back*.
 */
export function shownWhilePressed(
  relation: FriendRelation,
  out: ImmediatePress | undefined,
): FriendRelation {
  return out === undefined ? relation : GUESSED[out];
}

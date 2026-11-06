/**
 * **A Members row's right-hand end** — **+ Add**, *request sent*, *friend* or **Accept**
 * ([#753](https://github.com/Raketa02/Raketa/issues/753); the friends screens §1; friends 1, 2).
 *
 * ```
 * ┌ the row (groups') ─────────────────────────────┐ ┌──────────┐
 * │ face  kuba.w ✦96                               │ │  + Add   │   black pill: acts
 * │       • Padel 2,80                             │ └──────────┘
 * └────────────────────────────────────────────────┘
 *                                                    request sent    amber tag: says
 * ```
 *
 * ## The row is `groups'`; the end is this feature's
 *
 * **The rows keep today's design** (the README's override 1): Members draws its own row — face,
 * nickname, reliability chip, the sport's line — and hands it in as `children`; this draws it with
 * the end on its right and the write's note under both. So `groups` never names a friends act, and
 * this feature never names a Members key: the list's re-read is handed in (`reread`), `blocks`'
 * `rereadRecord` seam.
 *
 * ## The pill acts; the rest of the row opens the record
 *
 * **The pill is a sibling of the row's own press, never inside it** — two controls side by side, so
 * a tap on the face or the name opens the record (`groups'` press) and only the pill sends a request
 * (the screens §1: *so nobody sends a request by accident*). A tag is never pressable (6.4).
 *
 * The pill is the `dark` button in the chip's pill at `sm` (Part 16, 2026-11-06), spoken with the
 * person's nickname — a column of *+ Add* names nobody. **It stays busy until the list under it has
 * re-read**, so the row turns *request sent* on the server's answer and never on a guess.
 */

import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { Button, Tag, theme } from '@/shared/ui';

import { rowEndOf, type AskedWhere } from '../domain/friendship';
import type { FriendRelation } from '../domain/vocabulary';
import { useAcceptFriendRequest, useAskToBeFriends, type Reread } from '../hooks/useFriendWrites';

import { FRIENDS_COPY, acceptLabel, addLabel } from './friendsCopy';
import { WriteNote } from './WriteNote';

const COPY = FRIENDS_COPY.members;

export interface RowWithFriendEndProps {
  /** The row as the surface draws it — its own press, its own words. */
  readonly children: ReactNode;
  readonly playerId: string;
  /** Their whole nickname, for the pill's spoken name. */
  readonly nickname: string;
  /** Where the reader stands with them, as the surface's read said it. */
  readonly relation: FriendRelation;
  /** The screen, its group and its sport — which the other person's Home card names. */
  readonly where: AskedWhere;
  /** The surface's own re-read, which a press awaits before it settles. */
  readonly reread: Reread;
}

export function RowWithFriendEnd({
  children,
  playerId,
  nickname,
  relation,
  where,
  reread,
}: RowWithFriendEndProps) {
  const asking = useAskToBeFriends(playerId, where, reread);
  const accepting = useAcceptFriendRequest(playerId, reread);
  const end = rowEndOf(relation);

  return (
    <View style={s.item} testID={`friend-row-${playerId}`}>
      <View style={s.line}>
        <View style={s.row}>{children}</View>
        {end.kind === 'tag' ? (
          // A tag stands at its own top-left (6.4); the box centres it on the row.
          <View>
            <Tag
              label={end.tag === 'sent' ? COPY.sent : COPY.friend}
              variant={end.tag === 'sent' ? 'warn' : 'ok'}
            />
          </View>
        ) : end.act === 'ask' ? (
          <Button
            label={COPY.add}
            accessibilityLabel={addLabel(nickname)}
            variant="dark"
            size="sm"
            shape="pill"
            busy={asking.isPending}
            busyLabel={COPY.asking}
            onPress={() => asking.mutate()}
          />
        ) : (
          <Button
            label={COPY.accept}
            accessibilityLabel={acceptLabel(nickname)}
            variant="dark"
            size="sm"
            shape="pill"
            busy={accepting.isPending}
            busyLabel={COPY.accepting}
            onPress={() => accepting.mutate()}
          />
        )}
      </View>
      <WriteNote writes={[asking, accepting]} />
    </View>
  );
}

const s = StyleSheet.create({
  item: { gap: theme.space.xs },
  line: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // The row takes what the end leaves it; the nickname inside it is what truncates.
  row: { flex: 1 },
});

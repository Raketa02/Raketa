/**
 * **The Friends page from You — three tabs** ([#754](https://github.com/Rakieta02/Rakieta/issues/754),
 * PRD #743 stories 34–37; the friends screens §4.1; Q4, Q41). Designed, no mock.
 *
 * ```
 * [ Friends | Asked you · 2 | You asked ]      the design system's segmented control (6.3)
 * ┌──────────────────────────────────────┐
 * │ face  ania.k                         │     Friends: by nickname, every sport and its Level
 * │       Padel 2,68                     │
 * │ face  ines.d               [Accept]  │     Asked you: Accept · You asked: Cancel
 * └──────────────────────────────────────┘
 * ```
 *
 * **The body of the page's one mode with tabs**: `FriendsPage` is the frame — the header, *+ Add
 * friends* and its sheet — and this is what it holds when opened from You. The picker a group's
 * Friends tab opens (#757) is the frame's other body.
 *
 * ## Only *Asked you* counts
 *
 * *Asked you · 2* while requests wait — set-aside ones too, since **Accept** still answers them (Q1)
 * — and *Asked you* alone at nought (the words §29.3). The count is in the label, as §29 writes it,
 * and spoken with it. *Friends* and *You asked* never count: nothing on them waits on the reader.
 *
 * ## Each list is the server's, in the server's order
 *
 * Friends by nickname (call 11), requests newest first, and nothing re-sorts them. A row is the
 * face, the whole nickname and, on *Friends*, every sport they play with its Level (*Padel 2,75 ·
 * Tennis 3,10*). **The rest of every row opens the record** (`onPerson`, the composer's — the
 * record is `player_record`'s, which draws this feature's button). **Accept** and **Cancel** sit
 * beside that press, never inside it, and act on the press: each moves towards somebody who still
 * answers, or takes back what they never saw, and a cancelled request can be asked again from their
 * Members row. **Each stays busy until its list has read again**, so the row leaves on the server's
 * answer; every friends write re-reads all three lists (`friendKeys`), so a tab not on screen is
 * right when it is opened.
 *
 * **Each tab has a one-line empty state** (the words §29.3), and a read that failed says why with
 * *Try again*, never an empty list.
 */

import { useState, type ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { Button, Card, Segment, theme } from '@/shared/ui';

import type { Friend, FriendRequest, FriendsTab } from '../domain/friendList';
import type { RequestDirection } from '../domain/vocabulary';
import { useFriendRequests, useFriends } from '../hooks/useFriendLists';
import { useAcceptFriendRequest, useCancelFriendRequest } from '../hooks/useFriendWrites';

import {
  FRIENDS_COPY,
  acceptLabel,
  askedYouTab,
  cancelRequestLabel,
  sportsLine,
} from './friendsCopy';
import { ListReading } from './ListReading';
import { PersonRow } from './PersonRow';
import { WriteNote, type WriteState } from './WriteNote';

const COPY = FRIENDS_COPY.page;

export interface FriendsTabsProps {
  /** A tap on the rest of a row: their record, the composer's to open. */
  readonly onPerson: (playerId: string) => void;
}

export function FriendsTabs({ onPerson }: FriendsTabsProps) {
  const [tab, setTab] = useState<FriendsTab>('friends');
  // Read whichever tab is open: the count is on *Asked you*'s name.
  const waiting = useFriendRequests('ASKED_YOU').data?.length ?? 0;

  return (
    <View style={s.body}>
      <Segment
        options={[
          { key: 'friends', label: COPY.tabs.friends },
          { key: 'ASKED_YOU', label: askedYouTab(waiting) },
          { key: 'YOU_ASKED', label: COPY.tabs.YOU_ASKED },
        ]}
        selected={tab}
        onSelect={setTab}
      />
      {tab === 'friends' ? (
        <FriendsList onPerson={onPerson} />
      ) : (
        <RequestsList direction={tab} onPerson={onPerson} />
      )}
    </View>
  );
}

function FriendsList({ onPerson }: FriendsTabsProps) {
  const read = useFriends();
  const friends = read.data;

  if (friends === undefined) return <ListReading read={read} reading={COPY.reading} />;
  if (friends.length === 0) return <Text style={s.quiet}>{COPY.empty.friends}</Text>;
  return (
    <Card style={s.rows}>
      {friends.map((friend, at) => (
        <FriendItem key={friend.playerId} friend={friend} divided={at > 0} onPerson={onPerson} />
      ))}
    </Card>
  );
}

function FriendItem({
  friend,
  divided,
  onPerson,
}: {
  readonly friend: Friend;
  readonly divided: boolean;
} & FriendsTabsProps) {
  return (
    <View testID={`friend-${friend.playerId}`} style={[s.entry, divided ? s.divided : undefined]}>
      <PersonRow
        testID={`friend-open-${friend.playerId}`}
        playerId={friend.playerId}
        nickname={friend.nickname}
        {...(friend.photoUrl === undefined ? {} : { photoUrl: friend.photoUrl })}
        line={sportsLine(
          friend.sports.map((one) => ({ name: sportLabel(one.sport), level: one.level })),
        )}
        onPress={() => onPerson(friend.playerId)}
      />
    </View>
  );
}

function RequestsList({
  direction,
  onPerson,
}: { readonly direction: RequestDirection } & FriendsTabsProps) {
  const read = useFriendRequests(direction);
  const requests = read.data;

  if (requests === undefined) return <ListReading read={read} reading={COPY.reading} />;
  if (requests.length === 0) return <Text style={s.quiet}>{COPY.empty[direction]}</Text>;
  const Item = direction === 'ASKED_YOU' ? AskedYouItem : YouAskedItem;
  return (
    <Card style={s.rows}>
      {requests.map((request, at) => (
        <Item
          key={request.playerId}
          request={request}
          divided={at > 0}
          reread={() => read.refetch()}
          onPerson={onPerson}
        />
      ))}
    </Card>
  );
}

interface RequestItemProps extends FriendsTabsProps {
  readonly request: FriendRequest;
  readonly divided: boolean;
  /** The tab's own list, read again — what a press awaits before it settles. */
  readonly reread: () => Promise<unknown>;
}

/** *Asked you*: **Accept**, the `dark` pill Members' own Accept is. */
function AskedYouItem(props: RequestItemProps) {
  const { request } = props;
  const accepting = useAcceptFriendRequest(request.playerId, props.reread);
  return (
    <RequestRow {...props} prefix="asked-you" write={accepting}>
      <Button
        label={COPY.accept}
        accessibilityLabel={acceptLabel(request.nickname)}
        variant="dark"
        size="sm"
        shape="pill"
        busy={accepting.isPending}
        busyLabel={COPY.accepting}
        onPress={() => accepting.mutate()}
      />
    </RequestRow>
  );
}

/** *You asked*: **Cancel**, the `secondary` pill — taking back, never the accent. */
function YouAskedItem(props: RequestItemProps) {
  const { request } = props;
  const cancelling = useCancelFriendRequest(request.playerId, props.reread);
  return (
    <RequestRow {...props} prefix="you-asked" write={cancelling}>
      <Button
        label={COPY.cancel}
        accessibilityLabel={cancelRequestLabel(request.nickname)}
        variant="secondary"
        size="sm"
        shape="pill"
        busy={cancelling.isPending}
        busyLabel={COPY.cancelling}
        onPress={() => cancelling.mutate()}
      />
    </RequestRow>
  );
}

/**
 * **A request's row** — the person, whose press opens the record, and the tab's one act beside it
 * (`children`), with the act's note under both. The testID's prefix tells the two tabs apart.
 */
function RequestRow({
  request,
  divided,
  onPerson,
  prefix,
  write,
  children,
}: RequestItemProps & {
  readonly prefix: string;
  readonly write: WriteState;
  readonly children: ReactNode;
}) {
  return (
    <View
      testID={`${prefix}-${request.playerId}`}
      style={[s.entry, divided ? s.divided : undefined]}
    >
      <View style={s.line}>
        <View style={s.person}>
          <PersonRow
            testID={`${prefix}-open-${request.playerId}`}
            playerId={request.playerId}
            nickname={request.nickname}
            {...(request.photoUrl === undefined ? {} : { photoUrl: request.photoUrl })}
            line=""
            onPress={() => onPerson(request.playerId)}
          />
        </View>
        {children}
      </View>
      <WriteNote writes={[write]} />
    </View>
  );
}

const s = StyleSheet.create({
  body: { gap: theme.space.sm },
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  // The rows carry their own padding, so the card's is a step smaller (the You tab's groups').
  rows: { paddingVertical: theme.space.xxs },
  entry: { gap: theme.space.xs, paddingVertical: theme.space.sm },
  // 5.5: the fold from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  line: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // The row takes what the button leaves it; the nickname inside it is what truncates.
  person: { flex: 1 },
});

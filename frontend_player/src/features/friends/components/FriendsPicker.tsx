/**
 * **The Friends page as a picker** — what it holds when a group's Friends court opens it
 * ([#757](https://github.com/Raketa02/Raketa/issues/757); the friends screens §4.2; friends 3, 6).
 *
 * ```
 * ┌──────────────────────────────────────┐
 * │ face  karol.t                    ( ) │   every friend, from every group
 * │       2,75 · established             │   the Level in the group's sport, its band
 * │ face  magda.p                    (✓) │   picked: the round box filled, a drawn tick
 * │ face  zofia.b                    ( ) │   greyed — no Level in this sport
 * │       No padel level yet             │
 * └──────────────────────────────────────┘
 * ```
 *
 * **The body of the page's second mode**: `FriendsPage` is the frame — the header, *+ Add friends*
 * and its sheet — and the composer pins **Done** under it. **No tabs.**
 *
 * - **Every friend, from every group**, in the server's order for the sport: **highest Level
 *   first**, the unrated last (call 4; `GET /friends?sport=`). Nothing re-sorts them.
 * - **The whole row is the tick** — a checkbox, its name the friend and their line. Picked rows
 *   wear the round box filled with a drawn tick (Archivo has no ✓), 6.11's inversion and shape.
 * - **Full** — three picked in doubles, one in singles — **the rest grey out** (friends 6) and
 *   cannot be picked until one is unpicked; a picked row never greys.
 * - **No Level in the sport**: greyed, *No padel level yet*. Its *Ask … to get a padel level* is
 *   #758's. One seated before they lost it can still be unpicked.
 * - **No friends at all**: the group's empty card (play 55), handed in, since it is `groups'`.
 *
 * **The picks are the composer's** (`picked`, `onToggle`): they become the court's seats on Done,
 * which is the group page's, and a list read again leaves them where they were.
 */

import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { sportInLine } from '@/features/onboarding/types';
import { Card, PlayerPhoto, Tick, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { levelIn, type Friend } from '../domain/friendList';
import { useFriendsIn } from '../hooks/useFriendLists';

import { FRIENDS_COPY, noLevelLine, pickerLine, pickerRowLabel } from './friendsCopy';
import { ListReading } from './ListReading';
import { ROW_FACE } from './PersonRow';

export interface FriendsPickerProps {
  readonly sport: Sport;
  /** Picked so far. */
  readonly picked: readonly string[];
  readonly onToggle: (playerId: string) => void;
  /** How many may be picked: the seats beside the reader — three in doubles, one in singles. */
  readonly seats: number;
  /** No friends yet: the group's empty card (play 55), the composer's. */
  readonly empty: ReactNode;
}

export function FriendsPicker({ sport, picked, onToggle, seats, empty }: FriendsPickerProps) {
  const read = useFriendsIn(sport);
  const friends = read.data;

  if (friends === undefined) {
    return <ListReading read={read} reading={FRIENDS_COPY.picker.reading} />;
  }
  if (friends.length === 0) return <>{empty}</>;

  const full = picked.length >= seats;
  return (
    <Card style={s.rows}>
      {friends.map((friend, at) => (
        <PickerRow
          key={friend.playerId}
          friend={friend}
          sport={sport}
          divided={at > 0}
          picked={picked.includes(friend.playerId)}
          full={full}
          onToggle={() => onToggle(friend.playerId)}
        />
      ))}
    </Card>
  );
}

function PickerRow({
  friend,
  sport,
  divided,
  picked,
  full,
  onToggle,
}: {
  readonly friend: Friend;
  readonly sport: Sport;
  readonly divided: boolean;
  readonly picked: boolean;
  readonly full: boolean;
  readonly onToggle: () => void;
}) {
  const rated = levelIn(friend, sport);
  const line =
    rated === undefined ? noLevelLine(sportInLine(sport)) : pickerLine(rated.level, rated.band);
  const fullHere = full && !picked;
  // A picked row is never shut: whoever is seated can always be unpicked, rated or not.
  const shut = !picked && (rated === undefined || fullHere);

  return (
    <Pressable
      testID={`pick-${friend.playerId}`}
      accessibilityRole="checkbox"
      accessibilityLabel={pickerRowLabel(friend.nickname, line, fullHere && rated !== undefined)}
      accessibilityState={{ checked: picked, disabled: shut }}
      disabled={shut}
      onPress={onToggle}
      hitSlop={theme.hit.peopleRow}
      style={({ pressed }) => [
        s.row,
        divided ? s.divided : undefined,
        pressed ? s.pressed : undefined,
      ]}
    >
      <View style={[s.person, shut ? s.shut : undefined]}>
        <PlayerPhoto
          playerId={friend.playerId}
          {...(friend.photoUrl === undefined ? {} : { photoUrl: friend.photoUrl })}
          box={{ kind: 'face', size: ROW_FACE }}
        />
        <View style={s.words}>
          <Text style={s.name} numberOfLines={1}>
            {friend.nickname}
          </Text>
          <Text style={s.line} numberOfLines={1}>
            {line}
          </Text>
        </View>
      </View>
      <View style={[s.circle, picked ? s.circlePicked : undefined, shut ? s.shut : undefined]}>
        {picked ? <Tick /> : null}
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  // The rows carry their own padding, so the card's is a step smaller — You › Friends' own.
  rows: { paddingVertical: theme.space.xxs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
  },
  // 5.5: the fold from the second row on.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  pressed: { opacity: 0.7 },
  // Greyed, as friends 6 draws the rows a full court leaves: the person and the circle, never the
  // row's own press feedback.
  shut: { opacity: 0.4 },
  person: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  // Mono whole, as Members' line is: the Level is a figure.
  line: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  // 6.11's box, round — the mocks' circle — and its inversion when picked.
  circle: {
    width: theme.size.tickBox.box,
    height: theme.size.tickBox.box,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  circlePicked: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
});

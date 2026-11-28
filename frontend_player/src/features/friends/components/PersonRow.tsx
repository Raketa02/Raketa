/**
 * **A person's row** — the face, the whole nickname and a line under it, the whole row one press
 * that opens their record ([#754](https://github.com/Rakieta02/Rakieta/issues/754)).
 *
 * ```
 * ┌────┐ magda.p
 * │face│ • Padel 2,66          ← the sport's dot only where the row is about one sport
 * └────┘
 * ```
 *
 * **Members' row, drawn by this feature**: You › Friends' three tabs and the result screen's PLAYED
 * WITH list people as Members does (the screens §3, §4.1), and Members' row is `groups'`, which
 * draws this feature's pills — the other way round would be a dependency both ways. So the same
 * parts at the same sizes: 7.19's 38pt face, `cardTitle` for the name, the line mono whole (the
 * Level is a figure), and the sport's round dot before it. **No reliability chip**: neither read
 * carries the points Members' does.
 *
 * The pill or the button on the right is a **sibling** of this press, never inside it — the caller
 * draws it beside (`RowWithFriendEnd`, a request row's end) — so a tap on the face or the name opens
 * the record and only the pill acts.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { sportColour } from '@/features/onboarding/types';
import { PlayerPhoto, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { FRIENDS_COPY, personRowLabel } from './friendsCopy';

/**
 * 7.19's people-list face — this feature's one spelling of it, which Home's request cards read too;
 * `groups`' and `blocks`' lists spell their own. Kept out of `theme.ts` by #338 §5 until a change
 * about faces decides its home.
 */
export const ROW_FACE = 38;

export interface PersonRowProps {
  readonly testID: string;
  readonly playerId: string;
  readonly nickname: string;
  /** Omitted when they have no photograph: the face draws their poster. */
  readonly photoUrl?: string;
  /** Under the name — *Padel 2,66*, *Padel 2,60 · Tennis 3,10* — or nothing where it is empty. */
  readonly line: string;
  /** The sport the line is about, whose dot leads it; absent where the line names several. */
  readonly sport?: Sport;
  readonly onPress: () => void;
}

export function PersonRow({
  testID,
  playerId,
  nickname,
  photoUrl,
  line,
  sport,
  onPress,
}: PersonRowProps) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={personRowLabel(nickname, line)}
      accessibilityHint={FRIENDS_COPY.page.openRecord}
      onPress={onPress}
      hitSlop={theme.hit.peopleRow}
      // 6.6: the row is the target, so the row dims.
      style={({ pressed }) => [s.row, pressed ? s.pressed : undefined]}
    >
      <PlayerPhoto
        playerId={playerId}
        {...(photoUrl === undefined ? {} : { photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />
      <View style={s.words}>
        <Text style={s.name} numberOfLines={1}>
          {nickname}
        </Text>
        {line === '' ? null : (
          <View style={s.lineRow}>
            {sport === undefined ? null : (
              <View
                style={[s.dot, { backgroundColor: sportColour(sport) }]}
                accessibilityElementsHidden
                importantForAccessibility="no"
              />
            )}
            <Text style={s.line} numberOfLines={1}>
              {line}
            </Text>
          </View>
        )}
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  lineRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  // Mono whole, as Members' line is: the Level is a figure.
  line: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted, flexShrink: 1 },
});

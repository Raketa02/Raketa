/**
 * **A Fill in row's frame** — the two rows' shared drawing (the screens A3; mocks 11–13,
 * [#557](https://github.com/Raketa02/Raketa/issues/557)): a surface card framed 1.5pt in the row's
 * colour, the upper block — the title over the club and the bold *when* — as one door to the game's
 * details, and the foot under it, the squares left and the act right.
 *
 * *Seats to fill* is framed in `coral` and *You're In* in `mint`: a rescue is the group's one
 * emergency, the rescue ribbon's meaning (§1.2), and a yes standing is settled (1.3).
 */

import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { LINE_JOIN } from './deckPresentation';
import { FILL_IN_COPY } from './fillInCopy';

export interface FillInRowProps {
  readonly frame: 'rescue' | 'yours';
  /** The upper block, spoken — the game, the club, the *when*. */
  readonly label: string;
  readonly title: string;
  readonly club: string;
  /** *fills by Fri 16:00* · *book by Sat 13:00*, drawn bold. */
  readonly when: string;
  readonly onOpen: () => void;
  /** The squares, and the row's act. */
  readonly children: ReactNode;
  readonly testID: string;
}

export function FillInRow({
  frame,
  label,
  title,
  club,
  when,
  onOpen,
  children,
  testID,
}: FillInRowProps) {
  return (
    <View style={[s.row, FRAME[frame]]} testID={testID}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityHint={FILL_IN_COPY.rowHint}
        onPress={onOpen}
        style={({ pressed }) => [s.head, pressed ? s.pressed : undefined]}
      >
        <Text style={s.title}>{title}</Text>
        <Text style={s.sub}>
          {club}
          {LINE_JOIN}
          <Text style={s.when}>{when}</Text>
        </Text>
      </Pressable>
      <View style={s.foot}>{children}</View>
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: theme.size.fillInRow.stroke,
    padding: theme.space.md,
    gap: theme.space.md,
  },
  head: { gap: theme.space.xxs },
  title: { ...theme.type.h2, color: theme.color.ink },
  sub: { ...theme.type.rlLabel, color: theme.color.muted },
  when: { ...theme.type.rlValue, color: theme.color.ink },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: theme.space.sm,
  },
  // 6.6: the block is the target, so it dims.
  pressed: { opacity: 0.7 },
});

const FRAME = StyleSheet.create({
  rescue: { borderColor: theme.color.coral },
  yours: { borderColor: theme.color.mint },
});

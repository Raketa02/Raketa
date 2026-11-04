/**
 * **A club in a search's answer, drawn as a card of its own** — New group's home-club search and
 * Join a group's search both draw it (the 2026-09-27 mocks, and the review that carried them to
 * Join a group).
 *
 * **Lifted off the page** (`shadow.clubResult`, design-system 4.3). A club and the groups under it
 * are one object and the list is long; a divider between rows could not say where one club's
 * groups end and the next club begins, and a card with its own shadow does.
 *
 * Two parts. **The head** is the club's name over *district · distance · sports*, on white — in
 * New group the one tap that chooses it, with a *Set as home* pill beside it (and in the player
 * profile's *Pick a club near where you play*, with a *Pick* pill, #733); in Join a group
 * context, spoken whole with no button role, because nothing happens when it is touched (story
 * 39). **The band** under it, a step down on `paper3` to the card's edges, holds what is at the
 * club — its groups, or Join a group's sentence that it has none.
 */

import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { SearchedClub } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import { clubLine } from './groupsPresentation';

/** How a test finds the band a club's contents sit on, to read its ground. */
export const CLUB_CARD_TRAY_TEST_ID = 'club-card-tray';

export interface ClubCardProps {
  readonly club: SearchedClub;
  /** The head, spoken — whole, as the one element it is. */
  readonly headLabel: string;
  /**
   * New group's *Set as home*: the head becomes the one tap, with the pill beside it. Absent in
   * Join a group, where the head is context.
   */
  readonly onChoose?: () => void;
  /** The pill's word beside a head that chooses — *Set as home* unless the caller says. */
  readonly chooseWord?: string;
  /** What sits on the band under the head. Absent — or `null` — draws no band. */
  readonly children?: ReactNode;
  readonly testID?: string;
}

export function ClubCard({
  club,
  headLabel,
  onChoose,
  chooseWord = GROUPS_COPY.newGroup.setAsHome,
  children,
  testID,
}: ClubCardProps) {
  const words = (
    <View style={s.words}>
      <Text style={s.name} numberOfLines={1}>
        {club.name}
      </Text>
      <Text style={s.line} numberOfLines={1}>
        {clubLine(club)}
      </Text>
    </View>
  );

  return (
    // Two boxes because iOS clips a shadow to `overflow: hidden`: the outer one casts it, the
    // inner one rounds the band into the card's corners.
    <View testID={testID} style={s.card}>
      <View style={s.inside}>
        {onChoose === undefined ? (
          <View style={s.head} accessible accessibilityLabel={headLabel}>
            {words}
          </View>
        ) : (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={headLabel}
            onPress={onChoose}
            style={({ pressed }) => [s.head, pressed ? s.pressed : undefined]}
          >
            {words}
            {/* Drawn as a chip and not one: the whole head is the tap, as it always was, so the
                pill is where the finger is invited rather than a second control inside the first. */}
            <View style={s.pill}>
              <Text style={s.pillWord}>{chooseWord}</Text>
            </View>
          </Pressable>
        )}

        {children === undefined || children === null ? null : (
          <View testID={CLUB_CARD_TRAY_TEST_ID} style={s.band}>
            {children}
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    ...theme.shadow.clubResult,
  },
  inside: {
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    overflow: 'hidden',
  },
  head: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    padding: theme.space.md,
    minHeight: theme.size.minTouch,
  },
  pressed: { opacity: 0.7 },
  words: { flex: 1, gap: theme.space.xxs },
  name: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  // 6.2's unselected chip, drawn: the same pill, border, ground and label.
  pill: {
    minHeight: theme.size.chip,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xxs,
    borderRadius: theme.radius.pill,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    justifyContent: 'center',
  },
  pillWord: { ...theme.type.chip, color: theme.color.ink },
  // The club's contents sit a step down from the head they belong to, to the card's edges — on
  // `paper3`, deep enough to be told from the page at the card's bottom edge, where `paper2` was
  // not (#529). Text on it is `muted2`, never `muted`.
  band: {
    backgroundColor: theme.color.paper3,
    padding: theme.space.md,
    gap: theme.space.md,
  },
});

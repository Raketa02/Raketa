/**
 * **A Same vibe tile** ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows screens
 * §6.2, §6.4; the words §31.8; home rows 20, 22–22.3, 24; design-system 7.35) — `shared/ui`'s tinted
 * pale tile, washed in their court poster's hue, with:
 *
 * ```
 * ┌────────────────────────────────────┐
 * │ [face]  karol.t               (98%) │  the face, the nickname, the vibe % in a white circle
 * │         6 things in common          │
 * │ [Stays for a drink] [Plays to win]  │  the tags they share, green, as many whole as fit in
 * │ [Here to improve]  [+2 more]        │  three lines — the last place +N more (`SharedTags`)
 * │                                (✓)  │  the round friend button, bottom-right
 * └────────────────────────────────────┘
 * ```
 *
 * **Two doors**: the round button acts, asking from *same vibe*; a tap anywhere else opens the vibe
 * sheet (`onOpen`). The face is not a door of its own here — the sheet's is.
 *
 * Home's row hands the rail's width and draws the row's sizes; See all hands its column and draws the
 * grid's (`theme.size.sameVibe`).
 */

import { StyleSheet, Text, View } from 'react-native';

import { RoundFriendButton } from '@/features/friends/types';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { PlayerPhoto, TintedTile, theme } from '@/shared/ui';
import { thingsInCommon } from '@/shared/vocabulary/socialTagPresentation';

import { FOUND_THROUGH_TAGS, type SameVibePlayer } from '../domain/sameVibe';

import { vibeTileLabel } from './discoveryCopy';
import { SharedTags } from './SharedTags';

export interface SameVibeTileProps {
  readonly player: SameVibePlayer;
  /** Home's row or See all's grid — the width handed in, and the face's and the circle's sizes. */
  readonly layout: 'row' | 'grid';
  readonly width: number;
  /** Anywhere but the button: the vibe sheet. */
  readonly onOpen: () => void;
}

export function SameVibeTile({ player, layout, width, onOpen }: SameVibeTileProps) {
  const face = theme.size.sameVibe.face[layout];
  const circle = theme.size.sameVibe.percent[layout];

  return (
    <TintedTile
      playerId={player.playerId}
      accessibilityLabel={vibeTileLabel(player)}
      onPress={onOpen}
      width={width}
      testID={`same-vibe-${player.playerId}`}
      corner={
        <RoundFriendButton
          playerId={player.playerId}
          nickname={player.nickname}
          relation={player.relation}
          where={FOUND_THROUGH_TAGS}
        />
      }
    >
      <View style={s.head}>
        <PlayerPhoto
          playerId={player.playerId}
          {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
          box={{ kind: 'face', size: face }}
        />
        <View style={s.who}>
          <View style={s.nameLine}>
            <Text style={s.name} numberOfLines={1}>
              {player.nickname}
            </Text>
            <View style={[s.circle, { width: circle, height: circle }]}>
              <Text style={s.percent} numberOfLines={1}>
                {formatPercent(player.vibePercent)}
              </Text>
            </View>
          </View>
          <Text style={s.inCommon} numberOfLines={1}>
            {thingsInCommon(player.inCommon)}
          </Text>
        </View>
      </View>
      <SharedTags tags={player.sharedTags} />
    </TintedTile>
  );
}

const s = StyleSheet.create({
  head: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.space.sm,
    marginBottom: theme.space.sm,
  },
  who: { flex: 1 },
  // The nickname takes the line, and the circle stands at its end; the count runs under both.
  nameLine: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  name: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  // The vibe % in a white circle, on the tint (home rows 22).
  circle: {
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  percent: {
    ...theme.num.tiny,
    ...theme.tabular,
    fontFamily: theme.font.mono[600],
    color: theme.color.ink,
  },
  inCommon: { ...theme.type.rlLabel, color: theme.color.muted },
});

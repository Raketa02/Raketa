/**
 * **A New in Raketa tile** ([#801](https://github.com/Raketa02/Raketa/issues/801); the Home rows
 * screens §5.2–§5.3; home rows 17–19; design-system 7.31) — `shared/ui`'s portrait tile, with:
 *
 * - **a volt *NEW*** top-left, and **`friends`' round button** top-right, asking from *new players*;
 * - over the wash: the nickname, bold; **every sport they hold a level in**, its dot and level in mono
 *   — one to a line on Home's row, as many to a line as fit in See all's columns (home rows 18, 19);
 *   and *Joined 2 days ago*. **A player with no level has no sport lines** (designed, no mock).
 *
 * A tap anywhere but the button opens the record (`onOpen`). The tile's spoken name reads it in the
 * order drawn (`tileLabel`).
 */

import { StyleSheet, Text, View } from 'react-native';

import { RoundFriendButton } from '@/features/friends/types';
import { PortraitTile, Tag, theme } from '@/shared/ui';

import { FOUND_AMONG_NEW_PLAYERS, joinedAgo, type Joiner } from '../domain/joiner';

import { DISCOVERY_COPY, joinedLine, sportLevelLine, tileLabel } from './discoveryCopy';

export interface JoinerTileProps {
  readonly joiner: Joiner;
  readonly width: number;
  /** Home's row: 11:8 and a sport to a line; See all: 9:8 and as many as fit. */
  readonly layout: 'row' | 'grid';
  readonly onOpen: () => void;
}

export function JoinerTile({ joiner, width, layout, onOpen }: JoinerTileProps) {
  const joined = joinedLine(joinedAgo(joiner.daysSinceJoined));
  const aspect =
    layout === 'row' ? theme.size.portraitTile.railAspect : theme.size.portraitTile.gridAspect;

  return (
    <PortraitTile
      playerId={joiner.playerId}
      {...(joiner.photoUrl === undefined ? {} : { photoUrl: joiner.photoUrl })}
      width={width}
      aspect={aspect}
      accessibilityLabel={tileLabel(joiner, joined)}
      onPress={onOpen}
      tag={<Tag label={DISCOVERY_COPY.newInRaketa.tag} variant="volt" />}
      corner={
        <RoundFriendButton
          playerId={joiner.playerId}
          nickname={joiner.nickname}
          relation={joiner.relation}
          where={FOUND_AMONG_NEW_PLAYERS}
        />
      }
      testID={`joiner-${joiner.playerId}`}
    >
      <Text style={s.name} numberOfLines={1}>
        {joiner.nickname}
      </Text>
      {joiner.sports.length === 0 ? null : (
        <View style={layout === 'row' ? s.sportsOnePerLine : s.sportsAsTheyFit}>
          {joiner.sports.map((held) => (
            <View key={held.sport} style={s.sport} testID={`joiner-sport-${held.sport}`}>
              <View style={[s.dot, { backgroundColor: theme.sport[held.sport] }]} />
              <Text style={s.level} numberOfLines={1}>
                {sportLevelLine(held.sport, held.level)}
              </Text>
            </View>
          ))}
        </View>
      )}
      <Text style={s.joined} numberOfLines={1}>
        {joined}
      </Text>
    </PortraitTile>
  );
}

const s = StyleSheet.create({
  // Over the wash, as on a dark card — every label with the on-media shadow (7.31).
  name: { ...theme.type.h2, color: theme.color.surface, ...theme.shadow.textOnMedia },
  sportsOnePerLine: { gap: 0 },
  // Two to a line where they fit (home rows 19): a sport that does not fit starts the next line.
  sportsAsTheyFit: { flexDirection: 'row', flexWrap: 'wrap', columnGap: theme.space.sm },
  sport: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  level: {
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.surface,
    ...theme.shadow.textOnMedia,
  },
  joined: { ...theme.type.tiny, color: theme.color.onDarkTiny, ...theme.shadow.textOnMedia },
});

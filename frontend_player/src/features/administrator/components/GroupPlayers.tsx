/**
 * **The players** — how many, and who, newest first (club 11, 18, 19; PRD #500 story 130).
 *
 * - **The players card** — up to five stacked faces, the newest first, *+N* for everybody else, and
 *   *N players*; under it who gets in and how much of the WhatsApp group has arrived (club 11:
 *   *anyone with the link joins · 0% of the WhatsApp group*). One element, and it opens nothing.
 * - **The list** — every player, **newest joined first**, with the day they joined: *this week*
 *   within seven days, otherwise *7 Sep* (`joinedWhen`), in mono because it is a date. **Rows are
 *   not tappable and nobody can be removed** (PRD #500: nobody removes a Group member).
 *
 * *N players* is the group's member count, which a block does not change; the rows are the players
 * the server may show this reader, a blocked pair left out. So *+N* counts from the count, not from
 * the rows (`playersStack`). The stack is Info's members row's own drawing (`groups`' `FaceStack`).
 * With nobody in yet the list is not drawn — the card's *0 players* is the whole of it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { FaceStack, personName, ROW_FACE } from '@/features/groups/types';
import { Card, PlayerPhoto, theme } from '@/shared/ui';

import type { GroupPlayer, OfficialGroup } from '../domain/officialGroup';
import { joinedWhen, playersStack, whatsAppShare } from '../domain/officialGroupRules';

import {
  joinedLabel,
  playerRowLabel,
  playersCardLabel,
  playersCardLine,
  playersLine,
} from './administratorPresentation';

export interface GroupPlayersProps {
  readonly group: Pick<OfficialGroup, 'memberCount' | 'joinPolicy' | 'whatsAppSize' | 'players'>;
  /** When the group was read — every row's *this week* is judged against the same moment. */
  readonly readAt: number;
}

export function GroupPlayers({ group, readAt }: GroupPlayersProps) {
  const stack = playersStack(group.players, group.memberCount);
  const count = playersLine(group.memberCount);
  const line = playersCardLine(group, whatsAppShare(group.memberCount, group.whatsAppSize));

  return (
    <>
      <Card style={s.summary}>
        <View style={s.words} accessible accessibilityLabel={playersCardLabel(count, line)}>
          <View style={s.headline}>
            {stack.faces.length > 0 ? (
              <FaceStack faces={stack.faces} more={stack.more} testIDPrefix="players-face-" />
            ) : null}
            <Text style={s.count}>{count}</Text>
          </View>
          <Text style={s.line}>{line}</Text>
        </View>
      </Card>

      {group.players.length > 0 ? (
        <Card style={s.list}>
          {group.players.map((player, at) => (
            <PlayerRow key={player.playerId} player={player} readAt={readAt} divided={at > 0} />
          ))}
        </Card>
      ) : null}
    </>
  );
}

function PlayerRow({
  player,
  readAt,
  divided,
}: {
  readonly player: GroupPlayer;
  readonly readAt: number;
  readonly divided: boolean;
}) {
  const when = joinedWhen(player.joinedAt, readAt);

  return (
    <View
      testID={`player-${player.playerId}`}
      accessible
      accessibilityLabel={playerRowLabel(player.name, when)}
      style={[s.row, divided ? s.divided : undefined]}
    >
      <PlayerPhoto
        playerId={player.playerId}
        {...(player.photoUrl === undefined ? {} : { photoUrl: player.photoUrl })}
        box={{ kind: 'face', size: ROW_FACE }}
      />
      <Text style={s.name} numberOfLines={1}>
        {personName(player.name)}
      </Text>
      {when === undefined ? null : <Text style={s.joined}>{joinedLabel(when)}</Text>}
    </View>
  );
}

const s = StyleSheet.create({
  summary: { gap: theme.space.xs },
  words: { gap: theme.space.xxs },
  headline: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  count: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  list: { gap: theme.space.sm },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // 5.3: `line2` folds one card into rows.
  divided: {
    borderTopWidth: 1,
    borderTopColor: theme.color.line2,
    paddingTop: theme.space.sm,
  },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flex: 1 },
  // A date is a figure: mono and tabular (1.4), in `muted` as club 18 draws it.
  joined: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
});

/**
 * **The two cards New group and Edit group share** — the Name and *Who can join* (play 5, 12;
 * [#514](https://github.com/Raketa02/Raketa/issues/514): Edit group is *the New group form's Name
 * and Who can join cards*). One drawing, so the two forms cannot drift apart; each screen holds its
 * own state and hands it in.
 *
 * The name field stops at 40 characters (`GROUP_NAME_MAX`) — the server trims and counts again.
 * *Who can join* is two chips, *Anyone* first, with the note that there is no sport to pick.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, Chip, TextField, theme } from '@/shared/ui';

import { GROUP_NAME_MAX } from '../domain/group';
import type { JoinPolicy } from '../domain/vocabulary';

import { GROUPS_COPY } from './groupsCopy';

const COPY = GROUPS_COPY.newGroup;

export function GroupNameCard({
  name,
  onName,
}: {
  readonly name: string;
  readonly onName: (name: string) => void;
}) {
  return (
    <Card style={s.card}>
      <TextField
        label={COPY.name}
        recessed
        placeholder={COPY.namePlaceholder}
        value={name}
        onChangeText={onName}
        maxLength={GROUP_NAME_MAX}
        autoCapitalize="sentences"
        returnKeyType="next"
      />
    </Card>
  );
}

export function WhoCanJoinCard({
  joinPolicy,
  onJoinPolicy,
}: {
  readonly joinPolicy: JoinPolicy;
  readonly onJoinPolicy: (policy: JoinPolicy) => void;
}) {
  return (
    <Card style={s.card}>
      <Text style={s.label}>{COPY.whoCanJoin}</Text>
      <View style={s.chips}>
        <Chip
          label={COPY.anyone}
          selected={joinPolicy === 'ANYONE'}
          onPress={() => onJoinPolicy('ANYONE')}
        />
        <Chip
          label={COPY.peopleIApprove}
          selected={joinPolicy === 'PEOPLE_I_APPROVE'}
          onPress={() => onJoinPolicy('PEOPLE_I_APPROVE')}
        />
      </View>
      <Text style={s.note}>{COPY.noSportNote}</Text>
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  chips: { flexDirection: 'row', gap: theme.space.xs },
  note: { ...theme.type.tiny, color: theme.color.muted },
});

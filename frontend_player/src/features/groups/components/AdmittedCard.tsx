/**
 * ***LET IN · 2*** — who a switch to *Anyone* admitted, in the order they asked: everybody waiting
 * is in at once, and the save's answer says who, as a card under the button — a face and a name
 * each, and it stays until the next save.
 *
 * Edit group's (story 76, [#514](https://github.com/Rakieta02/Rakieta/issues/514)), and an official
 * group's settings' ([#517](https://github.com/Rakieta02/Rakieta/issues/517)), where the same switch
 * does the same thing: one drawing, lent to the administrator through `types.ts`.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Card, PlayerPhoto, theme } from '@/shared/ui';

import type { GroupPerson } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import { admittedEyebrow, personName } from './groupsPresentation';
import { ROW_FACE } from './peopleRow';

export function AdmittedCard({ people }: { readonly people: readonly GroupPerson[] }) {
  return (
    <View style={s.section}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {admittedEyebrow(people.length)}
      </Text>
      <Card style={s.card}>
        <Text style={s.line}>{GROUPS_COPY.editGroup.admittedLine}</Text>
        {people.map((person) => (
          <View
            key={person.playerId}
            testID={`admitted-${person.playerId}`}
            style={s.row}
            accessible
            accessibilityLabel={personName(person.name)}
          >
            <PlayerPhoto
              playerId={person.playerId}
              {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
              box={{ kind: 'face', size: ROW_FACE }}
            />
            <Text style={s.name} numberOfLines={1}>
              {personName(person.name)}
            </Text>
          </View>
        ))}
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  card: { gap: theme.space.sm },
  line: { ...theme.type.tiny, color: theme.color.muted },
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  name: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
});

/**
 * **The other players' faces, overlapping, up to three** (details 7) — the details' top bar draws
 * them before the names, and a Home card beside its facts (#556). Decorative: the title, or the
 * card's spoken name, says who they are.
 */

import { StyleSheet, View } from 'react-native';

import { PlayerPhoto, theme } from '@/shared/ui';

import type { DeckPerson } from '../domain/deck';

/** How many of the other players' faces overlap (details 7). */
const FACES = 3;

export interface OthersFacesProps {
  /** Everybody on the game — the reader among them, who is left out. */
  readonly people: readonly DeckPerson[];
}

export function OthersFaces({ people }: OthersFacesProps) {
  const others = people.filter((person) => !person.isYou).slice(0, FACES);
  return (
    <View
      style={s.faces}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {others.map((person, at) => (
        <View key={person.playerId} style={at > 0 ? s.overlap : undefined}>
          <PlayerPhoto
            playerId={person.playerId}
            {...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl })}
            box={{ kind: 'face', size: theme.size.groupPage.stackFace }}
          />
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  faces: { flexDirection: 'row' },
  overlap: { marginLeft: -theme.size.groupPage.stackOverlap },
});

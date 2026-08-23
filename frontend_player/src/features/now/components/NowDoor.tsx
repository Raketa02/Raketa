/**
 * The door into a sport's questionnaire, where that sport's shelves would be.
 *
 * `ADR-0084` closes the sport bar's one open cost with a **destination rather
 * than a better sentence**: three of five chips lie to a one-sport player until
 * she taps one, and *"the door is not a follow-up to the fixed row, it is the
 * condition on it."*
 *
 * **Full width, not a rail.** Every other block on this screen is a horizontal
 * row of cards; this one is a single ask, and putting it in a scroller would let
 * it sit half off the edge of the screen it is the whole point of.
 *
 * **It draws nothing for a code it cannot word.** A door whose sentence is blank
 * and whose button says nothing is worse than the row being missing, and the
 * missing row is exactly what an old build gets — which is what `ADR-0084`
 * accepts when it puts the door *in* the list.
 *
 * **The two light shelves are below it and that is the argument**, not a
 * leftover: *New on Raketa* and *New clubs* are index queries with no scorer, so
 * they still find squash players and squash clubs. She sees there are squash
 * clubs here before spending two minutes.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, theme } from '@/shared/ui';

import type { Door } from '../domain/ComposedScreen';

import { GUTTER } from './nowGeometry';

export const DOOR_ID = 'now-door';

export interface DoorViewProps {
  readonly door: Door;
  /** Opens this sport's questionnaire. Which sport is the chip the screen holds. */
  readonly onEnter: () => void;
}

export function DoorView({ door, onEnter }: DoorViewProps) {
  if (door.copy === undefined) return null;

  return (
    <View testID={DOOR_ID} style={s.block}>
      <Card style={s.card}>
        <Text style={s.line}>{door.copy.line}</Text>
        <Button label={door.copy.action} onPress={onEnter} />
      </Card>
    </View>
  );
}

const s = StyleSheet.create({
  block: { paddingHorizontal: GUTTER, marginBottom: theme.space.xl },
  card: { gap: theme.space.sm },
  line: { ...theme.type.tiny, color: theme.color.ink },
});

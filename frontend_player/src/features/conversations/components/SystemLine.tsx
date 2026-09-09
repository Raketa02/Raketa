/**
 * **One thing that happened**, told by a context that does not know this one exists.
 *
 * The stream's second component, and the reason it is a second one is `Bubble`'s module note.
 * What it draws is **type and not an element** (#338 §7): `tiny` in `muted`, centred, full width,
 * with no ground, no border and no token of its own. A system line is not a message somebody sent
 * and must not look like one — *nobody typed **Tomek set the day***.
 *
 * The sentence is `conversationPresentation.ts`', keyed by code, with `{name}` filled from the
 * members the room already holds and never from `values` — *so a corrected handle fixes the whole
 * backlog*. A code this build cannot read, and a code whose values it cannot read, both draw the
 * same named gap, because a system line **is** the whole of the slot it is drawn in.
 */

import { StyleSheet, Text } from 'react-native';

import { theme } from '@/shared/ui';

export interface SystemLineProps {
  /** The rendered sentence, which already names its own actor. */
  readonly sentence: string;
}

export function SystemLine({ sentence }: SystemLineProps) {
  // One element per entry, and the sentence is its whole name: there is nothing here a listener
  // gets that a reader does not.
  return (
    <Text accessible style={s.line}>
      {sentence}
    </Text>
  );
}

const s = StyleSheet.create({
  line: {
    ...theme.type.tiny,
    color: theme.color.muted,
    textAlign: 'center',
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xs,
  },
});

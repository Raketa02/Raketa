/**
 * **One line that grows to a cap, and Send.**
 *
 * The field is 6.13's, which arrived with this surface — *"two more surfaces need a field, and a
 * third implementation is exactly the drift a shared primitive exists to prevent"*. What this
 * component owns is the strip: the cap, the one control beside it, and when that control is open.
 *
 * ## The label is spoken and not drawn
 *
 * `labelHidden`, which is the prop 6.13 said would arrive with the surface that needed one. A box
 * under a header naming the people and the sport, with `Send` beside it, does not need `MESSAGE`
 * over it — and a listener, who has none of that around them, still gets the name (§24.4).
 *
 * ## Nothing here caps the text, and that is the contract rather than an oversight
 *
 * The message length cap is **deliberately not on the wire**: an over-long message is a refusal
 * the conversation context owns and names, not a `422` about a field. So this client cannot know
 * the number, and a `maxLength` picked to match it would silently truncate a paste — *a shortened
 * message is one the sender believes they sent whole, in front of other people*. What is refused
 * comes back as a code, and the sentence for it is `conversationErrorMessage`'s.
 *
 * **Send is closed on an empty box and on nothing else.** Whitespace-only is empty, which is the
 * server's own trim read one step early — the one refusal this client can prevent without
 * guessing at a number it was not told.
 *
 * ## The strip is not a screen action
 *
 * It is `paper` rather than 10.1's pinned CTA slot: the composer is part of the room, sitting
 * under the stream and above the tab bar, and a control tray around it would draw a second
 * bounded surface on a screen whose whole content is already bounded blocks.
 */

import { StyleSheet, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import { COMPOSER_LABEL, SEND } from './conversationPresentation';

/**
 * How far the box may grow before it scrolls, in lines.
 *
 * 6.13 hands the ceiling to the caller because *"a number is written only for what a device
 * drew"*, and what this one is written against is the strip's own job: at `type.rlValue`'s 16pt
 * line, five lines plus the box's padding is 106pt — under a fifth of the shortest stream this
 * app draws with a keyboard up, so a long message never eats the conversation it is a reply to.
 * Past that it scrolls, which is the shape a message being written in a room wants rather than a
 * page that grows.
 */
const COMPOSER_LINES = 5;

export interface ComposerProps {
  readonly text: string;
  readonly onChange: (text: string) => void;
  readonly onSend: () => void;
}

export function Composer({ text, onChange, onSend }: ComposerProps) {
  return (
    <View style={s.strip}>
      <View style={s.field}>
        <TextField
          label={COMPOSER_LABEL}
          labelHidden
          growTo={COMPOSER_LINES}
          value={text}
          onChangeText={onChange}
        />
      </View>

      <Button label={SEND} disabled={text.trim() === ''} onPress={onSend} />
    </View>
  );
}

const s = StyleSheet.create({
  strip: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.sm,
  },
  field: { flex: 1 },
});

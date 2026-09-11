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
 * **Send is closed on an empty box and on nothing else**, and the rule is `mayPost`'s rather
 * than this file's: the control that closes and the act that refuses are two readers of one
 * question, and two copies of it is how one stops agreeing with the other.
 *
 * ## The one other thing that closes it is the account, and it greys the box as well
 *
 * A **held** account may read here and may not write (ADR-0148 §9), so both halves of the strip
 * refuse and the field is greyed rather than merely `editable={false}` — the busy shape would say
 * *waiting* about something that is not going to happen. It is only acceptable because the note
 * above it has already said why, which is the condition 6.13's amendment attaches to the prop and
 * the whole of why the screen puts the note above this strip rather than beside the control.
 *
 * **Not live does not close it.** Sends are ordinary authenticated `POST`s over a channel that is
 * unidirectional by construction, so writing is unaffected — and disabling the composer would
 * state something false about the half that still works (§3.6).
 *
 * ## The strip is not a screen action, and there is no bar under it
 *
 * It is `paper` rather than 10.1's pinned CTA slot: the composer is part of the room, sitting
 * under the stream, and a control tray around it would draw a second bounded surface on a screen
 * whose whole content is already bounded blocks. **It is the last thing on the screen**: the tab
 * bar stands down inside a conversation so the keyboard and the stream get the whole of it
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)), and the bottom safe-area inset the bar
 * owns everywhere else is taken by the room's own frame, under this strip — not in it, because a
 * padding here would be counted a second time the moment the keyboard is up. `ConversationScreen`
 * carries that arithmetic.
 */

import { StyleSheet, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import { mayPost } from '../domain/stream';

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
  /** The account may not write here. Both halves refuse, and the screen owns the note. */
  readonly refused?: boolean;
}

export function Composer({ text, onChange, onSend, refused = false }: ComposerProps) {
  return (
    <View style={s.strip}>
      <View style={s.field}>
        <TextField
          label={COMPOSER_LABEL}
          labelHidden
          growTo={COMPOSER_LINES}
          value={text}
          onChangeText={onChange}
          disabled={refused}
        />
      </View>

      <Button label={SEND} disabled={refused || !mayPost(text)} onPress={onSend} />
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

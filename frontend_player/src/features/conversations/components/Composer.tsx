/**
 * **The composer: the field and Send** ([#402](https://github.com/Raketa02/Raketa/issues/402)).
 *
 * The field is 6.13's, which arrived with this surface — *"two more surfaces need a field, and a
 * third implementation is exactly the drift a shared primitive exists to prevent"*. What this
 * component owns is the block: the field, the cap, the one control beside it, and when that
 * control is open. It drew a row of quick chips above the field too, asking about an old-loop
 * plan's empty slots, until a booked game's room became the only room
 * ([#576](https://github.com/Raketa02/Raketa/issues/576)): the booking is the plan, so there is
 * nothing left to ask.
 *
 * **The block has one door out, `onPost`** — the screen's `post()`, optimistic and reconciled on
 * `client_message_id`.
 *
 * ## The label is spoken and not drawn, and the hint is not the label
 *
 * `labelHidden`, which is the prop 6.13 said would arrive with the surface that needed one. A box
 * under a header naming the people and the sport, with `Send` beside it, does not need `MESSAGE`
 * over it — and a listener, who has none of that around them, still gets the name (§24.4). The
 * placeholder is a hint while the box is empty and goes the moment somebody types, which is
 * exactly why 6.13 refuses it as a label: the name is `COMPOSER_LABEL`, the hint is
 * `COMPOSER_PLACEHOLDER`, and neither stands in for the other.
 *
 * ## Send is 6.1 `primary`
 *
 * `coralInk` filled with a white label, brightening to `coral` on press — Rule C, because white
 * on `coral` is 3,89:1. It is the variant and not a hand-rolled fill, so the press state and the
 * contrast arrive with it.
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
 * ## The one other thing that closes it is the account, and it greys the whole block
 *
 * A **held** account may read here and may not write (ADR-0148 §9), so the field and Send refuse
 * together, and the field is greyed rather than merely `editable={false}` — the busy
 * shape would say *waiting* about something that is not going to happen. It is only acceptable
 * because the note above the block has already said why, which is the condition 6.2 and 6.13 both
 * attach to a greyed control and the whole of why the screen puts **one** note above this block
 * rather than one beside each control.
 *
 * **Not live does not close it.** Sends are ordinary authenticated `POST`s over a channel that is
 * unidirectional by construction, so writing is unaffected — and disabling the composer would
 * state something false about the half that still works (§3.6).
 *
 * ## The block is bounded by one line along its top, and it sits on the screen's own ground
 *
 * A 1pt `line` along its top and nothing else. `line` and not 5.3's hairline: that is `line2`, a
 * **fold inside** one thing, and this edge **bounds** one — 2.1's *`line` bounds a thing*, and
 * the same edge the tab bar draws along its own top for the same reason (10.2). The bottom is the
 * screen's edge, and a block at the foot of a screen needs one edge drawn to read as one thing.
 * It takes no ground of its own — no `surface`, and no `backgroundColor` at all, it sits on the
 * frame's `paper` — for two reasons that are one. It is part of the room rather than 10.1's pinned
 * CTA slot, so a second bounded surface under a screen whose content is already bounded blocks
 * would be a tray around a tray; and **the bottom safe-area inset is the frame's**, taken under
 * this block by `ConversationScreen`'s `SafeAreaView`, outside the keyboard avoidance
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)) — so a block on a ground of its own
 * would leave a band of paper between itself and the home indicator, and a block that took the
 * inset itself would be counted a second time the moment the keyboard is up. The tab bar stands
 * down inside a conversation, and this block is what stands where it stood; the inset is applied
 * once, and it is applied under it.
 *
 * **No device drew these numbers, and none of them is new.** The paddings are the gutter and
 * `space.sm`, the line is 1pt — every one an existing step, which is why there is no Part 16 row:
 * that table is the diff against the design system, and nothing in it changed.
 */

import { StyleSheet, View } from 'react-native';

import { Button, TextField, theme } from '@/shared/ui';

import { mayPost } from '../domain/stream';

import { COMPOSER_LABEL, COMPOSER_PLACEHOLDER, SEND } from './conversationPresentation';

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
  /** **The block's one door out.** Send posts what is in the box, through the screen's send. */
  readonly onPost: (words: string) => void;
  /** The account may not write here. Every part of the block refuses, and the screen owns the note. */
  readonly refused?: boolean;
}

export function Composer({ text, onChange, onPost, refused = false }: ComposerProps) {
  return (
    // Named so a suite can say *one block*: a claim about what contains what, which nothing a
    // listener hears can carry.
    <View style={s.block} testID="conversation-composer">
      <View style={s.strip}>
        <View style={s.field}>
          <TextField
            label={COMPOSER_LABEL}
            labelHidden
            placeholder={COMPOSER_PLACEHOLDER}
            growTo={COMPOSER_LINES}
            value={text}
            onChangeText={onChange}
            disabled={refused}
          />
        </View>

        {/* 6.1's default and said out loud, because the ticket asks for coral by name. */}
        <Button
          label={SEND}
          variant="primary"
          disabled={refused || !mayPost(text)}
          onPress={() => onPost(text)}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  block: {
    borderTopWidth: 1,
    borderTopColor: theme.color.line,
    paddingVertical: theme.space.sm,
  },
  strip: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    paddingHorizontal: theme.size.gutter,
  },
  field: { flex: 1 },
});

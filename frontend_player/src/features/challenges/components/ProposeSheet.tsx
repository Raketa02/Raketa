/**
 * **`SH.propose`** — the last thing between a built court and four people being asked.
 *
 * It is `features/challenges/`' and not Play's, on
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §8's
 * line: the card's primary button and the court's pinned CTA are the screen's, and the sheet and
 * the send's use-case are this feature's, because this is *the one action in the tab that
 * reaches another person*.
 *
 * ## It states the irreversibility, and **names no duration**
 *
 * *"24 h" is not a string.* Each invited seat carries its own `answer_by` and a challenge born
 * of a mutual yes has none at all, so one constant was standing in for three different
 * sentences. The pre-send half is the one with nothing to render: there is no `challenges`
 * route the client calls before its first send, `GET /sports` carries the right argument at the
 * wrong home — a per-seat answer window is not a property of squash — and **the same screen
 * states the real deadline, per person, from a real timestamp, the moment after the act**. So
 * §14's `{window}` obligation is discharged by **deletion**, and what the sheet owes is the
 * fact the player cannot recover from ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md)
 * §14, §21).
 *
 * ## Two closers, because *nothing opens until they accept* is false for doubles
 *
 * The first acceptance opens the chat, so a doubles sheet promising that nothing opens would be
 * describing a different product. `proposeClosing` holds both.
 *
 * ## The handles are whole, one per line
 *
 * §15's rule is *the whole handle, or nobody*, and a sentence never truncates. `playerName()` is
 * the one thing that turns a player into words, and the names are drawn as a **list** rather
 * than joined: at sixty-four characters a joined phrase is a string no row can hold, and a
 * formatter that returned one would have decided the layout.
 *
 * ## What it does not draw
 *
 * **No refusal, and no pending state.** Confirming here dismisses the sheet, and everything the
 * send then does happens on the court's pinned CTA — pending on the control, and a refusal
 * beside it, where the player can act on it ([#239](https://github.com/Raketa02/Raketa/issues/239)
 * §5). A sheet that stayed up holding a failure would be a modal over the seats that have to
 * change.
 */

import { StyleSheet, Text, View } from 'react-native';

import { playerName, type NamedPlayer } from '@/shared/formatting/playerName';
import { BottomSheet, Button, Note, theme, type FocusTarget } from '@/shared/ui';

import {
  NOBODY_IS_CONTACTED_YET,
  PROPOSE_SHEET_CLOSE_LABEL,
  PROPOSE_SHEET_TITLE,
  SEND_CHALLENGE_LABEL,
  WHO_YOU_ARE_ASKING,
  proposeClosing,
} from './challengePresentation';

export interface ProposeSheetProps {
  readonly visible: boolean;
  readonly onClose: () => void;
  /** Confirming. The caller dismisses the sheet and runs the send — see the module note. */
  readonly onSend: () => void;
  /**
   * The people about to be asked, in seat order and **without the organiser**: nobody is
   * invited to their own challenge, and *"nothing asks whether you want to play the game you
   * just built."*
   */
  readonly invitees: readonly NamedPlayer[];
  /**
   * Which closer the sheet ends on. It is the court's shape and the number of answers it needs,
   * both of which are the caller's facts — the sheet knows nothing about sports or seats.
   */
  readonly lineUp: Parameters<typeof proposeClosing>[0];
  /**
   * The control the sheet was opened from. Focus returns there on close.
   *
   * **Required, where `BottomSheet`'s own is optional.** Part 13 returns focus to the trigger
   * or a listener is dropped at the top of the screen with no idea what happened, and the
   * screen behind this one is hidden while it is up — so a caller that forgot would strand
   * somebody in front of the app's one irreversible act. The two onboarding sheets take the
   * same posture for the same reason.
   */
  readonly returnFocusTo: FocusTarget;
}

export function ProposeSheet({
  visible,
  onClose,
  onSend,
  invitees,
  lineUp,
  returnFocusTo,
}: ProposeSheetProps) {
  return (
    <BottomSheet
      visible={visible}
      onClose={onClose}
      title={PROPOSE_SHEET_TITLE}
      closeLabel={PROPOSE_SHEET_CLOSE_LABEL}
      returnFocusTo={returnFocusTo}
    >
      <View style={s.block}>
        <Text style={s.heading}>{WHO_YOU_ARE_ASKING}</Text>
        {invitees.map((invitee, at) => (
          // The handle where there is one, and the position where there is not: two seats
          // whose rows the record can no longer describe are two seats, and a key of `?`
          // would collapse them.
          <Text key={`${playerName(invitee)}-${at}`} style={s.handle}>
            {playerName(invitee)}
          </Text>
        ))}
      </View>

      {/* The one fact the player cannot recover from, and the whole of what this sheet owes. */}
      <Note variant="amber">{NOBODY_IS_CONTACTED_YET}</Note>

      <Text style={s.closing}>{proposeClosing(lineUp)}</Text>

      <View style={s.action}>
        <Button label={SEND_CHALLENGE_LABEL} size="lg" onPress={onSend} />
      </View>
    </BottomSheet>
  );
}

const s = StyleSheet.create({
  block: { paddingTop: theme.space.sm, gap: theme.space.xxs },
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  handle: { ...theme.type.inlineTitle, color: theme.color.ink },
  closing: { ...theme.type.tiny, color: theme.color.ink, paddingTop: theme.space.sm },
  action: { paddingTop: theme.space.md },
});

/**
 * The deck's two endings — **You have seen everybody** and **Nobody in range yet** — one shape,
 * and only the first offers the reset
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5).
 *
 * They split on `players_in_range` (`domain/deckHand`), and the split is what makes both honest.
 * *You have seen everybody* is the mock: a title, one sentence naming the radius and how long a
 * yes lives — both off the wire — then **Show them again**, which is `POST /deck/reset` and a
 * fresh deal, and **Try the radar**, which flips the toggle. *Nobody in range* keeps its own
 * sentence — the pool description — and *widen it in You*, in the same style, **without** the
 * reset, which would deal nobody; and without the radar door, which would plot nobody.
 *
 * ## Centred, on the paper, in the ending's own shape
 *
 * Not a `Note`: a note is a message block at the top of a column, and this is the whole of what
 * the tab shows. The title is `h1`, the sentences `tiny` in `muted`, both centred with the
 * buttons under them at the mock's widths — `secondary` for the reset, because the deck's one
 * accent is spent on the yes button that is not on screen, and `dark` for the radar, which is
 * the mock's own pair.
 *
 * **The refusal stays on the ending, and the button is the retry.** A reset that fails leaves
 * the sentence above the button rather than a second control, and a reset in flight holds the
 * button `busy`: pressing it twice is one press by contract, but a second deal in flight over
 * the first is not.
 */

import { StyleSheet, Text, View } from 'react-native';

import type { AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import {
  NOBODY_IN_RANGE_TITLE,
  SEEN_EVERYBODY_TITLE,
  SHOW_THEM_AGAIN_LABEL,
  TRY_THE_RADAR_LABEL,
  WIDEN_IN_YOU,
  seenEverybodyLine,
} from './deckPresentation';
import { playErrorMessage } from './playErrorMessage';

export type DeckEndingProps =
  | {
      readonly kind: 'seen-everybody';
      /** The radius the deal ran on, in whole kilometres. */
      readonly radiusKm: number;
      /** How long a yes lives, off the interest read — absent until it lands. */
      readonly ttlDays?: number;
      readonly onShowThemAgain: () => void;
      readonly onTryTheRadar: () => void;
      /** The reset is in flight. */
      readonly resetting: boolean;
      /** The reset was refused, and this is the sentence. */
      readonly resetError: AppError | null;
    }
  | {
      readonly kind: 'nobody-in-range';
      /** The pool description — the count, the radius and the sport, in one sentence. */
      readonly pool: string;
      /** Whether *widen in You* may be said: never to a player already at their own ceiling. */
      readonly mayWiden: boolean;
    };

export function DeckEnding(props: DeckEndingProps) {
  if (props.kind === 'nobody-in-range') {
    return (
      <View style={s.ending}>
        <Text style={s.title} accessibilityRole="header">
          {NOBODY_IN_RANGE_TITLE}
        </Text>
        <Text style={s.line}>{props.pool}</Text>
        {props.mayWiden ? <Text style={s.line}>{WIDEN_IN_YOU}</Text> : null}
      </View>
    );
  }

  return (
    <View style={s.ending}>
      <Text style={s.title} accessibilityRole="header">
        {SEEN_EVERYBODY_TITLE}
      </Text>
      <Text style={s.line}>
        {seenEverybodyLine({
          radiusKm: props.radiusKm,
          ...(props.ttlDays === undefined ? {} : { ttlDays: props.ttlDays }),
        })}
      </Text>

      {props.resetError === null ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {playErrorMessage(props.resetError)}
        </Note>
      )}

      <View style={s.doors}>
        <Button
          label={SHOW_THEM_AGAIN_LABEL}
          variant="secondary"
          size="lg"
          busy={props.resetting}
          busyLabel={SHOW_THEM_AGAIN_LABEL}
          onPress={props.onShowThemAgain}
        />
        <Button
          label={TRY_THE_RADAR_LABEL}
          variant="dark"
          size="lg"
          onPress={props.onTryTheRadar}
        />
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // Centred in whatever the page gives it: the ending is the whole of the tab.
  ending: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingHorizontal: theme.space.lg,
  },
  title: { ...theme.type.h1, color: theme.color.ink, textAlign: 'center' },
  line: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
  doors: { alignItems: 'center', gap: theme.space.sm, paddingTop: theme.space.sm },
});

/**
 * The deck's three round buttons under the stage — **✕, i, the ball** — the path that is never
 * removed ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §3).
 *
 * The drag is the cheap path and these are the accessible one: VoiceOver and TalkBack consume
 * a drag before the stage sees it, so the buttons are how a listener answers, and §20.5's rule
 * is kept in its other half — *the drag is never the only path*. ✕ passes, the ball says yes,
 * and **i** opens the record sheet, which the long press on the card opens too.
 *
 * ## Circles, at the mock's three sizes
 *
 * 54, 42 and 66, measured off the mock — `theme.size.deckAnswer` — and the sizes say which is
 * which: the yes is the largest and coral, the pass a step smaller and white, the record the
 * smallest. That is the 1:2 ratio the two named buttons used to carry, read as diameters. A
 * circle is `radius.pill` on a square box (4.2 as amended, Part 16), and the smallest of the
 * three is under 6.5's 44pt and grows to it by slop on every side — the arithmetic below, rather
 * than a `hit` preset, because no preset reaches sideways on a 42.
 *
 * **Not `Button`.** The primitive draws a word in its label box and sizes its height from a
 * type role; these draw a mark in a fixed circle. They take 6.1's own pairs — `primary`'s
 * `coralInk` / `coral` for the yes, `secondary`'s surface, border and `line2` for the other two,
 * the 40 % fade for a locked one — so the three read as the app's buttons, and the row records
 * itself in Part 16 as the mock's circles rather than as a second button.
 *
 * **Marks, not words.** The ✕ is Feather's `x` — the app's family everywhere but the tab bar
 * ([ADR-0135](../../../../../docs/adr/0135-the-bar-draws-one-family-and-the-bolt-joins-it.md),
 * ADR-0210 §5) —
 * the **i** is the information mark's own serif letter (5.4), and the ball is **drawn**
 * (`DeckBall`): a white outline with its two seams, at Feather's proportion, on the coral. It was the
 * 🎾 emoji as text until 2026-09-15, which the platform substituted in its own colours and clipped
 * at the top. None of the three is spoken: each button carries the name its deck composes — on
 * Players, `deckAnswerLabels` for the person on the card, so a listener hears *Let's play, Marek
 * Z.* and never *tennis ball*; on a group's Games deck, the game's own (*I'm in*, *Not this time*,
 * *Game details*, #553). **The names are the caller's**, because the row is one drawing under two
 * decks whose cards are about different things — a person, and a game.
 *
 * **Coral on the yes, and only there.** §1.2's list is closed at six and the primary button is
 * on it; the yes is the deck's primary act and takes `primary`'s fill and press. The pass and
 * the record are `secondary`'s surface with its border, so the three read as one row of controls
 * on paper rather than three fills. The pressed states are declared, because there is no hover.
 */

import Feather from '@expo/vector-icons/Feather';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { DeckBall } from './DeckBall';

/** The deck's three buttons. It is §20.3's card with three actions beside it instead of one. */
export interface DeckAnswerLabels {
  readonly pass: string;
  readonly accept: string;
  /** `Marek Z.’s record` — the *i*, and the long press's own name. */
  readonly record: string;
}

export interface DeckAnswersProps {
  /** The three buttons' spoken names — see the module note. */
  readonly labels: DeckAnswerLabels;
  readonly onPass: () => void;
  readonly onAccept: () => void;
  readonly onRecord: () => void;
  /**
   * Whether an answer is already on its way — **the two answers lock until the card has left**.
   *
   * Not a `busy` state: nothing is loading, and the answer is optimistic, so the card is
   * already travelling. What this prevents is the second press landing on a person who has been
   * answered and is still on screen, which would record two acts about one card. The record
   * stays open: reading somebody is not an answer.
   */
  readonly answering?: boolean;
}

export function DeckAnswers({
  labels,
  onPass,
  onAccept,
  onRecord,
  answering = false,
}: DeckAnswersProps) {
  const { pass, record, accept } = theme.size.deckAnswer;
  // 6.5: the i is under the minimum, and its neighbours are a large step away on either side,
  // so the slop that lifts it to 44 fits between them.
  const reach = Math.max(0, (theme.size.minTouch - record) / 2);
  const recordSlop = { top: reach, bottom: reach, left: reach, right: reach };

  return (
    <View style={s.row}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={labels.pass}
        accessibilityState={{ disabled: answering }}
        disabled={answering}
        onPress={onPass}
        style={({ pressed }) => [
          s.disc,
          s.paper,
          circle(pass),
          pressed ? s.paperPressed : undefined,
          answering ? s.blocked : undefined,
        ]}
      >
        <Feather name="x" size={theme.size.tabIcon} color={theme.color.ink} />
      </Pressable>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={labels.record}
        onPress={onRecord}
        hitSlop={recordSlop}
        style={({ pressed }) => [
          s.disc,
          s.paper,
          circle(record),
          pressed ? s.paperPressed : undefined,
        ]}
      >
        <Text style={s.info} accessibilityElementsHidden importantForAccessibility="no">
          i
        </Text>
      </Pressable>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel={labels.accept}
        accessibilityState={{ disabled: answering }}
        disabled={answering}
        onPress={onAccept}
        style={({ pressed }) => [
          s.disc,
          s.coral,
          circle(accept),
          pressed ? s.coralPressed : undefined,
          answering ? s.blocked : undefined,
        ]}
      >
        <DeckBall />
      </Pressable>
    </View>
  );
}

/** A square box at the pill's radius, which is a circle — the whole of each button's geometry. */
const circle = (diameter: number) => ({ width: diameter, height: diameter });

const s = StyleSheet.create({
  // Centred under the stage, the three a large step apart, the tallest setting the row's height.
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.space.xl,
  },
  disc: {
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1 `secondary`'s fill and border, and its press.
  paper: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
  },
  paperPressed: { backgroundColor: theme.color.line2 },
  // 6.1 `primary`'s fill and press: `coralInk` at rest, `coral` under the finger.
  coral: { backgroundColor: theme.color.coralInk },
  coralPressed: { backgroundColor: theme.color.coral },
  blocked: { opacity: 0.4 },
  // The information mark's own letter (5.4): the serif form is the one people recognise.
  info: {
    ...theme.type.h2,
    fontFamily: Platform.select({
      ios: theme.font.serif.ios,
      default: theme.font.serif.android,
    }),
    fontStyle: 'italic',
    color: theme.color.ink,
  },
});

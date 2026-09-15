/**
 * **The trash on a called-off card** — *Remove this card*, the reader's own act, and the one
 * control in the app that removes something at once with no sheet in front of it
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §5, §8).
 *
 * ## Why no sheet
 *
 * The act removes a card and not a fact: the challenge row and the screen behind it keep the news
 * for their day, the record is untouched, and nobody else's rail moves. A confirmation would put
 * the withdraw's ceremony on the least consequential act in the app. It is instant, and the card
 * leaves the rail on the reply — a mis-tap loses the card and nothing else, which the record names
 * as the cost and accepts.
 *
 * ## The second icon-only button in the app, on the first one's shape
 *
 * `ChatDoor` one feature over is the precedent, and this takes its shape whole: a glyph with its
 * word spoken — Part 13's *never colour alone* read as *never a glyph alone* — in 6.1 `on-dark`'s
 * own fill at `btnLg`'s height and the touch minimum's width, beside the wide door on the card's
 * one action row. The glyph is Feather `trash-2` and never the character (ADR-0135; Archivo ships
 * no wastebasket), hidden from assistive tech because the control carries the name.
 *
 * ## A challenge act's posture, on a game act
 *
 * Drawn by `features/plans`' card and composed there as `FillTheSeat` is, because the act is this
 * feature's — `POST /games/{id}/dismissal` — and the card is that one's. Pending, never optimistic:
 * the control goes busy and the card stays until the reply says it is gone. A refusal is a re-read
 * of the games list and no words — the fold the re-read lands on is the answer, as it is for a
 * stale fill — and the re-read is `useDismissGame`'s own to declare: unlike `FillTheSeat`, whose
 * feature cannot reach this cache and is handed the composer's `onReRead`, this act lives beside
 * the list it touches.
 */

import Feather from '@expo/vector-icons/Feather';
import { Pressable, StyleSheet } from 'react-native';

import { theme } from '@/shared/ui';

import { useDismissGame } from '../hooks/useGames';

import { REMOVE_THIS_CARD } from './gamePresentation';

export interface RemoveCardProps {
  readonly gameId: string;
}

export function RemoveCard({ gameId }: RemoveCardProps) {
  const dismiss = useDismissGame();

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={REMOVE_THIS_CARD}
      accessibilityState={{ busy: dismiss.isPending, disabled: dismiss.isPending }}
      disabled={dismiss.isPending}
      onPress={() => dismiss.mutate(gameId)}
      hitSlop={theme.hit.btn}
      style={({ pressed }) => [s.door, pressed ? s.pressed : undefined]}
    >
      <Feather
        name="trash-2"
        size={theme.size.tabIcon}
        color={theme.color.surface}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
    </Pressable>
  );
}

const s = StyleSheet.create({
  door: {
    minWidth: theme.size.minTouch,
    minHeight: theme.size.btnLg,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.onDarkFill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1 `on-dark`'s pressed fill, because that is the shape this control borrows.
  pressed: { backgroundColor: theme.color.onDarkFillPressed },
});

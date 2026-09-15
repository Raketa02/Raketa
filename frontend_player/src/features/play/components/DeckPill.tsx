/**
 * The deck's two pills — the **counter** floating over the card's foot and the **chip** in the
 * header's right slot — one shape in two colours
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §4, §5, §7).
 *
 * `radius.pill` is the chip's — *the only true pill* — and 4.2 as amended by ADR-0167 gave it a
 * second user; §7's table gives it these two: *the chip is the pill, and the counter is one*.
 * Neither is a `Chip`, because neither is pressable: a chip is a filter you tap, and these are
 * two sentences. Neither is a `Tag` either — a tag is 6pt-cornered and 9,5pt, and these are the
 * mock's own pill at the chip's height with the button's 12pt word.
 *
 * **Volt with `ink`** for the chip — a fill anywhere, 13,96:1, and the one the mock draws for
 * *2 want to play you*; **`night` with `surface`** for the counter, 13,29:1, the toast's own
 * pair, because it floats over the card's foot and the bottom of the wash is near-black.
 * Colour is not the signal on either: each is a sentence.
 *
 * **Both announce as text.** A listener reaches the chip after the toggle and the counter after
 * the card, each a sentence about a number — and the chip is not drawn at all at nought, so
 * there is never an empty pill to land on.
 *
 * **Where it sits is its bed's decision, not the pill's.** The header's right slot pins the chip
 * to the right and the counter's box centres it over the card's foot; the pill hugs its words in
 * either. It carried an `alignSelf: 'flex-start'` of its own until 2026-09-15, and a child's
 * `alignSelf` outranks its parent's `alignItems` — so the counter sat at the card's left edge
 * while its box said *centre*.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

export type DeckPillTone = 'volt' | 'night';

export interface DeckPillProps {
  readonly children: string;
  readonly tone: DeckPillTone;
}

export function DeckPill({ children, tone }: DeckPillProps) {
  return (
    <View style={[s.pill, FILL[tone]]}>
      <Text style={[s.words, INK[tone]]} numberOfLines={1}>
        {children}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  pill: {
    height: theme.size.chip,
    borderRadius: theme.radius.pill,
    paddingHorizontal: theme.space.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  words: { ...theme.type.btn },
});

const FILL = StyleSheet.create({
  volt: { backgroundColor: theme.color.volt },
  night: { backgroundColor: theme.color.night },
});

const INK = StyleSheet.create({
  volt: { color: theme.color.ink },
  night: { color: theme.color.surface },
});

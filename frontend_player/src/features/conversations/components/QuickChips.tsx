/**
 * **The questions the room still has to ask**, as words somebody can post without typing them.
 *
 * 6.2 `Chip`s in a row above the composer, and **a chip posts words and nothing else**
 * (ADR-0144): *"Saturday works?"* is a question, and a chip that also filled the day slot would
 * record an agreement nobody had yet — the one thing the plan card must not do. So pressing one
 * sends a message and changes no state anywhere.
 *
 * **Which chips there are is `domain/quickChips.ts`'** — one per unfilled slot in slot order,
 * plus *On my way* when the agreed day is today, capped at three by the conditional rather than
 * by a `slice`. **What each one says is `conversationPresentation.ts`'** — and each asks the
 * question its slot is about and names nothing, because a chip naming Saturday is a chip that is
 * wrong six days a week.
 *
 * They scroll horizontally rather than wrapping: three questions at `type.chip` fit a phone
 * comfortably, and a row that wrapped to two lines would push the composer up by a line on a
 * screen where a keyboard is already taking half of it.
 *
 * **A held account greys them rather than losing them**, because a chip is a message and a hold
 * stops you writing anywhere another player sees it (ADR-0148 §9). Greyed and not removed: the row
 * is what says the room still has three questions in it, and the note above the strip is what says
 * why none of them can be asked — one note for every refused control on the screen, never one per
 * chip.
 */

import { ScrollView, StyleSheet } from 'react-native';

import { Chip, theme } from '@/shared/ui';

import type { QuickChip } from '../domain/quickChips';

import { QUICK_CHIP } from './conversationPresentation';

export interface QuickChipsProps {
  readonly chips: readonly QuickChip[];
  /** What pressing one does — post its words. It is the composer's own send, pre-filled. */
  readonly onPost: (words: string) => void;
  /** The account may not write here. Every chip greys; the screen owns the one note. */
  readonly refused?: boolean;
}

export function QuickChips({ chips, onPost, refused = false }: QuickChipsProps) {
  if (chips.length === 0) return null;

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={s.row}
      keyboardShouldPersistTaps="handled"
    >
      {chips.map((chip) => (
        <Chip
          key={chip}
          label={QUICK_CHIP[chip]}
          disabled={refused}
          onPress={() => onPost(QUICK_CHIP[chip])}
        />
      ))}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', gap: theme.space.xs, paddingHorizontal: theme.size.gutter },
});

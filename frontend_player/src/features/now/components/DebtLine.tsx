/**
 * The one line on Now that is about the player rather than about a match.
 *
 * `ADR-0070` puts exactly one viewer fact on the envelope beside the three
 * regions, and this draws it: **an amount, its currency, and one boolean** meaning
 * *she may not create a match or book a court*. Everything below is a rendering of
 * those three; nothing is computed and nothing is compared.
 *
 * **A screen fact, not a fourth region.** The three regions are ordered lists of
 * tappable cards, which is what makes that shape worth having, and a region
 * holding one untappable sentence would break it on its first use. So this sits
 * above them and belongs to none of them.
 *
 * **It is not an invitation, and it earns its place on one argument.** `ADR-0050`
 * still holds — a row that is neither a thing the player is in nor a thing she
 * could join is furniture — and the argument that buys this row is `ADR-0058`'s:
 * she cannot create or book, Now renders the create tab, and without the line she
 * meets the block as a bare refusal. That argument, not the slot, is the entry fee.
 *
 * **Amber, and no glyph.** Colour is picked by meaning and amber is
 * *reversible-but-not-yet-wrong*, which is exactly a balance she can settle —
 * coral is the accent and would make owing money the loudest thing on a screen
 * about matches, and red is for something that ended badly. The sentences carry
 * the state in words, so the colour is never the only cue.
 *
 * **No `alert` role.** A note announces itself when it *appears*, and this one
 * appears with the screen — on arrival, on every pull, on every one of
 * `ADR-0054`'s four asks. Announcing a standing fact as an alert would interrupt
 * her each time she came back to a screen she already knew about it from. It is
 * prose, read in document order, and it is read **before** the regions because it
 * is drawn before them.
 *
 * **Nothing here is a control.** There is no *settle* button, because there is no
 * payment surface to open and a button whose destination does not exist is the one
 * outcome worse than silence (`ADR-0083`'s rule, applied off a card).
 */

import { StyleSheet, Text, View } from 'react-native';

import { Note, theme } from '@/shared/ui';

import type { DebtLine as DebtLineValue } from '../domain/ComposedScreen';

import { debtSentences } from './nowCopy';
import { GUTTER } from './nowGeometry';

/** So *at most once on the screen* is assertable rather than implied. */
export const DEBT_LINE_ID = 'now-debt-line';

export function DebtLine({ debt }: { readonly debt: DebtLineValue }) {
  return (
    <View testID={DEBT_LINE_ID} style={s.line}>
      <Note variant="amber">
        {debtSentences(debt).map((sentence) => (
          // Keyed by the sentence, which is safe here in a way it is not for the
          // fit reasons beside it: this list is one to three fixed sentences from
          // one table, never a server-composed list that two entries could word
          // alike.
          <Text key={sentence} style={s.sentence}>
            {sentence}
          </Text>
        ))}
      </Note>
    </View>
  );
}

const s = StyleSheet.create({
  line: { paddingHorizontal: GUTTER, marginBottom: theme.space.xl },
  sentence: { ...theme.type.tiny, color: theme.color.ink },
});

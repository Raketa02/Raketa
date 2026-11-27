/**
 * **The other kind's door, opened** — the panel the Games tab's menu's dimmed line opens over the
 * deck (the switch's dimmed kind until #862) ([#740](https://github.com/Raketa02/Raketa/issues/740);
 * [ADR-0201](../../../../../docs/adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
 * §2; the screens A2.1; the words §28).
 *
 * Ania is Competitive in padel and taps `For fun`:
 *
 * > **You play padel competitively, so Raketa only puts you in competitive games.**
 * > Want for-fun games too?
 * >
 * > **Either suits me** — *Keep your 7 competitive cards and get for-fun ones too.*
 * > **For fun** — *Your 7 competitive cards go. Games you're In on stay.*
 * > **Keep competitive**
 *
 * ## In place, over the deck, and taking no height from it
 *
 * Not a route and not a sheet: `GamesDeck` draws this **over the deck's area** — on a ground it
 * lays absolutely over it, the paper the cards stand on, under the cap line and the tabs, the menu
 * the player picked from folded away first — so the stage underneath keeps the size it measured and
 * nothing in the stack moves (Q7's argument against a line under the switch).
 * It scrolls inside that area rather than growing it, so on a short phone or at a large text size
 * *Keep* is reached by a drag, never cut off and never by pushing the cards.
 *
 * It meets `shared/ui`'s three overlay obligations this way: what it covers is hidden from a screen
 * reader (`behindOverlay`, spread by the deck on the area's content, of which this is the sibling);
 * Android's back closes it, as it closes every layer — except while an answer is on its way, which
 * nothing closes; and **it moves no focus**, as ADR-0198 has the app add no screen-reader behaviour
 * of its own for now.
 *
 * ## The same question, asked about a change
 *
 * It is the first-time question's surface — the dark card and its glossed answers in the three
 * words `playIntentPresentation` gives every screen that asks — because it writes the same fact,
 * reported on the same **`DECK`** surface (ADR-0201 §2; `DeclarationInterstitial`). What differs is
 * what it says: why the other kind is missing, and **what each answer costs** in the player's own
 * count of the kind they play, the one their menu shows. And one answer is **highlighted**:
 * *Either suits me* comes first on the `primary` fill, because it is the answer that loses nothing;
 * the kind tapped and *Keep* are `onDark`, as the first-time question's three are (5.2 as amended).
 *
 * **The write is the deck's** (`onAnswer`, the answer in flight as `answering`, a refusal as
 * `refusal`), not this panel's: an answer must still land — the deck moved to the kind tapped,
 * the group read again — when the panel has gone meanwhile, by a re-read that shows the kind or a
 * change of sport, and a write held by this component would be dropped with it. A refusal is the
 * first-time question's coral note above the card.
 */

import { ScrollView, StyleSheet, Text, View } from 'react-native';

import { sportInLine, sportLabel } from '@/features/onboarding/types';
import { recoveryMessage, type AppError } from '@/shared/errors';
import { useHardwareBack } from '@/shared/lib/platform';
import { Button, DarkCard, Note, theme } from '@/shared/ui';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import { declarationOptionLabel, intentLabel } from '@/shared/vocabulary/playIntentPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import { intentAnswering, type DoorAnswer, type DoorPanel } from '../domain/deck';

import { doorQuestion, doorTitle, dropCost, eitherCost, keepLabel } from './doorPresentation';

export interface KindDoorProps {
  readonly sport: Sport;
  readonly panel: DoorPanel;
  /** The intent being written for this sport, while it is — that answer busy, the rest shut. */
  readonly answering?: PlayIntent;
  /** Why the last answer was refused, until another is given. */
  readonly refusal?: AppError;
  readonly onAnswer: (answer: DoorAnswer) => void;
  /** *Keep*, or Android's back — nothing sent. */
  readonly onClose: () => void;
}

export function KindDoor({ sport, panel, answering, refusal, onAnswer, onClose }: KindDoorProps) {
  const sportName = sportLabel(sport);

  useHardwareBack(() => {
    if (answering === undefined) onClose();
  });

  const offer = (answer: DoorAnswer, gloss: string) => {
    const intent = intentAnswering(panel, answer);
    return (
      <Button
        key={answer}
        label={intentLabel(intent)}
        gloss={gloss}
        accessibilityLabel={declarationOptionLabel(intent, sportName)}
        variant={answer === 'either' ? 'primary' : 'onDark'}
        busy={answering === intent}
        disabled={answering !== undefined && answering !== intent}
        onPress={() => onAnswer(answer)}
      />
    );
  };

  return (
    <ScrollView
      testID="kind-door"
      style={s.fill}
      contentContainerStyle={s.content}
      // Inside the page's own scroller, which Android lets lead unless this one asks.
      nestedScrollEnabled
    >
      {refusal === undefined ? null : (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(refusal)}
        </Note>
      )}

      <DarkCard>
        <Text style={s.title}>{doorTitle(panel, sportInLine(sport))}</Text>
        <Text style={s.body}>{doorQuestion(panel)}</Text>

        <View style={s.answers}>
          {offer('either', eitherCost(panel))}
          {offer('tapped', dropCost(panel))}
          <Button
            label={keepLabel(panel)}
            variant="onDark"
            disabled={answering !== undefined}
            onPress={onClose}
          />
        </View>
      </DarkCard>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  // The whole of the ground `GamesDeck` lays over the deck's area, so the cards are covered.
  fill: { flex: 1 },
  content: { gap: theme.space.sm },
  title: { ...theme.type.cardTitle, color: theme.color.surface },
  body: { ...theme.type.tiny, color: theme.color.onDarkTiny, marginTop: theme.space.xxs },
  answers: { gap: theme.space.xs, marginTop: theme.space.md },
});

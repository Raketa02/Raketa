/**
 * ADR-0094's **one-tap interstitial** — *permanent, not a migration path* — in front of a group's
 * Games deck ([#553](https://github.com/Raketa02/Raketa/issues/553), the screens A2.1).
 *
 * A group deals a player only the kind of game their intent wants, and nothing while they have
 * declared none, so the one-time question replaces the deck until it is answered. It reports
 * `DECK` — the contract's word for a deck, which is what the tab is — and says its one line about
 * who reads the answer (`GROUP_DECK_DECLARATION_BODY`). `onDeclared` is the caller's, so the deck
 * is read again for the segments the answer now shows; the interstitial knows nothing about what
 * it stands in front of.
 *
 * It began on Find a game, which reported `SEARCH_SWITCH` and said its own line, and came here
 * with the Games deck ([#574](https://github.com/Raketa02/Raketa/issues/574)); that screen left
 * with the old loop ([#576](https://github.com/Raketa02/Raketa/issues/576)), and its surface, its
 * line and the two props that let two callers differ went with it. A refusal is said in the app's
 * recovery sentence: the declaration's route answers only a lost race and a malformed request.
 *
 * **It is not the mode toggle, and the two must never be collapsed.** This writes a
 * `PlayIntent` with three values; the toggle chooses a `SearchMode` with two. That arity gap
 * is ADR-0094's central move, and `domain/playMode` holds the whole argument.
 *
 * ## Why it is a dark card and not a note
 *
 * It was a [5.4](../../../../docs/design-system.md#54-note--the-message-block) note, and a note
 * is the surface this app carries *reasoning* on. What is being asked for here is a **fact
 * about the player**, kept on their profile and read by other people's searches — and the app
 * already has one surface for those: [5.2](../../../../docs/design-system.md#52-dark-card)
 * draws the onboarding result and nothing else
 * ([#293](https://github.com/Raketa02/Raketa/issues/293)). On Find a game the note was drawn
 * as a sibling of the mode section, same width and same rhythm, so proximity was grouping a
 * search's toggle with a profile's answer and *"looks like the user is selecting options for
 * the same thing"* was the correct reading of it. The render order is what took the pair
 * apart; the surface is what says which of the two the remaining one is.
 *
 * **The three answers are stacked full-width buttons rather than a wrapped row of them**, and
 * each carries a gloss saying what somebody reading it would take it to mean. That is 6.1's
 * `onDark` variant and its `gloss`, both of which live on `Button` — the variant was specified
 * in 6.1 and unbuilt, and a fill, a pressed fill and a blocked opacity re-declared in this file
 * would be the second copy of the button `shared/ui/README.md` exists to prevent.
 *
 * **The one in flight is busy and the other two are disabled**, which is `Button`'s own
 * distinction — *a busy button is not a disabled button* — and the mutation's `variables` are
 * what tell them apart. All three were `disabled` while any of them was writing, which
 * announced *unavailable* for the one the player had just pressed.
 *
 * **The failure stays on paper, above the card.** Coral is the app's failure colour and the
 * dark card's repaint has no on-dark coral in it; a white line inside the card would be a
 * failure carried by wording alone, next to a screen that draws every other one as a coral
 * note. So it is drawn as that same note, above the card, exactly as the search's own refusal
 * is drawn above the court card that failed.
 */

import { StyleSheet, Text, View } from 'react-native';

import { useDeclarePlayIntent } from '@/features/player_profile/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, DarkCard, Note, theme } from '@/shared/ui';
import { PLAY_INTENTS } from '@/shared/vocabulary/playIntent';
import {
  declarationOptionLabel,
  intentGloss,
  intentLabel,
} from '@/shared/vocabulary/playIntentPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  DECLARATION_EYEBROW,
  GROUP_DECK_DECLARATION_BODY,
  declarationTitle,
} from './declarationPresentation';

/**
 * The `PlayIntentSurface` this screen reports — the deck's, and no other: the rating tail, the
 * drift prompt and the profile screen write through their own paths.
 */
const DECLARED_ON = 'DECK';

export interface DeclarationInterstitialProps {
  readonly sport: Sport;
  /** This app's word for that sport — the caller already drew it on a chip. */
  readonly sportName: string;
  /** The answer has landed — for a caller whose own read the answer changes. */
  readonly onDeclared?: () => void;
}

export function DeclarationInterstitial({
  sport,
  sportName,
  onDeclared,
}: DeclarationInterstitialProps) {
  const declare = useDeclarePlayIntent();
  // Which answer is being written, and therefore which one is *busy* rather than merely shut.
  const inFlight = declare.isPending ? declare.variables?.intent : undefined;

  return (
    <View style={s.block}>
      {/* Above the card and on paper — see the module note. */}
      {declare.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(declare.error)}
        </Note>
      ) : null}

      <DarkCard>
        <Text style={s.eyebrow}>{DECLARATION_EYEBROW}</Text>
        <Text style={s.title}>{declarationTitle(sportName)}</Text>
        <Text style={s.body}>{GROUP_DECK_DECLARATION_BODY}</Text>

        <View style={s.answers}>
          {PLAY_INTENTS.map((intent) => (
            /* One button is one element to a listener, and the name is unchanged: the gloss is
               the sighted half of what `declarationOptionLabel` has been saying all along, so
               reading it out as a second line would say the same thing twice. */
            <Button
              key={intent}
              label={intentLabel(intent)}
              gloss={intentGloss(intent)}
              accessibilityLabel={declarationOptionLabel(intent, sportName)}
              variant="onDark"
              busy={inFlight === intent}
              disabled={declare.isPending && inFlight !== intent}
              onPress={() =>
                declare.mutate(
                  { sport, intent, surface: DECLARED_ON },
                  { onSuccess: () => onDeclared?.() },
                )
              }
            />
          ))}
        </View>
      </DarkCard>
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  title: { ...theme.type.cardTitle, color: theme.color.surface },
  body: { ...theme.type.tiny, color: theme.color.onDarkTiny, marginTop: theme.space.xxs },
  answers: { gap: theme.space.xs, marginTop: theme.space.md },
});

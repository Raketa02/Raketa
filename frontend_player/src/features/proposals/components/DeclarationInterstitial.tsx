/**
 * ADR-0094's **one-tap interstitial** — *permanent, not a migration path*.
 *
 * A player rated in a sport and never asked what kind of game they want in it is refused by
 * every matchmaking route with `play_intent_not_declared`. This is the screen that lets them
 * answer, and it is opened **knowingly, before the refusal** rather than after it: the profile
 * read already carries what was declared, and the difference against `GET /ratings` is a set
 * difference the surface holds for nothing.
 *
 * ## Why it is a component and not a block on one screen
 *
 * It began inline on Find a game, which was the only surface that could be refused for this.
 * The deck is the second: `POST /deck` has **no mode to read**, so it reads the declaration —
 * *"without one there is nothing at all to go on"* — and its sport chips can land on a rated,
 * undeclared sport exactly as the search screen's can. Two copies of a question whose answer
 * is a permanent write is two places for the wording, the surface code and the refusal path to
 * drift apart.
 *
 * ## The surface is the caller's, because the two callers are two screens
 *
 * `PlayIntentSurface` is a closed **five**, and the fifth is `DECK`
 * ([#280](https://github.com/Raketa02/Raketa/issues/280)). It shipped as a widening rather
 * than a rename of `SEARCH_SWITCH` into a `PLAY_SWITCH` true of both: the code is stored
 * verbatim on the backend's `PlayIntentDeclared` and read back as itself, so a rename is an
 * event migration bought on a field nothing branches on.
 *
 * So `declaredOn` is a **required prop**, and it is the one thing that must differ between the
 * two callers — every other word, write and refusal on this screen is shared, which is why the
 * component exists. It was deliberately not a prop while the deck had no value of its own: a
 * prop carrying one value at two call sites is a seam invented for a distinction the contract
 * could not express. Now it can, so the seam is real and the type is `SEARCH_SWITCH | DECK` —
 * the rating tail, the drift prompt and the profile screen write through their own paths and
 * cannot reach this one.
 *
 * **The deck has since left** ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §2): it deals everybody under one ruler and reads no declaration, so `play_intent_not_declared`
 * is never raised by it and this screen has one caller again. `declaredOn` stays a prop — the
 * surface is still the caller's fact, recorded beside the write — but its type names the one
 * Play surface that still writes here, because a member nothing can send is a value the contract
 * keeps for the events that carry it and this component does not. The argument above is kept as
 * the record of why the seam was cut where it was.
 *
 * **A group's Games tab is the second caller again** ([#553](https://github.com/Raketa02/Raketa/issues/553),
 * the screens A2.1): a group deals a player only the kind of game their intent wants, and nothing
 * while they have declared none, so the one-time question replaces the deck until it is answered.
 * It reports `DECK` — the contract's word for a deck, which is what the tab is — and says its own
 * one line about who reads the answer (`GROUP_DECK_DECLARATION_BODY`), because *a yes on Players*
 * is not the reader there. `onDeclared` is the caller's, so the deck is read again for the
 * segments the answer now shows; the interstitial knows nothing about what it stands in front of.
 *
 * **It lives with the Games deck** ([#574](https://github.com/Raketa02/Raketa/issues/574)), the
 * caller that stays when Find a game goes with the old loop
 * ([#569](https://github.com/Raketa02/Raketa/issues/569)); `SEARCH_SWITCH` and its line leave
 * with that screen. **What a refusal says is the caller's too** (`refusalMessage`), for the reason
 * the stage's words are: Find a game says Play's own sentences, as it always has, and the Games
 * deck says the app's recovery sentence — the declaration's route answers only a lost race and a
 * malformed request, and neither is a search's to explain.
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
import type { AppError } from '@/shared/errors';
import { Button, DarkCard, Note, theme } from '@/shared/ui';
import { PLAY_INTENTS } from '@/shared/vocabulary/playIntent';
import {
  declarationOptionLabel,
  intentGloss,
  intentLabel,
} from '@/shared/vocabulary/playIntentPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  DECLARATION_BODY,
  DECLARATION_EYEBROW,
  GROUP_DECK_DECLARATION_BODY,
  declarationTitle,
} from './declarationPresentation';

/**
 * The two of `PlayIntentSurface` a Play screen may report, spelled here rather than derived.
 *
 * Two values and not five: the rating tail, the drift prompt and the profile screen write
 * through their own paths, and a component that accepted `DRIFT_PROMPT` would let the prompt
 * sheet's value be reported from a place that is not the prompt sheet.
 *
 * It is **not** `Extract<…>` off the generated union, though that would say the same thing in
 * fewer words. Generated types are transport and are read only in a feature's `api/` or
 * `mappers/` layer, which `mappers/wireVocabulary.ts` argues for in writing and rejects this
 * exact shortcut by name. Nothing is lost by spelling it: `declare.mutate` below takes the
 * wire union, so a member the contract drops or renames makes this type unassignable *there*
 * — the same red build, on the same `pnpm typecheck`, without transport reaching `components/`.
 */
export type PlayDeclarationSurface = 'SEARCH_SWITCH' | 'DECK';

/** Who reads the answer, said on each surface — see the module note. */
const BODY: Readonly<Record<PlayDeclarationSurface, string>> = {
  SEARCH_SWITCH: DECLARATION_BODY,
  DECK: GROUP_DECK_DECLARATION_BODY,
};

export interface DeclarationInterstitialProps {
  readonly sport: Sport;
  /** This app's word for that sport — the caller already drew it on a chip. */
  readonly sportName: string;
  /** Which Play screen this is. See the module note — it is the caller's to say. */
  readonly declaredOn: PlayDeclarationSurface;
  /** The answer has landed — for a caller whose own read the answer changes. */
  readonly onDeclared?: () => void;
  /** The sentence a refused answer is said in — the caller's words. See the module note. */
  readonly refusalMessage: (error: AppError) => string;
}

export function DeclarationInterstitial({
  sport,
  sportName,
  declaredOn,
  onDeclared,
  refusalMessage,
}: DeclarationInterstitialProps) {
  const declare = useDeclarePlayIntent();
  // Which answer is being written, and therefore which one is *busy* rather than merely shut.
  const inFlight = declare.isPending ? declare.variables?.intent : undefined;

  return (
    <View style={s.block}>
      {/* Above the card and on paper — see the module note. It is the same coral note the
          screen draws over the court card a search was refused on. */}
      {declare.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {refusalMessage(declare.error)}
        </Note>
      ) : null}

      <DarkCard>
        <Text style={s.eyebrow}>{DECLARATION_EYEBROW}</Text>
        <Text style={s.title}>{declarationTitle(sportName)}</Text>
        <Text style={s.body}>{BODY[declaredOn]}</Text>

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
                  { sport, intent, surface: declaredOn },
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

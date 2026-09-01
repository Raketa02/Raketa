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
 * **It is not the mode toggle, and the two must never be collapsed.** This writes a
 * `PlayIntent` with three values; the toggle chooses a `SearchMode` with two. That arity gap
 * is ADR-0094's central move, and `domain/playMode` holds the whole argument.
 */

import { StyleSheet, Text, View } from 'react-native';

import { useDeclarePlayIntent } from '@/features/player_profile/types';
import type { Sport } from '@/shared/vocabulary/sport';
import { Button, Note, theme } from '@/shared/ui';

import { PLAY_INTENTS } from '../domain/vocabulary';

import {
  DECLARATION_BODY,
  declarationOptionLabel,
  declarationTitle,
  intentLabel,
} from './findAGamePresentation';
import { playErrorMessage } from './playErrorMessage';

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

export interface DeclarationInterstitialProps {
  readonly sport: Sport;
  /** This app's word for that sport — the caller already drew it on a chip. */
  readonly sportName: string;
  /** Which of the two Play screens this is. See the module note — it is the caller's to say. */
  readonly declaredOn: PlayDeclarationSurface;
}

export function DeclarationInterstitial({
  sport,
  sportName,
  declaredOn,
}: DeclarationInterstitialProps) {
  const declare = useDeclarePlayIntent();

  return (
    <Note title={declarationTitle(sportName)}>
      <Text style={s.body}>{DECLARATION_BODY}</Text>
      {declare.error !== null ? (
        <Text style={s.failureLine} accessibilityRole="alert">
          {playErrorMessage(declare.error)}
        </Text>
      ) : null}
      <View style={s.answers}>
        {PLAY_INTENTS.map((intent) => (
          <Button
            key={intent}
            label={intentLabel(intent)}
            accessibilityLabel={declarationOptionLabel(intent, sportName)}
            variant="secondary"
            disabled={declare.isPending}
            onPress={() => declare.mutate({ sport, intent, surface: declaredOn })}
          />
        ))}
      </View>
    </Note>
  );
}

const s = StyleSheet.create({
  body: { ...theme.type.tiny, color: theme.color.ink },
  failureLine: { ...theme.type.tiny, color: theme.color.coralInk },
  answers: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});

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
 * ## The surface it reports is `SEARCH_SWITCH` from both, and that is a rough edge
 *
 * `PlayIntentSurface` is a **closed four** — `RATING_TAIL`, `SEARCH_SWITCH`, `DRIFT_PROMPT`,
 * `PROFILE_SCREEN` — and none of them is the deck. It is client-asserted context recorded
 * beside a fact, *"never a thing any decision branches on"*, so the cost of the nearest value
 * is bounded: both Play surfaces are a sport switch on a Play screen, and nothing downstream
 * reads which. It is not a prop, because a prop with one value at two call sites is a seam
 * invented for a fifth value that does not exist; a fifth value is a **contract change to
 * argue**, and [#280](https://github.com/Raketa02/Raketa/issues/280) is where that argument
 * belongs.
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

/** The nearest of the closed four. See the module note — the deck has no value of its own. */
const DECLARED_ON = 'SEARCH_SWITCH' as const;

export interface DeclarationInterstitialProps {
  readonly sport: Sport;
  /** This app's word for that sport — the caller already drew it on a chip. */
  readonly sportName: string;
}

export function DeclarationInterstitial({ sport, sportName }: DeclarationInterstitialProps) {
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
            onPress={() => declare.mutate({ sport, intent, surface: DECLARED_ON })}
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

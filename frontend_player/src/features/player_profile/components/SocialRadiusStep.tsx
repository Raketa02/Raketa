/**
 * Step five of onboarding's second part: **how far will you travel?**
 *
 * It comes immediately after *where do you play*, so the question makes sense when it
 * arrives: a distance is a distance *from* somewhere, and the screen before this one is
 * where that somewhere was given.
 *
 * ## A slider, and not the four fixed chips both source specifications drew
 *
 * A deliberate departure, recorded in the parent spec. Four jumps are four opinions about
 * which distances matter; a slider is the player's own, and the precision it offers costs
 * nothing because the step is a whole kilometre — nobody lands on a fractional distance the
 * matcher could not use anyway.
 *
 * ## Nothing here decides anything
 *
 * The bounds, the snapping and the stepping are `searchRadius`'s, with their own tests and
 * no renderer; the words are `radiusPresentation`'s; the track, the thumb and the two
 * accessibility actions are the design system's. What is left in this file is what a player
 * sees — the same split the four steps before it made, and for the same reason: the profile
 * editor will obey these rules from a screen that looks nothing like this one.
 *
 * ## The four numbers are the server's, and the step opens at one of them
 *
 * The minimum, the maximum, the step and the default arrive with the tag vocabulary from
 * `GET /player-profile/options`. The default is written into the draft as soon as it is
 * known, which is what lets the step be **passed without touching the slider** — a player
 * who continues straight past this screen has answered it, at the number product chose.
 * Only when nothing has been answered yet: walking back here must find the value the player
 * set, never the default reclaiming it.
 */

import { useRouter } from 'expo-router';
import { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { recoveryMessage } from '@/shared/errors';
import { Button, Note, RadiusSlider, theme } from '@/shared/ui';

import {
  openingRadius,
  radiusAtFraction,
  radiusFraction,
  steppedRadius,
  topOfScale,
} from '../domain/searchRadius';
import { stepAfter } from '../domain/socialSteps';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileDraft } from '../store/profileDraft.store';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  RADIUS_BODY,
  RADIUS_LABEL,
  RADIUS_TITLE,
  radiusFigure,
  radiusWords,
  spokenRadius,
  widestRadiusFigure,
} from './radiusPresentation';

export function SocialRadiusStep() {
  const router = useRouter();
  const options = useProfileOptions();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('radius');
  const bounds = options.data?.searchRadius;
  const held = draft?.searchRadiusKm;
  const radius = bounds === undefined ? undefined : openingRadius(held, bounds);

  /**
   * Open at the served default, in the **draft** and not only on the screen.
   *
   * A step that drew the default but recorded nothing would be a step a player passed
   * without answering, and the commit at the end of the part carries a radius whether or
   * not this screen was touched. Guarded on `held`, so it seeds once and never overwrites.
   */
  useEffect(() => {
    if (bounds === undefined || held !== undefined || radius === undefined) return;
    // `radius`, not `bounds.defaultKm`: *what this step opens at* is `openingRadius`'s
    // answer and is stated once, in the domain. Spelling the default here as well would be
    // the same rule written twice, one edit away from the two disagreeing.
    answer({ searchRadiusKm: radius });
  }, [bounds, held, radius, answer]);

  return (
    <SocialStepLayout
      step="radius"
      action={
        radius === undefined || next === undefined ? null : (
          <Button
            label="Continue"
            size="lg"
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={`Goes to ${stepCopy(next).title}`}
          />
        )
      }
    >
      <Text style={s.asks}>{stepCopy('radius').asks}</Text>

      {/* Paused, not loading: `networkMode: 'online'` holds a query rather than failing it,
          so an offline player would otherwise watch a spinner forever. */}
      {options.fetchStatus === 'paused' ? (
        <Note variant="amber">
          You&apos;re offline. The distances will load as soon as you&apos;re back.
        </Note>
      ) : null}

      {options.isPending && options.fetchStatus !== 'paused' ? (
        <ActivityIndicator accessibilityLabel="Loading distances" color={theme.color.muted} />
      ) : null}

      {options.error !== null ? (
        <View style={s.failure}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(options.error)}
          </Note>
          <Button label="Try again" variant="secondary" onPress={() => void options.refetch()} />
        </View>
      ) : null}

      {bounds === undefined || radius === undefined ? null : (
        <RadiusSlider
          value={radius}
          minimum={bounds.minimumKm}
          /* The top of the *scale*, which is the served maximum whenever the step divides
             the range and the last value on a step when it does not. What is announced has
             to be a radius the control can be driven to and the commit would accept —
             announcing one neither is true of would be the screen describing a distance
             nobody can hold. */
          maximum={topOfScale(bounds)}
          fraction={radiusFraction(radius, bounds)}
          onSlideTo={(fraction) => answer({ searchRadiusKm: radiusAtFraction(fraction, bounds) })}
          onIncrement={() => answer({ searchRadiusKm: steppedRadius(radius, bounds, 'increment') })}
          onDecrement={() => answer({ searchRadiusKm: steppedRadius(radius, bounds, 'decrement') })}
          figure={radiusFigure(radius)}
          widestFigure={widestRadiusFigure(bounds)}
          words={radiusWords(radius)}
          accessibilityLabel={RADIUS_LABEL}
          accessibilityValueText={spokenRadius(radius)}
        />
      )}

      {/* After the control rather than before it. The location step explains first because
          a permission prompt a player did not expect is refused by people who would have
          said yes; nothing here prompts for anything, and what this note carries is what
          the number *does* — which is read against a distance the player has already set.

          `info` rather than `amber`: this explains what the product does with the answer,
          and amber means *watch this, reversible, not yet wrong* — a status about the
          player's own answer rather than an explanation of the app (design-system 1.3). */}
      <Note variant="info" title={RADIUS_TITLE}>
        {RADIUS_BODY}
      </Note>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  /** Secondary text is always `tiny` in `muted` — what this step asks. */
  asks: { ...theme.type.tiny, color: theme.color.muted },
  failure: { gap: theme.space.sm },
});

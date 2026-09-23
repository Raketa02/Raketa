/**
 * Step six of onboarding's second part: **how far will you travel?**
 *
 * It comes immediately after *where do you play*, so the question makes sense when it
 * arrives: a distance is a distance *from* somewhere, and the screen before this one is
 * where that somewhere was given.
 *
 * **The title asks about the search, not about the journey.** *How far will you travel* was
 * a question about a commitment nobody is held to; the number is the edge of a search and
 * the weighting on a proposal, and a player who answered the old question honestly would
 * have set it lower than they wanted.
 *
 * **The title is the whole of what the screen says.** The line under it and the note under
 * the slider are both gone: the title asks the question, the figure answers it, and the
 * plain-word reading beneath the figure (*across your town*) is what a distance means to
 * somebody who does not think in kilometres. `stepCopy('radius').asks` is still the table's
 * entry for this step — the chrome of all six is one table — and this screen no longer
 * draws it.
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
 * editor will obey these rules from a screen that looks nothing like this one. **That screen
 * exists now** — the You tab's *How far to look* (ADR-0179 §2) — and the slider the two share
 * is `SearchRadiusControl`; what this step keeps is the seeding below and its *Continue*.
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
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { openingRadius } from '../domain/searchRadius';
import { stepAfter } from '../domain/socialSteps';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileDraft } from '../store/profileDraft.store';

import { SearchRadiusControl } from './SearchRadiusControl';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

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
      {/* Paused, not loading: `networkMode: 'online'` holds a query rather than failing it,
          so an offline player would otherwise watch a spinner forever. */}
      {options.fetchStatus === 'paused' ? (
        <Note variant="amber">{offlineMessage('resumes')}</Note>
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
        // Every move writes through to the draft: walking on and back finds the number the
        // player set, and the commit carries it.
        <SearchRadiusControl
          radius={radius}
          bounds={bounds}
          onChange={(searchRadiusKm) => answer({ searchRadiusKm })}
        />
      )}
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
});

/**
 * Step seven of onboarding's second part: **who do you want to play with?**
 *
 * Two controls and one decision. The first asks the player their own answer; the second
 * asks who they are willing to be matched with, and the second is unanswerable in isolation
 * — which is the same relationship *where do you play* and *how far out* have, and the
 * reason those are two steps and these are one. Splitting them would be an eighth screen
 * carrying a radio group.
 *
 * It sits after the radius rather than beside the tags, and that is the order's decision
 * (`socialSteps`): the tags step says what kind of player somebody is, and the week, the
 * area, the radius and this one narrow who the platform will put in front of them.
 *
 * ## The preference has a cost, and the screen says it at the moment of the press
 *
 * The gate is **mutual**
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 * Narrowing does not only filter what a player sees — it hides them from the excluded side
 * entirely, including from people who searched for anybody. That half is the one nobody
 * would guess, and **learning it from an empty inbox is not acceptable**, so it is rendered
 * the moment a narrowing option is chosen and disappears when it is widened again.
 *
 * The rule that decides whether there is a cost is `reachOf`'s, the sentence is
 * `genderPresentation`'s, and the two groups themselves are `GenderControls` — which is the
 * split the five steps before it made, and for the reason they made it: the profile editor
 * obeys these rules from a screen that looks nothing like this one. *Who you play with* on
 * the You tab is that screen, and it draws the same two groups under a *Save* each
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What is left here is the onboarding around them.
 *
 * ## Required, and pre-answered in exactly one place
 *
 * **Nothing about the player is pre-selected.** The continue is closed until they answer,
 * because there is no answer here the product may give on their behalf — `prefer not to
 * say` is a choice somebody makes, never a default somebody is given.
 *
 * **The preference is the opposite, and deliberately.** It opens on *Anyone* because that
 * is what every player already holds: unconstrained is not a blank to be filled but the
 * value a profile carries until somebody narrows it. A player who continues without
 * touching the second control has answered it, at the widest setting, which is the only
 * default that takes nothing away from anybody.
 *
 * ## Nothing here reaches anybody else
 *
 * No response that describes one player to another carries a gender value out (ADR-0096 §6):
 * neither answer is rendered on a card, a profile or a shortlist. The one shape that carries
 * them is the owner's own profile read (ADR-0179 §4), so that *Who you play with* can open on
 * the answer already given — and **the scope note that says what the answers are used for is
 * the first thing on the screen**, above both questions rather than between them. It is one
 * claim covering both answers, and a player weighing whether to answer at all is weighing it
 * before the first press, not after it.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Note, theme } from '@/shared/ui';

import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import { GenderControl, GenderPreferenceControl } from './GenderControls';
import {
  GENDER_CONTINUE_BLOCKED_HINT,
  GENDER_SCOPE,
  PREFERENCE_IS_DURABLE,
} from './genderPresentation';
import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';

export function SocialGenderStep() {
  const router = useRouter();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's.
  const next = stepAfter('gender');
  const gender = draft?.gender;

  return (
    <SocialStepLayout
      step="gender"
      action={
        next === undefined ? null : (
          <Button
            label="Continue"
            size="lg"
            // Closed on the answer about the player and on nothing else. The preference
            // below cannot hold this shut — it is already answered, at its widest.
            disabled={gender === undefined}
            onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
            accessibilityHint={
              gender === undefined
                ? GENDER_CONTINUE_BLOCKED_HINT
                : `Goes to ${stepCopy(next).title}`
            }
          />
        )
      }
    >
      {/* At the top, above the first question rather than between the two.

          `info`, because it explains what the product does with the answers rather than
          reporting a status about something the player just did (1.3). It moved up here
          because a player deciding whether to answer at all decides that **before** they
          press anything — a reassurance underneath the control they have already used
          arrives after the moment it was for — and because it is true of the preference
          below as much as of the answer above, which it could not claim from between them. */}
      <Note variant="info">{GENDER_SCOPE}</Note>

      {/* Each group a step down from what is above it — the step's own rhythm, which the
          tab does not share because there each group has a card of its own. */}
      <View style={s.section}>
        <GenderControl gender={gender} onChange={(value) => answer({ gender: value })} />
      </View>

      {/* Never `undefined`: the draft holds `any` from the moment the part is entered, so
          there is no "not answered yet" state for the control to draw — and no draft at all
          is the part not entered, which `useSocialStepAdmission` has already refused. */}
      {draft === undefined ? null : (
        <View style={s.section}>
          <GenderPreferenceControl
            preference={draft.genderPreference}
            onChange={(value) => answer({ genderPreference: value })}
          />
        </View>
      )}

      <Text style={s.smallPrint}>{PREFERENCE_IS_DURABLE}</Text>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  section: { paddingTop: theme.space.sm },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
});

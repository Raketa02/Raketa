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
 * `genderPresentation`'s, and what is left here is what a player sees and touches — the
 * same split the five steps before it made, and for the reason they made it: the profile
 * editor will obey these rules from a screen that looks nothing like this one.
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
 * ## Nothing here comes back
 *
 * No response shape in this app carries a gender value out (ADR-0096 §6), so this screen is
 * the only place in the app either value is ever seen. It is not rendered on a card, a
 * profile or a shortlist, and **the scope note that says so is the first thing on the
 * screen** — above both questions rather than between them. It is one claim covering both
 * answers, and a player weighing whether to answer at all is weighing it before the first
 * press, not after it.
 */

import { useRouter } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Note, theme } from '@/shared/ui';

import { GENDERS, GENDER_PREFERENCES, reachOf, costsReach } from '../domain/gender';
import { stepAfter } from '../domain/socialSteps';
import { useProfileDraft } from '../store/profileDraft.store';

import {
  GENDER_CONTINUE_BLOCKED_HINT,
  GENDER_HEADING,
  GENDER_SCOPE,
  PREFERENCE_HEADING,
  PREFERENCE_IS_DURABLE,
  PREFER_NOT_TO_SAY_COST,
  genderLabel,
  preferenceLabel,
  reachNote,
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
  // Never `undefined`: the draft holds `any` from the moment the part is entered, so there
  // is no "not answered yet" state for this control to draw.
  const preference = draft?.genderPreference;
  const reach = preference === undefined ? undefined : reachOf(preference);
  const note = reach === undefined ? undefined : reachNote(reach);

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

      <Text style={s.label}>{GENDER_HEADING}</Text>

      {/* Stacked full-width buttons, not chips: a chip is a filter over content a player can
          already see (6.2), and these are the answers to the screen's question. The chosen
          one is `dark` and the rest `secondary` — a luminance inversion — and `selected` is
          announced by all three, because *not chosen* and *not a choice* are different
          things to be told. Neither is `primary`: coral is the one accent and the continue
          below has it. */}
      <View style={s.answers}>
        {GENDERS.map((value) => (
          <Button
            key={value}
            label={genderLabel(value)}
            size="lg"
            variant={gender === value ? 'dark' : 'secondary'}
            selected={gender === value}
            onPress={() => answer({ gender: value })}
          />
        ))}
      </View>

      {/* The one answer that costs its holder reach, said only when it is the one given.
          `amber`: nothing has gone wrong and nothing is lost — it is a consequence of a
          choice that can be changed on this screen, right now. */}
      {gender !== undefined && costsReach(gender) ? (
        <Note variant="amber">{PREFER_NOT_TO_SAY_COST}</Note>
      ) : null}

      <Text style={s.label}>{PREFERENCE_HEADING}</Text>

      <View style={s.answers}>
        {GENDER_PREFERENCES.map((value) => (
          <Button
            key={value}
            label={preferenceLabel(value)}
            size="lg"
            variant={preference === value ? 'dark' : 'secondary'}
            selected={preference === value}
            onPress={() => answer({ genderPreference: value })}
          />
        ))}
      </View>

      {/* The mutuality cost. **This is the sentence the record requires**, and it is here
          rather than after the commit because a player who learned it from a quiet inbox
          would have been told at the one moment it could not help them. `amber` for the
          reason above: it is reversible, and the control that reverses it is directly
          above. */}
      {note === undefined ? null : <Note variant="amber">{note}</Note>}

      <Text style={s.smallPrint}>{PREFERENCE_IS_DURABLE}</Text>
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  // `flab`, not `eyebrow`: each of these labels a control the player is about to operate
  // rather than a region they are reading, and the two are not interchangeable.
  label: {
    ...theme.type.flab,
    color: theme.color.ink,
    textTransform: 'uppercase',
    marginTop: theme.space.sm,
  },
  // Stacked, not a row: three labels side by side on a phone are three clipped words. The
  // gap is the one between stacked controls in an action group.
  answers: { gap: theme.space.sm },
  smallPrint: { ...theme.type.tiny, color: theme.color.muted },
});

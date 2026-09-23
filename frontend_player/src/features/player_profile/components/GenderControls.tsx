/**
 * The gender step's two radio groups — **the controls, without the onboarding around them.**
 *
 * The step and the You tab's *Who you play with* draw the same two groups from the same
 * rules: three stacked answers under *About you* with the cost line where the one answer that
 * is not free is chosen, and three under *Who we should match you with* with the reach
 * sentence the moment a narrowing one is. What differs between the two is everything
 * *around* the groups — the step's scope note, its *Continue* and the durable-setting line;
 * the tab's *Save* per group — so each group is here, once, and each screen composes it under
 * its own chrome ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, first consequence).
 *
 * Nothing here decides anything: whether an answer costs reach is `gender.costsReach`'s,
 * whether a preference has a cost is `gender.reachOf`'s, and every word is
 * `genderPresentation`'s. What a press does to the value is the caller's — the step writes
 * the draft, the tab holds one.
 *
 * ## The reach sentence is said at the moment of the press, on both screens
 *
 * The gate is **mutual**
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 * Narrowing does not only filter what a player sees — it hides them from the excluded side
 * entirely, including from people who searched for anybody. That half is the one nobody
 * would guess, and **learning it from an empty inbox is not acceptable**, so it is rendered
 * the moment a narrowing option is chosen and disappears when it is widened again. The tab
 * is the second surface that takes the value, and ADR-0096 owes the player the sentence on
 * every one — which is the reason it is drawn here, under the group, rather than by either
 * screen.
 */

import { StyleSheet, Text, View } from 'react-native';

import { Button, Note, theme } from '@/shared/ui';

import {
  GENDERS,
  GENDER_PREFERENCES,
  costsReach,
  reachOf,
  type Gender,
  type GenderPreference,
} from '../domain/gender';

import {
  GENDER_HEADING,
  PREFERENCE_HEADING,
  PREFER_NOT_TO_SAY_COST,
  genderLabel,
  preferenceLabel,
  reachNote,
} from './genderPresentation';

export interface GenderControlProps {
  /** The answer as held — `undefined` where the question has not been answered. */
  readonly gender: Gender | undefined;
  readonly onChange: (gender: Gender) => void;
}

/**
 * *About you.* Stacked full-width buttons, not chips: a chip is a filter over content a player
 * can already see (6.2), and these are the answers to the group's question. The chosen one is
 * `dark` and the rest `secondary` — a luminance inversion — and `selected` is announced by all
 * three, because *not chosen* and *not a choice* are different things to be told. Neither is
 * `primary`: coral is the one accent and the screen's own control has it.
 */
export function GenderControl({ gender, onChange }: GenderControlProps) {
  return (
    <View style={s.group}>
      <Text style={s.label}>{GENDER_HEADING}</Text>

      <View style={s.answers}>
        {GENDERS.map((value) => (
          <Button
            key={value}
            label={genderLabel(value)}
            size="lg"
            variant={gender === value ? 'dark' : 'secondary'}
            selected={gender === value}
            onPress={() => onChange(value)}
          />
        ))}
      </View>

      {/* The one answer that costs its holder reach, said only when it is the one given.
          `amber`: nothing has gone wrong and nothing is lost — it is a consequence of a
          choice that can be changed on this screen, right now. */}
      {gender !== undefined && costsReach(gender) ? (
        <Note variant="amber">{PREFER_NOT_TO_SAY_COST}</Note>
      ) : null}
    </View>
  );
}

export interface GenderPreferenceControlProps {
  /** Never `undefined`: a profile holds `any` from the moment it exists. */
  readonly preference: GenderPreference;
  readonly onChange: (preference: GenderPreference) => void;
}

/** *Who we should match you with*, and the sentence ADR-0096 requires under it. */
export function GenderPreferenceControl({ preference, onChange }: GenderPreferenceControlProps) {
  const note = reachNote(reachOf(preference));

  return (
    <View style={s.group}>
      <Text style={s.label}>{PREFERENCE_HEADING}</Text>

      <View style={s.answers}>
        {GENDER_PREFERENCES.map((value) => (
          <Button
            key={value}
            label={preferenceLabel(value)}
            size="lg"
            variant={preference === value ? 'dark' : 'secondary'}
            selected={preference === value}
            onPress={() => onChange(value)}
          />
        ))}
      </View>

      {/* The mutuality cost. **This is the sentence the record requires**, and it is here
          rather than after the save because a player who learned it from a quiet inbox
          would have been told at the one moment it could not help them. `amber` for the
          reason above: it is reversible, and the control that reverses it is directly
          above. */}
      {note === undefined ? null : <Note variant="amber">{note}</Note>}
    </View>
  );
}

const s = StyleSheet.create({
  // The gap between a label, its answers and the note under them: the step's own, which is
  // the layout's gap between stacked things.
  group: { gap: theme.space.sm },
  // `flab`, not `eyebrow`: each of these labels a control the player is about to operate
  // rather than a region they are reading, and the two are not interchangeable.
  label: {
    ...theme.type.flab,
    color: theme.color.ink,
    textTransform: 'uppercase',
  },
  // Stacked, not a row: three labels side by side on a phone are three clipped words. The
  // gap is the one between stacked controls in an action group.
  answers: { gap: theme.space.sm },
});

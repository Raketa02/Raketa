/**
 * **Who you play with** — the gender step's two radio groups under the tab's chrome, each a
 * draft until its own *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §4).
 *
 * The two groups are `GenderControls`, exactly as `SocialGenderStep` draws them: *About you*
 * with the cost line where the one answer that is not free is chosen, and *Who we should
 * match you with* with **the reach sentence at the moment of the press** — the sentence
 * ADR-0096 owes the player on every surface that takes the value, and this is the second. What
 * the step said once, on the way in, is not said again: no scope note above, no durable-setting
 * line below.
 *
 * ## Two answers, two saves, two routes
 *
 * Each group is its own card with its own *Save*, because each is its own fact with its own
 * write — `PUT /players/me/gender` and `PUT /players/me/gender-preference`, both no-ops on an
 * unchanged value — and a player who narrows who they play with has not said anything new
 * about themselves. Nothing writes on a press; *Save* is shut while the group's draft is the
 * answer the profile holds, and the two *Save*s are told apart for a listener by a spoken
 * name carrying the group each belongs to. A refused save keeps the draft, says why under the
 * group, and the control that failed is the retry.
 *
 * ## Pre-selected from the read, and one group may open on nothing
 *
 * Both groups open on the owner's own answers off `GET /players/me/profile` — the one shape
 * that carries them (ADR-0179 §4) — because a screen that asks *who should we match you with*
 * with nothing pre-selected is a screen a player cannot trust. The exception is the step's
 * own rule kept: a profile committed before the question existed holds **no** gender, and
 * *About you* then pre-selects nothing rather than *Prefer not to say*, which is an answer
 * somebody gives.
 */

import { useRouter } from 'expo-router';
import { useState, type ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Card, Note, theme } from '@/shared/ui';

import type { Gender, GenderPreference } from '../domain/gender';
import {
  useChangeGender,
  useChangeGenderPreference,
  useProfileSurface,
} from '../hooks/useProfileSurface';

import { GenderControl, GenderPreferenceControl } from './GenderControls';
import { GENDER_HEADING, PREFERENCE_HEADING } from './genderPresentation';
import { ProfileReadStanding } from './ProfileReadStanding';
import {
  LOADING_WHO_YOU_PLAY_WITH,
  SAVE,
  SAVED,
  SAVING,
  WHO_YOU_PLAY_WITH_TITLE,
  groupSaveLabel,
} from './youProfilePresentation';

/**
 * `T` is the group's vocabulary and `H` what the profile holds of it: the whole of `T` for
 * the preference, which a profile always has, and `T | undefined` for the gender, which a
 * profile committed before the question existed does not. Typed per caller so the group is
 * drawn from exactly what it can be — a preference never has to say what it would draw for
 * an absence that cannot happen.
 */
interface SavedGroupProps<T extends string, H extends T | undefined> {
  readonly held: H;
  /** The group's heading: what its *Save* is called beside the other's. */
  readonly group: string;
  /** Send the draft. Called with the answer as the player left it; `onSaved` once it landed. */
  readonly onSave: (value: T, onSaved: () => void) => void;
  readonly isPending: boolean;
  readonly error: AppError | null;
  /** The group, drawn from the draft or the held answer, moving the draft on a press. */
  readonly children: (value: T | H, onChange: (value: T) => void) => ReactNode;
}

/**
 * One group under one *Save*: the draft, whether it differs from what is held, and the button
 * that sends it. The draft is dropped the moment the save lands, so the group and the row's
 * live line are then one read.
 */
function SavedGroup<T extends string, H extends T | undefined>({
  held,
  group,
  onSave,
  isPending,
  error,
  children,
}: SavedGroupProps<T, H>) {
  /** The answer as the player has left it — `undefined` while it is the profile's own. */
  const [draft, setDraft] = useState<T>();
  const value: T | H = draft ?? held;
  const dirty = draft !== undefined && draft !== held;
  const label = dirty ? SAVE : SAVED;

  return (
    <Card style={s.group}>
      {children(value, setDraft)}

      {error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(error)}
        </Note>
      ) : null}

      <Button
        label={label}
        accessibilityLabel={groupSaveLabel(label, group)}
        // Green and saying so while the group's draft is the profile's own — the week's rule,
        // once per group, so the one that was just saved turns green and the other stays as
        // it was.
        variant={dirty ? 'primary' : 'settled'}
        size="lg"
        disabled={!dirty}
        busy={isPending}
        busyLabel={SAVING}
        onPress={() => {
          // Shut while there is no draft, so this is the type's question and not a state's.
          if (draft !== undefined) onSave(draft, () => setDraft(undefined));
        }}
      />
    </Card>
  );
}

export function WhoYouPlayWithScreen() {
  const router = useRouter();
  const profile = useProfileSurface();
  const saveGender = useChangeGender();
  const savePreference = useChangeGenderPreference();

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.yourGames}
      title={WHO_YOU_PLAY_WITH_TITLE}
      onBack={router.back}
    >
      <ProfileReadStanding
        fetchStatus={profile.fetchStatus}
        isPending={profile.isPending}
        error={profile.error}
        onRetry={() => void profile.refetch()}
        loadingLabel={LOADING_WHO_YOU_PLAY_WITH}
      />

      {profile.data === undefined ? null : (
        <View style={s.groups}>
          <SavedGroup<Gender, Gender | undefined>
            held={profile.data.gender}
            group={GENDER_HEADING}
            onSave={(gender, onSaved) => saveGender.mutate(gender, { onSuccess: onSaved })}
            isPending={saveGender.isPending}
            error={saveGender.error}
          >
            {(gender, onChange) => <GenderControl gender={gender} onChange={onChange} />}
          </SavedGroup>

          <SavedGroup<GenderPreference, GenderPreference>
            held={profile.data.genderPreference}
            group={PREFERENCE_HEADING}
            onSave={(preference, onSaved) =>
              savePreference.mutate(preference, { onSuccess: onSaved })
            }
            isPending={savePreference.isPending}
            error={savePreference.error}
          >
            {(preference, onChange) => (
              <GenderPreferenceControl preference={preference} onChange={onChange} />
            )}
          </SavedGroup>
        </View>
      )}
    </ShellScreen>
  );
}

const s = StyleSheet.create({
  // 9 between stacked cards.
  groups: { gap: theme.space.sm },
  // The card's own gap between the group, a refusal and the button under it.
  group: { gap: theme.space.sm },
});

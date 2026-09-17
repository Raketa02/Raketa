/**
 * Step one of onboarding's second part: **what kind of player are you?**
 *
 * Nineteen chips in three groups, of which a player picks between two and six. There is no
 * free-text field anywhere on this screen and there is not going to be one: that is what
 * keeps the product's promise about what it asks (story 22), and it is the reason the
 * vocabulary is closed and served rather than typed.
 *
 * **The screen says nothing above the chips.** The line under the title and the note about
 * what the tags are *for* were both cut: the three group headings already say what each set
 * is about, and a screen of options reads faster with nothing stacked on top of them. The
 * eyebrow still carries the rule — pick two to six — which is the one thing a player has to
 * know before they start pressing.
 *
 * ## Nothing here decides anything, and the picker is not here either
 *
 * The floor, the ceiling and the refusal are `socialTagSelection`'s, with their own tests
 * and no renderer; the vocabulary and both numbers are the server's; the chips under their
 * headings and the press that obeys the bounds are `SocialTagPicker`'s, which the You tab's
 * *Tags* draws too ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2). What is left for this file is the step's own: its chrome, the options' three states,
 * and *Continue*.
 *
 * ## The selection lives in the draft, not in this screen
 *
 * Every press writes through to the part's client-held draft, so walking to step two and
 * back finds the tags still selected — the promise the part makes when it says checking one
 * thing costs you nothing. Nothing is sent anywhere: the draft is in memory until the one
 * commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 */

import { useRouter } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { stepAfter } from '../domain/socialSteps';
import { selectionStanding } from '../domain/socialTagSelection';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileDraft } from '../store/profileDraft.store';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  NO_TAGS_AVAILABLE,
  SOCIAL_TAG_CEILING_BODY,
  socialTagCeilingTitle,
  socialTagsContinueLabel,
  socialTagsEyebrow,
} from './socialTagPresentation';
import { SocialTagPicker, useSocialTagPicker } from './SocialTagPicker';

export function SocialTagsStep() {
  const router = useRouter();
  const options = useProfileOptions();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);

  // Where continuing leads is the step order's answer, not this screen's. There is exactly
  // one list of six and it is `SOCIAL_STEPS`; a literal here would survive a reordering of
  // it and quietly keep pointing at photos.
  const next = stepAfter('tags');
  const bounds = options.data?.socialTagSelection;
  const groups = options.data?.socialTagGroups ?? [];
  const selection = draft?.socialTagIds ?? [];
  const standing = bounds === undefined ? undefined : selectionStanding(selection, bounds);
  const picker = useSocialTagPicker({
    selection,
    bounds,
    onChange: (socialTagIds) => answer({ socialTagIds }),
  });

  return (
    <SocialStepLayout
      step="tags"
      eyebrow={socialTagsEyebrow(bounds)}
      action={
        standing === undefined || next === undefined ? null : (
          <>
            {/* Pinned to the action bar rather than left above nineteen chips: a player who
                pressed a seventh may be scrolled to the bottom of the third group, and a
                refusal they have to scroll back up to find is a screen that did nothing.
                `alert` announces it as well, for whoever is not looking at either. */}
            {picker.refused && bounds !== undefined ? (
              <Note variant="amber" accessibilityRole="alert" title={socialTagCeilingTitle(bounds)}>
                {SOCIAL_TAG_CEILING_BODY}
              </Note>
            ) : null}

            <Button
              label={socialTagsContinueLabel(standing)}
              size="lg"
              disabled={standing.kind !== 'ready'}
              onPress={() => router.replace(SOCIAL_STEP_PATH[next])}
              accessibilityHint={`Goes to ${stepCopy(next).title}`}
            />
          </>
        )
      }
    >
      {/* Paused, not loading: `networkMode: 'online'` holds a query rather than failing it,
          so an offline player would otherwise watch a spinner forever. */}
      {options.fetchStatus === 'paused' ? (
        <Note variant="amber">{offlineMessage('resumes')}</Note>
      ) : null}

      {options.isPending && options.fetchStatus !== 'paused' ? (
        <ActivityIndicator accessibilityLabel="Loading tags" color={theme.color.muted} />
      ) : null}

      {options.error !== null ? (
        <View style={s.failure}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(options.error)}
          </Note>
          <Button label="Try again" variant="secondary" onPress={() => void options.refetch()} />
        </View>
      ) : null}

      {options.isSuccess && groups.length === 0 ? (
        <Note variant="amber">{NO_TAGS_AVAILABLE}</Note>
      ) : null}

      <SocialTagPicker groups={groups} selection={selection} onPressTag={picker.pressTag} />
    </SocialStepLayout>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
});

/**
 * **Tags** — the tags step as it is, under the tab's chrome, a draft until *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The eyebrow carries the served rule under the group's title — *On your card · Pick 2 to 8*
 * — the title is the step's question, the three groups of chips and the press that obeys the
 * bounds are `SocialTagPicker`'s, and the ceiling note is pinned above the button as the
 * step pins it. The step's *Continue* is *Save*, shut under the floor with the step's own
 * words (`socialTagsSaveLabel`) and shut again while the draft is the selection the profile
 * already holds — by membership, never by order, because the profile holds its tags in the
 * vocabulary's order whatever order they were pressed in.
 *
 * ## A draft until the button
 *
 * The picker opens on the tags the profile holds and every press moves a draft of them;
 * nothing is written on a press. *Save* sends one `PUT /players/me/social-tags`, and what the
 * picker then draws is **the route's answer** written into the cache — the vocabulary's order
 * — never the draft echoed back. The draft is dropped the moment the save lands, so the picker
 * and the row's live line are then one read.
 *
 * ## Two reads before the chips
 *
 * The vocabulary and the bounds come from `GET /player-profile/options`, and the selection
 * from `GET /players/me/profile`; the chips are drawn once both are in, because chips with no
 * bounds have no ceiling to refuse at and a selection with no vocabulary has nothing to light.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { ShellScreen } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Note } from '@/shared/ui';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import { sameSelection, selectionStanding } from '../domain/socialTagSelection';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useChangeSocialTags, useProfileSurface } from '../hooks/useProfileSurface';

import { ProfileReadStanding } from './ProfileReadStanding';
import { stepCopy } from './socialStepPresentation';
import {
  NO_TAGS_AVAILABLE,
  SOCIAL_TAG_CEILING_BODY,
  socialTagCeilingTitle,
  socialTagsRule,
  socialTagsSaveLabel,
} from './socialTagPresentation';
import { SocialTagPicker, useSocialTagPicker } from './SocialTagPicker';
import {
  LOADING_TAGS,
  LOADING_YOUR_TAGS,
  SAVING,
  onYourCardEyebrow,
} from './youProfilePresentation';

export function TagsScreen() {
  const router = useRouter();
  const options = useProfileOptions();
  const profile = useProfileSurface();
  const save = useChangeSocialTags();
  /** The tags as the player has left them — `undefined` while they are the profile's own. */
  const [draft, setDraft] = useState<readonly SocialTagId[]>();

  const bounds = options.data?.socialTagSelection;
  const groups = options.data?.socialTagGroups ?? [];
  const held = profile.data?.socialTagIds;
  const selection = draft ?? held;
  const dirty = held !== undefined && draft !== undefined && !sameSelection(draft, held);
  const standing =
    bounds === undefined || selection === undefined
      ? undefined
      : selectionStanding(selection, bounds);
  const picker = useSocialTagPicker({ selection: selection ?? [], bounds, onChange: setDraft });

  return (
    <ShellScreen
      eyebrow={onYourCardEyebrow(bounds === undefined ? undefined : socialTagsRule(bounds))}
      title={stepCopy('tags').title}
      onBack={router.back}
      action={
        standing === undefined || selection === undefined || bounds === undefined ? undefined : (
          <>
            {/* Pinned above the button rather than left above twenty-seven chips, and announced
                — the step's reason. */}
            {picker.refused ? (
              <Note variant="amber" accessibilityRole="alert" title={socialTagCeilingTitle(bounds)}>
                {SOCIAL_TAG_CEILING_BODY}
              </Note>
            ) : null}

            {save.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(save.error)}
              </Note>
            ) : null}

            <Button
              label={socialTagsSaveLabel(standing, dirty)}
              // Green only when the label is *Saved*: a selection under the floor is shut
              // with the step's own words, and those are an ask, not a fact settled.
              variant={dirty || standing.kind !== 'ready' ? 'primary' : 'settled'}
              size="lg"
              disabled={standing.kind !== 'ready' || !dirty}
              busy={save.isPending}
              busyLabel={SAVING}
              onPress={() =>
                // The cache holds the route's order by the time this runs; dropping the
                // draft is what lets the picker draw it.
                save.mutate(selection, { onSuccess: () => setDraft(undefined) })
              }
            />
          </>
        )
      }
    >
      <ProfileReadStanding
        fetchStatus={options.fetchStatus}
        isPending={options.isPending}
        error={options.error}
        onRetry={() => void options.refetch()}
        loadingLabel={LOADING_TAGS}
      />

      {/* Once, not twice: with the options in, the profile is the only read left to wait on. */}
      {options.data === undefined ? null : (
        <ProfileReadStanding
          fetchStatus={profile.fetchStatus}
          isPending={profile.isPending}
          error={profile.error}
          onRetry={() => void profile.refetch()}
          loadingLabel={LOADING_YOUR_TAGS}
        />
      )}

      {options.isSuccess && groups.length === 0 ? (
        <Note variant="amber">{NO_TAGS_AVAILABLE}</Note>
      ) : null}

      {selection === undefined ? null : (
        <SocialTagPicker groups={groups} selection={selection} onPressTag={picker.pressTag} />
      )}
    </ShellScreen>
  );
}

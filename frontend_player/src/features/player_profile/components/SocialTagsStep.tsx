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
 * ## Nothing here decides anything
 *
 * The floor, the ceiling and the refusal are `socialTagSelection`'s, with their own tests
 * and no renderer; the vocabulary and both numbers are the server's. What is left for this
 * file is what a player sees — which is deliberate, because the profile editor will obey
 * exactly the same rules from a screen that looks nothing like this one.
 *
 * ## The selection lives in the draft, not in this screen
 *
 * Every press writes through to the part's client-held draft, so walking to step two and
 * back finds the tags still selected — the promise the part makes when it says checking one
 * thing costs you nothing. Nothing is sent anywhere: the draft is in memory until the one
 * commit at the end of the part
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
 *
 * ## The chips wrap; they do not scroll sideways
 *
 * Design-system Part 8 rails chips horizontally, and that pattern is for *filters* over
 * content the player can already see. Here the chips **are** the content, and a rail would
 * hide most of nineteen options off the right edge of a step whose whole job is to show
 * them. Wrapping is also what Part 13 asks for when the OS text size grows.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { Button, Chip, Note, theme } from '@/shared/ui';
import {
  socialTagGroupHeading,
  socialTagLabel,
  socialTagName,
} from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type { SocialTagGroup } from '../domain/SocialTag';
import { stepAfter } from '../domain/socialSteps';
import { selectionStanding, toggleSocialTag } from '../domain/socialTagSelection';
import { useProfileOptions } from '../hooks/useProfileOptions';
import { useProfileDraft } from '../store/profileDraft.store';

import { SocialStepLayout } from './SocialStepLayout';
import { SOCIAL_STEP_PATH } from './socialStepRoutes';
import { stepCopy } from './socialStepPresentation';
import {
  socialTagCeilingTitle,
  socialTagsContinueLabel,
  socialTagsEyebrow,
} from './socialTagPresentation';

export function SocialTagsStep() {
  const router = useRouter();
  const options = useProfileOptions();
  const draft = useProfileDraft((state) => state.draft);
  const answer = useProfileDraft((state) => state.answer);
  /**
   * The refusal is the one thing this screen holds of its own, and it is a *fact about the
   * last press* rather than a state a player is in — so it is cleared by the next press
   * that changes anything, including the removal that makes room.
   */
  const [refused, setRefused] = useState(false);

  // Where continuing leads is the step order's answer, not this screen's. There is exactly
  // one list of six and it is `SOCIAL_STEPS`; a literal here would survive a reordering of
  // it and quietly keep pointing at photos.
  const next = stepAfter('tags');
  const bounds = options.data?.socialTagSelection;
  const groups = options.data?.socialTagGroups ?? [];
  const selection = draft?.socialTagIds ?? [];
  const standing = bounds === undefined ? undefined : selectionStanding(selection, bounds);

  const pressTag = (tagId: SocialTagId) => {
    if (bounds === undefined) return;

    const change = toggleSocialTag(selection, tagId, bounds);
    if (change.kind === 'refused') {
      setRefused(true);
      return;
    }
    setRefused(false);
    answer({ socialTagIds: change.selection });
  };

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
            {refused && bounds !== undefined ? (
              <Note variant="amber" accessibilityRole="alert" title={socialTagCeilingTitle(bounds)}>
                Nothing changed. Remove one you have already picked to make room for another.
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
        <Note variant="amber">No tags are available right now. Try again later.</Note>
      ) : null}

      {groups.map((group) => (
        <TagGroup key={group.group} group={group} selection={selection} onPressTag={pressTag} />
      ))}
    </SocialStepLayout>
  );
}

interface TagGroupProps {
  readonly group: SocialTagGroup;
  readonly selection: readonly SocialTagId[];
  readonly onPressTag: (tagId: SocialTagId) => void;
}

/**
 * One group, under a heading naming what it is about.
 *
 * The heading is `flab` rather than the eyebrow role: it labels chips a player is about to
 * OPERATE, not a region they are reading, and design-system 3.3 says the two are not
 * interchangeable.
 */
function TagGroup({ group, selection, onPressTag }: TagGroupProps) {
  return (
    <View style={s.group}>
      <Text style={s.heading}>{socialTagGroupHeading(group.group)}</Text>
      <View style={s.chips}>
        {group.tagIds.map((tagId) => (
          <Chip
            key={tagId}
            label={socialTagLabel(tagId)}
            // The words without the glyph: the emoji is what makes nineteen chips findable
            // by eye, and reading its name aloud would announce the layout, not the choice.
            accessibilityLabel={socialTagName(tagId)}
            selected={selection.includes(tagId)}
            onPress={() => onPressTag(tagId)}
          />
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
  group: { gap: theme.space.xs, paddingTop: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  // The gap the design system gives a row of chips (Part 8), applied in both directions
  // because these wrap.
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});

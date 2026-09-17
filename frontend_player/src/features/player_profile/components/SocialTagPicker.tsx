/**
 * **The tag picker, as the step draws it** — three groups of chips under their `flab`
 * headings — for the two screens that pick tags: the onboarding step, and the You tab's
 * *Tags* ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * What a press does is the caller's: the step writes the draft, the tab holds one. The floor,
 * the ceiling and the refusal are `socialTagSelection`'s, applied by `useSocialTagPicker`
 * beside this, which both callers drive so a seventh press refuses identically on each.
 *
 * ## The chips wrap; they do not scroll sideways
 *
 * Design-system Part 8 rails chips horizontally, and that pattern is for *filters* over
 * content the player can already see. Here the chips **are** the content, and a rail would
 * hide most of nineteen options off the right edge of a screen whose whole job is to show
 * them. Wrapping is also what Part 13 asks for when the OS text size grows.
 */

import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Chip, theme } from '@/shared/ui';
import {
  socialTagGroupHeading,
  socialTagLabel,
  socialTagName,
} from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import type { SocialTagGroup } from '../domain/SocialTag';
import { toggleSocialTag, type SocialTagSelectionBounds } from '../domain/socialTagSelection';

export interface SocialTagPickerRule {
  readonly selection: readonly SocialTagId[];
  /** `undefined` while the bounds are on their way: a press then changes nothing. */
  readonly bounds: SocialTagSelectionBounds | undefined;
  readonly onChange: (selection: readonly SocialTagId[]) => void;
}

/**
 * A press on a chip, under the served bounds — and the one thing a picker holds of its own.
 *
 * The refusal is a *fact about the last press* rather than a state a player is in, so it is
 * cleared by the next press that changes anything, including the removal that makes room.
 */
export function useSocialTagPicker({ selection, bounds, onChange }: SocialTagPickerRule) {
  const [refused, setRefused] = useState(false);

  const pressTag = (tagId: SocialTagId) => {
    if (bounds === undefined) return;

    const change = toggleSocialTag(selection, tagId, bounds);
    if (change.kind === 'refused') {
      setRefused(true);
      return;
    }
    setRefused(false);
    onChange(change.selection);
  };

  return { refused, pressTag };
}

export interface SocialTagPickerProps {
  readonly groups: readonly SocialTagGroup[];
  readonly selection: readonly SocialTagId[];
  readonly onPressTag: (tagId: SocialTagId) => void;
}

export function SocialTagPicker({ groups, selection, onPressTag }: SocialTagPickerProps) {
  return (
    <>
      {groups.map((group) => (
        <TagGroup key={group.group} group={group} selection={selection} onPressTag={onPressTag} />
      ))}
    </>
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
  group: { gap: theme.space.xs, paddingTop: theme.space.xs },
  heading: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  // The gap the design system gives a row of chips (Part 8), applied in both directions
  // because these wrap.
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});

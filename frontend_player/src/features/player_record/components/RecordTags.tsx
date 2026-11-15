/**
 * **The record's tag row, as one element** — their live tags, in whichever register the caller's
 * overlap licenses (`recordTagRow`), spoken as the row says them (`socialTagsLabel`). Nothing where
 * there is nothing to say.
 *
 * The record sheet draws it under *Full record*; **the vibe sheet** (#803; the Home rows screens §6.3)
 * draws it whole, the tags the two share green and reading *· you too* — *as on the record*, so it is
 * this one row and not a second spelling of it.
 */

import { View } from 'react-native';

import { SocialTagRow } from '@/shared/ui';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import { recordTagRow } from '../domain/tagRow';

import { socialTagsLabel } from './recordPresentation';

export interface RecordTagsProps {
  /** The record's own tags, live. */
  readonly tags: readonly SocialTagId[];
  /** Which of them the reader also holds, where a comparison stands behind the surface. */
  readonly overlap?: SocialTagOverlap;
}

export function RecordTags({ tags, overlap }: RecordTagsProps) {
  const row = recordTagRow(tags, overlap);
  const label = socialTagsLabel(row);
  if (label === '') return null;
  return (
    <View accessible accessibilityLabel={label} testID="record-tags">
      <SocialTagRow row={row} />
    </View>
  );
}

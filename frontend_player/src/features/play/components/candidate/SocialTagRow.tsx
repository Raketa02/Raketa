/**
 * The competitive card's **Social tag row** — up to six of what the candidate published, with
 * the ones the searcher also chose tinted, and one amber sentence where nothing is shared.
 *
 * Four answers arrive from `domain/socialTagOverlap` and this component draws them; it decides
 * nothing ([#311](https://github.com/Raketa02/Raketa/issues/311)). The switch is exhaustive
 * over the union for the reason the union exists: *we do not know* and *there is nothing* are
 * different sentences, and a component reading a list plus a flag would eventually draw the
 * claim in the case that has not earned it.
 *
 * ## Two variants of `Tag`, and neither of them is a chip
 *
 * A shared tag is `ok` — mint on `mintSoft`, [6.4](../../../../../docs/design-system.md#64-tag--the-status-pill)'s
 * settled variant, which is *green* in the designs' word — and the rest are `base`. The amber
 * line is `warn`, which is 2.2's *watch this, reversible, not yet wrong*: nobody has done
 * anything wrong by having different tags, and it is the mildest thing the palette says.
 *
 * **Tags, not chips.** [6.4](../../../../../docs/design-system.md#64-tag--the-status-pill):
 * *a pressable pill is a chip*, and nothing here is pressable — the row states what somebody
 * published, and the surface that lets you act on a tag is not this one.
 *
 * **Colour is never the cue.** Each shared tag carries `· you too` in its own words, so the
 * tint is the second copy of a fact the label already states — the same order the marked
 * card's border takes ([Part 13](../../../../../docs/design-system.md#part-13--accessibility)).
 * `socialTagChip` owns that marker and the note on what the largest text sizes do to it.
 *
 * ## The row announces nothing of its own
 *
 * §20.1: one accessibility element per action, and everything with no action merges into the
 * nearest action above it. A tag has no action and the card body does, so the whole row merges
 * into it — which is why every tag drawn here is also a clause in `candidateCardLabel`, and why
 * the rule is *do not draw a tag the label does not speak* rather than *give each tag a name*.
 */

import { StyleSheet, View } from 'react-native';

import { Tag, theme } from '@/shared/ui';

import type { SocialTagOverlap } from '../../domain/socialTagOverlap';
import { NO_TAGS_IN_COMMON, socialTagChip } from '../playerCardPresentation';

export interface SocialTagRowProps {
  readonly row: SocialTagOverlap;
}

export function SocialTagRow({ row }: SocialTagRowProps) {
  switch (row.kind) {
    case 'hidden':
      return null;

    case 'none-in-common':
      // In the row's place rather than beneath it: six untinted tags under a line saying none
      // of them matched is the card answering one question twice, and the tags themselves are
      // read in full on the surface whose job they are.
      return (
        <View style={s.row}>
          <Tag label={NO_TAGS_IN_COMMON} variant="warn" />
        </View>
      );

    case 'shared':
      return (
        <View style={s.row}>
          {row.tags.map((tag) => (
            <Tag key={tag.id} label={socialTagChip(tag)} variant={tag.shared ? 'ok' : 'base'} />
          ))}
        </View>
      );

    case 'unknown':
      return (
        <View style={s.row}>
          {row.tags.map((id) => (
            <Tag key={id} label={socialTagChip({ id, shared: false })} />
          ))}
        </View>
      );
  }
}

const s = StyleSheet.create({
  // It wraps, because six tags never fit on one line and the longest of them fills most of a
  // card on its own — the same reason the card's own action row wraps.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});

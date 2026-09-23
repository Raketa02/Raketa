/**
 * **The Social tag row** — up to six of what somebody published, with the ones the reader also
 * chose tinted, and one amber sentence where nothing is shared.
 *
 * Four answers arrive as a `SocialTagOverlap` and this component draws them; it decides nothing
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)). The switch is exhaustive over the
 * union for the reason the union exists: *we do not know* and *there is nothing* are different
 * sentences, and a component reading a list plus a flag would eventually draw the claim in the
 * case that has not earned it.
 *
 * ## Two variants of `Tag`, and neither of them is a chip
 *
 * A shared tag is `ok` — mint on `mintSoft`,
 * [6.4](../../../docs/design-system.md#64-tag--the-status-pill)'s settled variant, which is
 * *green* in the designs' word — and the rest are `base`. The amber line is `warn`, which is
 * 2.2's *watch this, reversible, not yet wrong*: nobody has done anything wrong by having
 * different tags, and it is the mildest thing the palette says.
 *
 * **Tags, not chips.** [6.4](../../../docs/design-system.md#64-tag--the-status-pill):
 * *a pressable pill is a chip*, and nothing here is pressable — the row states what somebody
 * published, and the surface that lets you act on a tag is not this one.
 *
 * **Colour is never the cue.** Each shared tag carries `· you too` in its own words, so the
 * tint is the second copy of a fact the label already states — the same order the marked
 * card's border takes ([Part 13](../../../docs/design-system.md#part-13--accessibility)).
 * `socialTagChip` owns that marker and the note on what the largest text sizes do to it.
 *
 * ## On the deck card the pair is volt and on-dark
 *
 * The deck card draws the same row over its wash
 * ([ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7), where `mintSoft` and `line2` are two pale pills on a dark ground with nothing to tell
 * them apart. `onDark` swaps the pair for the two variants the dark surfaces already have — a
 * shared tag is `volt`, a fill anywhere and the one the mocks draw, and the rest are `onDark` —
 * and changes nothing else: the same four answers, the same order the caller hands over, the
 * same words. The amber sentence keeps its own variant, which reads on either ground.
 *
 * ## The row announces nothing of its own
 *
 * §20.1: one accessibility element per action, and everything with no action merges into the
 * nearest action above it. A tag has no action, so the whole row merges into whatever action
 * contains it — which is why every tag drawn here is also a clause in the containing surface's
 * spoken name, and why the rule that ships with the row is *do not draw a tag the label does
 * not speak* rather than *give each tag a name*.
 *
 * ## Why this is `shared/ui` and not the candidate card's own component
 *
 * It was the competitive card's. The record sheet draws the same row from its own read
 * ([#373](https://github.com/Raketa02/Raketa/issues/373)), so the row came below both features
 * rather than being copied or imported sideways out of `features/play/`. **The rule stayed
 * behind**: `features/play/domain/socialTagOverlap` reads one of these four answers off a
 * candidate row, which is a search result and Play's alone. A caller computes the overlap and
 * hands the value down.
 */

import { StyleSheet, View } from 'react-native';

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import { NO_TAGS_IN_COMMON, socialTagChip } from '@/shared/vocabulary/socialTagPresentation';

import { Tag } from './Tag';
import { theme } from './theme';

export interface SocialTagRowProps {
  readonly row: SocialTagOverlap;
  /** Over a dark ground — the deck card's wash — where the pair is `volt` and `onDark`. */
  readonly onDark?: boolean;
}

export function SocialTagRow({ row, onDark = false }: SocialTagRowProps) {
  const shared = onDark ? 'volt' : 'ok';
  const rest = onDark ? 'onDark' : 'base';

  switch (row.kind) {
    case 'hidden':
      return null;

    case 'none-in-common':
      // In the row's place rather than beneath it: six untinted tags under a line saying none
      // of them matched is the surface answering one question twice, and the tags themselves
      // are read in full on the surface whose job they are.
      return (
        <View style={s.row}>
          <Tag label={NO_TAGS_IN_COMMON} variant="warn" />
        </View>
      );

    case 'shared':
      return (
        <View style={s.row}>
          {row.tags.map((tag) => (
            <Tag key={tag.id} label={socialTagChip(tag)} variant={tag.shared ? shared : rest} />
          ))}
        </View>
      );

    case 'unknown':
      return (
        <View style={s.row}>
          {row.tags.map((id) => (
            <Tag key={id} label={socialTagChip({ id, shared: false })} variant={rest} />
          ))}
        </View>
      );
  }
}

const s = StyleSheet.create({
  // It wraps, because six tags never fit on one line and the longest of them fills most of a
  // card on its own — the same reason a card's own action row wraps.
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs },
});

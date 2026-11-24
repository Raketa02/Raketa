/**
 * **The tags two players share, as a tile's green chips** — as many whole chips as fit in **three
 * lines**, the last place a dashed *+N more* when more remain
 * ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows screens §6.2; the README's
 * override 8; home rows 20, 22–22.3, 24). Three lines on Home's tile and in See all alike.
 *
 * ## Measured, never guessed
 *
 * How many fit is a fact about this screen — the column's width, each tag's words, the text size —
 * so it is **read off the layout**: every chip and every *+N more* the tile could say is laid out once,
 * unseen, beside the line it would stand in, and `tagsThatFit` answers from their widths. **Nothing is
 * drawn until all of them are in**, so a chip never stands for a frame and then leaves; the three
 * lines' room is kept from the first frame, so the tile never grows under the reader.
 *
 * The chips are 6.4's `ok` tag — mint, green bold words — with the tag's emoji, as on the record;
 * *+N more* is its `more` tag. None is a control, and none is spoken: the tile's name says every tag
 * the two share (`vibeTileLabel`).
 */

import { useState } from 'react';
import { StyleSheet, View, type LayoutChangeEvent } from 'react-native';

import { TAG_HEIGHT, Tag, theme } from '@/shared/ui';
import { socialTagLabel } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';

import { moreTags } from './discoveryCopy';
import { tagsThatFit } from './tagFit';

/** The cap (the screens §6.2). */
const LINES = 3;

/** Between chips, both ways — the record's tag row's gap. */
const GAP = theme.space.xs;

/** **The three lines' room**, kept from the first frame — and held by a tile's skeleton (#872). */
export const SHARED_TAGS_ROOM = LINES * TAG_HEIGHT + (LINES - 1) * GAP;

export interface SharedTagsProps {
  /** The tags the two share, in the vocabulary's order. */
  readonly tags: readonly SocialTagId[];
}

export function SharedTags({ tags }: SharedTagsProps) {
  const [line, setLine] = useState<number>();
  const [widths, setWidths] = useState<Readonly<Partial<Record<SocialTagId, number>>>>({});
  const [moreWidths, setMoreWidths] = useState<Readonly<Record<number, number>>>({});

  // *+1 more* … — every count the tile could say, which is one fewer than its tags at most.
  const counts = Array.from({ length: Math.max(0, tags.length - 1) }, (_, at) => at + 1);
  const tagWidths = tags.map((id) => widths[id]);
  const countWidths = counts.map((count) => moreWidths[count]);
  // How many chips are drawn whole — none until every width is in.
  const whole =
    line === undefined || tagWidths.includes(undefined) || countWidths.includes(undefined)
      ? undefined
      : tagsThatFit({
          widths: tagWidths as number[],
          moreWidths: countWidths as number[],
          lineWidth: line,
          gap: GAP,
          lines: LINES,
        });

  const widthOf = (event: LayoutChangeEvent) => event.nativeEvent.layout.width;

  return (
    <View
      style={s.room}
      onLayout={(event) => setLine(widthOf(event))}
      testID="shared-tags"
      pointerEvents="none"
    >
      {whole === undefined ? null : (
        <View style={s.lines}>
          {tags.slice(0, whole).map((id) => (
            <View key={id} style={s.chip}>
              <Tag label={socialTagLabel(id)} variant="ok" />
            </View>
          ))}
          {whole < tags.length ? (
            <View style={s.chip}>
              <Tag label={moreTags(tags.length - whole)} variant="more" />
            </View>
          ) : null}
        </View>
      )}

      {/* Every chip and every count, laid out unseen at the line's width, for their widths alone. */}
      <View
        style={s.measuring}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        {tags.map((id) => (
          <View
            key={id}
            style={s.measured}
            testID={`measure-tag-${id}`}
            onLayout={(event) => {
              const width = widthOf(event);
              setWidths((before) => (before[id] === width ? before : { ...before, [id]: width }));
            }}
          >
            <Tag label={socialTagLabel(id)} variant="ok" />
          </View>
        ))}
        {counts.map((count) => (
          <View
            key={count}
            style={s.measured}
            testID={`measure-more-${count}`}
            onLayout={(event) => {
              const width = widthOf(event);
              setMoreWidths((before) =>
                before[count] === width ? before : { ...before, [count]: width },
              );
            }}
          >
            <Tag label={moreTags(count)} variant="more" />
          </View>
        ))}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  // The three lines' room, kept from the first frame — 6.4's own height, three times.
  room: { minHeight: SHARED_TAGS_ROOM },
  lines: { flexDirection: 'row', flexWrap: 'wrap', gap: GAP },
  // A chip is never wider than the line: one that would be is cut by its own ellipsis — the width it
  // was measured at.
  chip: { maxWidth: '100%' },
  // Laid out at the line's width and never seen: a chip wider than the line is cut to it, as it
  // would be drawn.
  measuring: { position: 'absolute', top: 0, left: 0, right: 0, opacity: 0 },
  measured: { position: 'absolute', top: 0, left: 0, maxWidth: '100%' },
});

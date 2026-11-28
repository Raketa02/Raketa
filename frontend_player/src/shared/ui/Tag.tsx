/**
 * The tag, per design-system 6.4 — the status pill.
 *
 * **A tag is never pressable.** A pressable pill is a chip, and the two look close enough
 * that the only thing keeping them apart is this rule: a control that cannot be operated
 * must not offer the affordance of one.
 *
 * A long tag truncates rather than breaking the row it sits in, because a row that reflows
 * because of a status is a row whose layout depends on server copy.
 *
 * ## `more` is the eighth, and it is a **count**, not a state
 *
 * *+2 more* on a Same vibe tile ([#803](https://github.com/Rakieta02/Rakieta/issues/803); the Home rows
 * screens §6.2): the tags a tile had no room for, drawn in the last place its lines leave. **A dashed
 * `line` border on no bed, its words `muted`** — the mocks' (home rows 20, 22.3): it says *there is
 * more of the same*, so it takes none of the six tones, and the dash is what tells it from the tags
 * beside it. Its border stands **in** the padding's first point, so it is exactly as tall and as
 * inset as every tag — a line of chips stays one height, and a width measured is a width drawn.
 *
 * ## `volt` is the seventh, and it is a **fill** rather than a soft
 *
 * The other six are the palette's soft/ink pairs, computed against each other. Volt has no
 * soft and needs none: it is *a fill anywhere and a stroke only on dark*
 * ([2.2](../../../docs/design-system.md#22-accent-and-semantics)), and `ink` on it is
 * **13.96:1** — AAA, and already published in
 * [2.5](../../../docs/design-system.md#25-contrast--computed). So its Rule C pair is
 * computed rather than eyeballed, and it is the one variant whose background is a base
 * colour: a `voltSoft` would be a colour invented to give this tag the shape of the other
 * six, which [15.2](../../../docs/design-system.md#152-adding-a-colour) forbids.
 *
 * **It carries Play's *they want you* signal, and it is why that signal is a tag at all.**
 * The 2026-08-31 amendment narrowed *volt never appears on paper* to the fills, and refused
 * the strokes it had been used for — *"the card's emphasis becoming a tag is what
 * [Part 13](../../../docs/design-system.md#part-13--accessibility) prefers anyway: a border
 * carries no word and this signal has one."* This is that tag.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

/** The *more* tag's dash — `line`'s width on a card, taken out of the padding so the box keeps its size. */
const DASH = 1;

/**
 * **One tag's height** — its line and its padding, every variant alike (`more`'s dash stands inside
 * the padding). For a surface that keeps room for lines of tags before it has laid any out: Same vibe's
 * three lines of chips (#803).
 */
export const TAG_HEIGHT = theme.type.tag.lineHeight + 2 * theme.space.xxs;

export type TagVariant = 'base' | 'ok' | 'hot' | 'warn' | 'bad' | 'volt' | 'onDark' | 'more';

export interface TagProps {
  readonly label: string;
  readonly variant?: TagVariant;
  /**
   * A 6pt square in a sport's identity colour. The dot is decoration — the label beside
   * it always says the same thing, so colour is never the only carrier.
   *
   * **The sport's, and only the sport's — on every surface but one.** A caller reaching for
   * it to carry urgency — the dot going amber as a clock runs down — is asking one token to
   * mean two things, after which it means neither, and it would be colour restating a value
   * the label has already rendered. Urgency is the **whole tag**: `warn` for a live window,
   * `ok` for a settled one, with the word beside it (6.4, Part 13).
   *
   * The one surface is Home's game card, where the dot is **the status's** and the sport is the
   * word beside the pill (`STATUS_INK`; the old loop's Now card's `STAGE_DOT` before it, 6.4 as
   * amended by #413). The argument above holds there too: the sport left the dot for a word, so
   * the token has one meaning on that card.
   */
  readonly dot?: string;
  /** Defaults to `label`. Set it when the word alone is cryptic out of context. */
  readonly accessibilityLabel?: string;
}

export function Tag({ label, variant = 'base', dot, accessibilityLabel }: TagProps) {
  return (
    <View style={[s.tag, SURFACE[variant]]}>
      {dot !== undefined ? (
        <View
          style={[s.dot, { backgroundColor: dot }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      ) : null}
      <Text
        style={[s.label, LABEL[variant]]}
        numberOfLines={1}
        accessibilityLabel={accessibilityLabel}
      >
        {label}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    paddingVertical: theme.space.xxs,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.tag,
    // `alignSelf`, so a tag in a row is its own width rather than the row's.
    alignSelf: 'flex-start',
  },
  // Square, not round: the round form is the sport dot, and the two mean different things.
  dot: { width: theme.size.sportDot, height: theme.size.sportDot },
  label: { ...theme.type.tag },
});

const SURFACE = StyleSheet.create({
  base: { backgroundColor: theme.color.line2 },
  ok: { backgroundColor: theme.color.mintSoft },
  hot: { backgroundColor: theme.color.coralSoft },
  warn: { backgroundColor: theme.color.amberSoft },
  bad: { backgroundColor: theme.color.redSoft },
  // The one background that is a base rather than a soft — see the module note.
  volt: { backgroundColor: theme.color.volt },
  onDark: { backgroundColor: theme.color.onDarkTag },
  // No bed: a dash in `line`, inside the padding's first point (see the module note).
  more: {
    borderWidth: DASH,
    borderStyle: 'dashed',
    borderColor: theme.color.line,
    paddingVertical: theme.space.xxs - DASH,
    paddingHorizontal: theme.space.xs - DASH,
  },
});

const LABEL = StyleSheet.create({
  base: { color: theme.color.muted },
  ok: { color: theme.color.mintInk },
  hot: { color: theme.color.coralInk },
  warn: { color: theme.color.amber },
  bad: { color: theme.color.red },
  // `ink` and never white: Rule C's arithmetic on volt runs the other way round (13.96:1).
  volt: { color: theme.color.ink },
  onDark: { color: theme.color.surface },
  more: { color: theme.color.muted },
});

/**
 * **One message** — somebody's own words, on their own side.
 *
 * The stream's first of two components, and the split from `SystemLine` is
 * [ADR-0146](../../../../../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)'s
 * held at the surface: **never one component with a `kind` branch**, because that re-introduces
 * here exactly the shape the wire was built to refuse — one type carrying a text field real for
 * one arm and meaningless for the other. They share nothing worth sharing either: this is a
 * constrained-width block with an author, a side and a ground, and a system line is centred type.
 *
 * ## The author is a prop, and it is the whole handle
 *
 * Drawn **only where the conversation has more than two members**. In a pair there is nothing to
 * disambiguate. That is a fact about the *room* rather than about the message, so it arrives from
 * the screen and is never read in here — the rule `the-play-components.md` §3 states about
 * `sportName`, and `domain/room.ts`'s `namesItsAuthors` is where it is decided.
 *
 * **Whole, never a familiar form** ([ADR-0107](../../../../../docs/adr/0107-the-player-card-is-assembled-outside-the-engine.md)):
 * the prototype's universal first name appears in fourteen of its twenty-two templates and is a
 * word the person never gave the platform.
 *
 * **The reader's own bubbles carry no label, which is one condition more than the spec states**
 * and is worth naming rather than leaving as an accident. The label exists to say **which of
 * several other people** spoke, and the reader's own side is never the ambiguous one. Drawn, it
 * would have to be either the reader's handle — which disagrees with the *You* the same bubble is
 * announced as, so the eye and the ear would name one person two ways — or the word *You*, which
 * is not a handle and repeats what the side and the ground already say. Neither is worth a line
 * of type above every message somebody sent.
 *
 * ## The spoken name always names the author, even where the label does not
 *
 * §24.4, and the reason is Part 13's: the visible label is dropped in a pair because **the side
 * and the ground** say who spoke, and *side and ground* is precisely what *never colour as the
 * only signal* refuses to let a listener depend on. So `bubbleLabel` names every author on every
 * bubble, and *You* on the reader's own — a bubble is read **by** the person it is drawn for,
 * where a system line is a third-person record everybody in the room reads identically.
 *
 * ## The geometry, which had never been drawn on a phone
 *
 * `size.bubble.maxShare` of the stream, and the argument for the number is in `theme.ts`. Two
 * grounds, one per side, and **the tail is a corner rather than a triangle**: the speaker's own
 * bottom corner drops to `radius.bubbleTail` while the other three stay at `radius.bubble`. A
 * drawn triangle is a rotated square nobody has measured against a ground it must match exactly,
 * and it is the first thing to go wrong when a bubble is the last one before a separator. A
 * corner is the same statement in a value the system already has.
 *
 * **A message still going out draws identically.** There is no dimming, no clock and no tick: it
 * is on screen because sending it is safe, and a bubble that looked provisional would be the app
 * hedging about the one act on this screen it has no reason to hedge about. What has not landed
 * is `domain/stream.ts`' business, and it is reconciled rather than redrawn.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { bubbleLabel } from './conversationAccessibility';

export interface BubbleProps {
  readonly text: string;
  /**
   * The author's whole handle, or **`You`** — always spoken, and drawn only when `showAuthor` is
   * set. Never a familiar form, and never derived here.
   */
  readonly author: string;
  /** Whose side it goes on. The reader's own messages sit right, on the dark ground. */
  readonly mine: boolean;
  /** Whether the handle is drawn as well as spoken. The screen decides — see the module note. */
  readonly showAuthor: boolean;
}

export function Bubble({ text, author, mine, showAuthor }: BubbleProps) {
  return (
    <View
      // One element per entry — §24.1's complement, and the whole reason a backlog with no
      // actions in it is navigable at all.
      accessible
      accessibilityLabel={bubbleLabel(author, text)}
      style={[s.row, mine ? s.rowMine : s.rowTheirs]}
    >
      <View style={[s.bubble, mine ? s.mine : s.theirs]}>
        {showAuthor ? (
          <Text style={[s.author, mine ? s.authorMine : s.authorTheirs]}>{author}</Text>
        ) : null}
        <Text style={mine ? s.textMine : s.textTheirs}>{text}</Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  row: { width: '100%' },
  rowMine: { alignItems: 'flex-end' },
  rowTheirs: { alignItems: 'flex-start' },
  bubble: {
    maxWidth: `${theme.size.bubble.maxShare * 100}%`,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.md,
    borderRadius: theme.radius.bubble,
    gap: theme.space.xxs,
  },
  // The dark card's ground, which is where white text is already 13,29:1 — and the one surface
  // in this system that carries a voice rather than a value.
  mine: { backgroundColor: theme.color.night, borderBottomRightRadius: theme.radius.bubbleTail },
  // 5.1's card: `surface` bounded by `line`, because a white block on `paper` with no border is
  // a shape that disappears at the edges.
  theirs: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderBottomLeftRadius: theme.radius.bubbleTail,
  },
  textMine: { ...theme.type.rlLabel, color: theme.color.surface },
  textTheirs: { ...theme.type.rlLabel, color: theme.color.ink },
  // `flab` labels a control and `eyebrow` labels a region you are reading, which is what a run
  // of somebody's messages is — so the on-dark half takes `onDarkEyebrow`, the token named for
  // exactly this role at exactly this ratio, rather than `line`, which bounds a thing.
  author: { ...theme.type.eyebrow, textTransform: 'uppercase' },
  authorMine: { color: theme.color.onDarkEyebrow },
  authorTheirs: { color: theme.color.muted },
});

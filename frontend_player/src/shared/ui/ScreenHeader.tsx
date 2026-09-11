/**
 * The screen header, per design-system 10.3 — eyebrow above, h1 below, an optional **sub-line**
 * under it, an optional back control, an optional **lead** slot and an optional right slot.
 *
 * ## The title and its sub-line are one element, and the name may differ from the drawing
 *
 * A sub-line **qualifies what the title names** — `Padel · planning` under the people a room is
 * named by — so it has no action of its own and no reason to be a second stop for a listener;
 * §20.1's merge rule, applied to a header. Absent a `titleLabel` the element reads its two texts
 * as drawn; **with one, it reads that and nothing else**. `titleLabel` is §20.4's *the visible
 * label truncates, the spoken one never does*, for a header whose drawn lines are not what it is
 * called — the conversation draws the handles' stems over a `·`, and is called by the handles
 * whole over commas ([#401](https://github.com/Raketa02/Raketa/issues/401)). A screen whose
 * sub-line carries a mark a listener has no reading for supplies one. The eyebrow stays outside
 * the element, above it: it labels the **region**, not the title.
 *
 * The sub-line is `tiny` in `muted` and is drawn **as given** — no uppercase, which is what tells
 * it apart from the eyebrow it sits opposite: the eyebrow shouts a region's name and the sub-line
 * says quietly what the thing above it is. No new type role was needed.
 *
 * **The back control is opt-in and stays that way.** Most screens are somewhere a player
 * arrived at rather than walked into, and a header that drew a chevron by default would
 * put that control on screen by omission — pointing at whatever the router happened to
 * have behind it. A screen that has a way back says so.
 *
 * The questionnaire is now one of them: a player may walk back over the questions they
 * have answered ([ADR-0020](../../../../docs/adr/0020-revisable-assessment-answers.md),
 * which supersedes ADR-0017's irreversibility rule), and this is the control they do it
 * with — 20pt, `muted`, on a 44 × 44 target, per design-system 10.3.
 *
 * The eyebrow labels a region you are READING. It is not `flab`, which labels a control
 * you are about to OPERATE — the two are not interchangeable (design-system 3.3).
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

export interface ScreenHeaderProps {
  readonly title: string;
  /**
   * What the header is **called**, where that differs from what it draws — §20.4's rule. Absent,
   * the element is named by the title and the sub-line. Every character of a shortened title
   * belongs here whole.
   */
  readonly titleLabel?: string;
  readonly eyebrow?: string;
  /**
   * Under the title, qualifying what it names — the sport and the game's state under the people
   * a room is named by. `tiny` in `muted`, drawn as given; spoken as part of the title's element.
   */
  readonly subline?: string;
  /**
   * Between the back control and the words — **whatever identifies what the title names.**
   *
   * The conversation is the first header with one: a room is named by the people in it, so their
   * faces belong beside their handles rather than in the page under them, where the stream would
   * scroll past them. It is a slot rather than a `faces` prop for `right`'s own reason — the
   * header holds an arrangement and the screen holds what goes in it, and a header that knew what
   * a face was would be the design system owning one, which #338 §5 refused by name.
   */
  readonly lead?: ReactNode;
  /** A segmented control, a close control — whatever the screen pins to the right. */
  readonly right?: ReactNode;
  readonly onBack?: () => void;
  readonly backLabel?: string;
}

export function ScreenHeader({
  title,
  titleLabel,
  eyebrow,
  subline,
  lead,
  right,
  onBack,
  backLabel = 'Back',
}: ScreenHeaderProps) {
  return (
    <View style={s.header}>
      {onBack !== undefined ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={backLabel}
          onPress={onBack}
          // The visual chevron is 20pt; the reachable area is 44 x 44.
          hitSlop={theme.hit.infoMark}
          style={({ pressed }) => [s.back, pressed ? s.backPressed : undefined]}
        >
          <Text style={s.backMark}>{'‹'}</Text>
        </Pressable>
      ) : null}

      {lead}

      <View style={s.titles}>
        {eyebrow !== undefined ? <Text style={s.eyebrow}>{eyebrow}</Text> : null}
        {/* One element: the title and what qualifies it. `accessible` is what merges the two
            texts on both platforms, and the role is the block's rather than the title's so a
            listener lands on the whole. A label only where the screen supplied one — absent, the
            platform reads the texts as drawn, and a header labelled with its own title would
            answer for it in every `getByLabelText` that means the control beside it. */}
        <View
          accessible
          accessibilityRole="header"
          {...(titleLabel === undefined ? {} : { accessibilityLabel: titleLabel })}
          style={s.named}
        >
          <Text style={s.title}>{title}</Text>
          {subline !== undefined ? <Text style={s.subline}>{subline}</Text> : null}
        </View>
      </View>

      {right !== undefined ? <View style={s.right}>{right}</View> : null}
    </View>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingHorizontal: theme.size.gutter,
    paddingVertical: theme.space.md,
  },
  titles: { flex: 1, gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  named: { gap: theme.space.xxs },
  title: { ...theme.type.h1, color: theme.color.ink },
  subline: { ...theme.type.tiny, color: theme.color.muted },
  back: { alignItems: 'center', justifyContent: 'center' },
  backPressed: { opacity: 0.7 },
  backMark: { ...theme.type.h1, color: theme.color.muted },
  right: { alignItems: 'flex-end' },
});

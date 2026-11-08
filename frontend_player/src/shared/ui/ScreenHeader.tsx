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
 * with — h1-sized, on a 44 × 44 target, per design-system 10.3.
 *
 * ## The chevron is `ink`, and its box is the glyph
 *
 * It was drawn in `muted` — the eyebrow's own colour — which made the one **control** in this
 * header the quietest thing in it, and left it reading as chrome beside the text rather than
 * as something to press. `ink` is the step up, and it is only a colour: the size, the weight
 * and the 44pt target are untouched, so nothing here grows.
 *
 * **Its line box is the glyph rather than h1's 24pt line**, which is what `num`'s own rule
 * does for a drawn figure — *lineHeight equals the size* — applied to a drawn mark. The row
 * centres its children, so a 24pt box containing a 19pt mark centred the box; on a header with
 * two lines that was close enough to pass, and on one with a single line it put the chevron
 * visibly off the text beside it. Read off the type role rather than typed, so the two cannot
 * drift.
 *
 * ## A header with no title is headed by its eyebrow
 *
 * 10.3 says a screen keeps its h1 even where the eyebrow seems to say enough, and the game
 * screen's plan lead is the first surface the design draws without one
 * ([#414](https://github.com/Raketa02/Raketa/issues/414), Part 16): `DOUBLES · COUNTED` over a
 * card that names the people and a plan that names the day, and nothing an h1 could add. So
 * `title` is optional, and **where it is absent the eyebrow moves inside the element and becomes
 * the heading** — the same words, the same style, one row lower in the tree — because a listener's
 * first stop has to be the line that says what the screen is, not an element with a role and no
 * words in it. With a title the eyebrow stays above and outside, exactly as before.
 *
 * **And a header with neither is headed by nothing.** The Players tab's header is its
 * *Deck | Radar* toggle in the lead slot and a chip in the right one, with no words of its own
 * ([ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1). There the heading element is not drawn at all rather than drawn empty: an element
 * carrying a role and no words is a stop a listener lands on and hears nothing from, and the
 * toggle's own segments are the first thing the screen has to say.
 *
 * ## A header that names a thing can be the door to it
 *
 * A group's page opens the group's Info from its header (Q125, as WhatsApp, Telegram and iMessage
 * open a group's info): the tile, the name and the line under it are one target. With `onPress`
 * **the whole row is the button** and the back control and the right slot keep their own presses —
 * they are the deeper responders, so a touch on either is theirs and a touch anywhere else in the
 * row is the header's. The row is pressed rather than a box round the lead and the words because
 * the lead must stay **a direct child of the row**: the group page's sport filter measures the tile
 * against the header's own left edge (`SportPillFrame`'s `cover`), and a box would move its origin.
 * The row dims while it is pressed — 6.6's opacity, the back control's own.
 *
 * **The named element is a `button` then, not a `header`**, carrying `pressHint` — a listener has to
 * hear that it does something. The row itself is not an element, so the back control and the right
 * slot are still stops of their own.
 *
 * The eyebrow labels a region you are READING. It is not `flab`, which labels a control
 * you are about to OPERATE — the two are not interchangeable (design-system 3.3).
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { ReactNode } from 'react';

import { theme } from './theme';

interface ScreenHeaderSlots {
  /** The h1. Absent on a screen the design draws without one — the eyebrow is the heading then. */
  readonly title?: string;
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
  /**
   * **A mark on the title's own line**, straight after its last letter and centred on it — a
   * group's official mark (#529). Hidden from a screen reader by whoever draws it, so a screen
   * whose mark means something says it in `titleLabel`. The title still ends in an ellipsis
   * before the mark is pushed off.
   */
  readonly titleMark?: ReactNode;
  /** A segmented control, a close control — whatever the screen pins to the right. */
  readonly right?: ReactNode;
  readonly onBack?: () => void;
  readonly backLabel?: string;
  /**
   * **A header that names a thing rather than a screen** — a group's page (play 39, 40;
   * [#512](https://github.com/Raketa02/Raketa/issues/512)): the title at `h2` beside the group's
   * tile in the lead slot, and **the title and the sub-line each on one line, ending in an
   * ellipsis** rather than wrapping (story 50), because a long group name and its club must not
   * push the page down. The spoken name is never cut: the element reads both texts whole.
   */
  readonly compact?: boolean;
}

/**
 * **The header is a button** — a group's page, whose header opens Info (Q125). The whole row answers
 * but for the back control and the right slot; the named element becomes a `button`. See the module
 * note. A pressable header **has a title**, which names the button, and says what it opens: a row
 * that could be pressed with nothing to call it is the unnamed pressable `shared/ui` refuses.
 */
interface PressableHeader {
  readonly title: string;
  readonly onPress: () => void;
  /** What pressing the header opens, spoken after its name — *Opens Info*. */
  readonly pressHint: string;
}

export type ScreenHeaderProps = ScreenHeaderSlots &
  (PressableHeader | { readonly onPress?: undefined; readonly pressHint?: undefined });

export function ScreenHeader({
  title,
  titleLabel,
  eyebrow,
  subline,
  lead,
  titleMark,
  right,
  onBack,
  backLabel = 'Back',
  compact = false,
  onPress,
  pressHint,
}: ScreenHeaderProps) {
  const lines = compact ? 1 : undefined;

  const row = (
    <>
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
        {eyebrow !== undefined && title !== undefined ? (
          <Text style={s.eyebrow}>{eyebrow}</Text>
        ) : null}
        {/* One element: the title and what qualifies it. `accessible` is what merges the two
            texts on both platforms, and the role is the block's rather than the title's so a
            listener lands on the whole. A label only where the screen supplied one — absent, the
            platform reads the texts as drawn, and a header labelled with its own title would
            answer for it in every `getByLabelText` that means the control beside it. Where there
            is no title the eyebrow is what is inside it, and is the heading — and where there is
            neither, there is no element: the slots are the header (see the module note). */}
        {title === undefined && eyebrow === undefined ? null : (
          <View
            accessible
            // A header that opens something is a button to a listener (see the module note).
            accessibilityRole={onPress === undefined ? 'header' : 'button'}
            {...(titleLabel === undefined ? {} : { accessibilityLabel: titleLabel })}
            {...(pressHint === undefined ? {} : { accessibilityHint: pressHint })}
            style={s.named}
          >
            {title === undefined ? (
              <Text style={s.eyebrow}>{eyebrow}</Text>
            ) : titleMark === undefined ? (
              <Text style={[s.title, compact ? s.titleCompact : undefined]} numberOfLines={lines}>
                {title}
              </Text>
            ) : (
              <View style={s.titleLine}>
                <Text
                  style={[s.title, compact ? s.titleCompact : undefined, s.titleBesideMark]}
                  numberOfLines={lines}
                >
                  {title}
                </Text>
                {titleMark}
              </View>
            )}
            {subline !== undefined ? (
              <Text style={s.subline} numberOfLines={lines}>
                {subline}
              </Text>
            ) : null}
          </View>
        )}
      </View>

      {right !== undefined ? <View style={s.right}>{right}</View> : null}
    </>
  );

  return onPress === undefined ? (
    <View style={s.header}>{row}</View>
  ) : (
    // Not an element of its own: the named block inside is the button a listener lands on, and
    // the back control and the right slot stay stops of their own.
    <Pressable
      accessible={false}
      onPress={onPress}
      style={({ pressed }) => [s.header, pressed ? s.headerPressed : undefined]}
    >
      {row}
    </Pressable>
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
  headerPressed: { opacity: 0.7 },
  titles: { flex: 1, gap: theme.space.xxs },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
  },
  named: { gap: theme.space.xxs },
  title: { ...theme.type.h1, color: theme.color.ink },
  titleCompact: { ...theme.type.h2 },
  // The mark rides the title's line: the title gives way to it rather than pushing it off.
  titleLine: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  titleBesideMark: { flexShrink: 1 },
  subline: { ...theme.type.tiny, color: theme.color.muted },
  back: { alignItems: 'center', justifyContent: 'center' },
  backPressed: { opacity: 0.7 },
  backMark: {
    ...theme.type.h1,
    // The mark's box IS the mark — see the module note. Read off the role it is drawn at, so
    // a change to h1 carries here rather than leaving a number behind.
    lineHeight: theme.type.h1.fontSize,
    color: theme.color.ink,
  },
  right: { alignItems: 'flex-end' },
});

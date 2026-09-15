/**
 * The **ON COURT** mark — a small drawn tick and two words: what the on-court check concluded
 * about that photograph ([#313](https://github.com/Raketa02/Raketa/issues/313),
 * [ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §7).
 *
 * Drawn on *checked and passed* and on nothing else. *Checked and flagged* and *nobody
 * looked* draw **identically**, which is `domain/onCourtMark`'s rule and not this
 * component's: a card must not tell one player that another player's photograph was doubted,
 * so what crosses is the positive alone
 * ([ADR-0138](../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)).
 *
 * ## One mark, one drawing, three placements
 *
 * The photo panel at its two sizes and the deck card all draw this — the words, the tick before
 * them, the spoken clause — because **one mark has one drawing**, and the tick is the one value
 * ADR-0169 §7 deliberately does not fence to the deck card. What differs by placement is the
 * composition around it: on a panel the mark is centred at the top in `mintSoft` over the pinned
 * scrim, capitalised and capped; on the deck card it sits top-right over an un-scrimmed
 * photograph in `surface` with the on-media shadow, lower-cased after its tick, at the size the
 * mock draws it. Both treatments are styles over the same two words, never a second string.
 *
 * ## The tick is drawn, sized to the words, and the mark moved down for it
 *
 * Archivo Bold **does not draw U+2713** — the app's own face has no glyph for it, so a text
 * tick renders in a per-platform fallback whose face, weight and advance this app neither
 * controls nor can measure (ADR-0135's finding about `U+26A1`, one surface over). So the tick
 * is `Tick`'s own path in a smaller box: a **share of the words' font size** rather than 6.8's
 * fixed 12 × 12, because on a 74pt panel the big tick beside a 51,19pt word leaves the words a
 * cap of 1,0 — a freeze under another name — and a 6,84pt one leaves them 1,1. Even that needed
 * room the corner did not leave at the panel's own `space.xs`: the mark now sits at `space.md`
 * (`PhotoPanel`'s `MARK_TOP`, 12pt down rather than 6), and the arithmetic is in
 * `onCourtMarkFit.test.ts` rather than in this sentence. It **does not scale with Dynamic Type** — geometry, as every drawn mark in
 * this system — so the cap is derived over what the corner leaves the words once the tick has
 * taken its share.
 *
 * **The words are what a reader can act on, and the tick is what the mocks draw.** A green tick
 * alone on a stranger's photograph would be a mark whose meaning nobody has been told — and the
 * meaning it would be assumed to have is *verified account*, which this platform does not do
 * and has never claimed. The words stay; the tick joins them.
 *
 * ## Mint over the pinned scrim, and no ground of its own
 *
 * `mintSoft` and not `mint` on the panels: as a foreground over the panel's scrim, `mint` is
 * **1,29:1** and simply not there — volt's own problem, in the other hue. `mintSoft` is
 * **4,55:1** against the worst photograph there can be, which is AA and is the tightest pair
 * on the panel; it is the pinned scrim that makes it computable at all, exactly as the white
 * Level beside it is, and it is derived in [`textOnMedia.test.ts`](./textOnMedia.test.ts)
 * rather than asserted here. The deck card has no scrim at its top — the mock has none — so
 * there the mark takes the Level's own treatment, `surface` with `textOnMedia`, and the tick
 * takes the same colour as the words beside it at every placement.
 *
 * **Colour is not the signal.** The words carry it and the tick and the mint reinforce it,
 * which is [Part 13](../../../docs/design-system.md#part-13--accessibility)'s *never colour
 * alone* answered by the copy rather than by a second cue — and the spoken half is
 * {@link ON_COURT_CLAUSE}, in the drawing surface's own name, because the mark announces
 * nothing (§20.1).
 */

import { StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import type { PhotoPanelSize } from './PlayerPhoto';
import { TICK_PATH, TICK_SPACE } from './Tick';
import { theme } from './theme';

/**
 * **The mark itself** — what the on-court check concluded, in two words.
 *
 * Sentence case here and capitalised by the panel, exactly as the Sport beneath it is — and
 * lower-cased by the deck card after its tick: the case is a treatment the placements apply,
 * and a string that arrived pre-shouted would be the one place in this system where a style
 * decision is spelled into the copy.
 *
 * **There is no figure in it and none to put in it.** ADR-0133's clause survives ADR-0138
 * untouched — the check's own confidence crosses on no route — so the mark says a thing
 * happened and never how sure anybody was.
 */
export const ON_COURT_MARK = 'On court';

/**
 * `Photo checked: on court` — the mark, for a listener, and **it leads with the photograph**.
 *
 * The drawing can rely on where it sits: a tick and two words over somebody's picture, above
 * their Level, are plainly about the picture. A clause in a run of sentences cannot, and *on
 * court* alone arriving between a Level and a forecast is one comma away from **activity
 * recency** — the one thing every card and every record on this platform refuses at every
 * granularity.
 *
 * The mark announces nothing of its own (§20.1), so this is composed by whichever surface
 * draws it — the candidate card's spoken body, the deck card's, and the record header's.
 */
export const ON_COURT_CLAUSE = 'Photo checked: on court';

/**
 * How far the mark's words may grow on a panel, and **derived rather than chosen**.
 *
 * Part 13 requires text to scale with the OS setting, and a panel is a fixed box at whichever
 * of its two sizes it is drawn — so the label may neither be frozen nor grow without bound,
 * and `maxFontSizeMultiplier` is what is left. That is the tab bar's mechanism, second instance
 * ([`tabBarLabelCap.test.ts`](./tabBarLabelCap.test.ts)), and the number comes from the same
 * place: the real Archivo Bold advance widths, against the width the panel's own corner leaves
 * at the mark's own top edge **once the tick has taken its share** — the tick is geometry and
 * does not scale, so what scales is the words alone.
 *
 * **It is a bound and not a licence** — `ON COURT` truncated is `ON COU…`, a mark that has
 * stopped saying anything, where the Sport label under it survives its own ellipsis legibly
 * and is therefore left uncapped.
 *
 * **One per panel size, re-derived and never scaled.** The panel's corner is a third of its
 * own width, so what is left for the words at the mark's own top edge is a different fraction
 * of a different width at each size — 67,20 of 74 on a card and 92,60 of 112 on the record
 * sheet, at `space.md`. Multiplying the card's cap by the widths' ratio would be
 * arithmetic over the wrong quantity; both come out of `largestStepThatFits` against the real
 * Archivo advances, and a third size that arrives without a row here fails to compile.
 *
 * **The deck card has no cap.** It is not a fixed box: the mark shares a row with the Level and
 * both scale, and the row wraps its own content rather than clipping it.
 */
export const ON_COURT_MAX_SCALE = {
  card: 1.1,
  record: 1.6,
} as const satisfies Readonly<Record<PhotoPanelSize, number>>;

/** Where the mark is standing: a photo panel at one of its two sizes, or the deck card. */
export type OnCourtMarkPlacement = PhotoPanelSize | 'deck';

/**
 * The tick's box for words at `fontSize` — a share of it, so tick and words read as one line.
 *
 * Exported for the fit test, which needs the number the panel arithmetic is done against.
 */
export function onCourtTickBox(fontSize: number): number {
  return fontSize * theme.size.onCourtTick.share;
}

export interface OnCourtMarkProps {
  /** Which composition it is standing in — the cap is a panel's own, and the deck has none. */
  readonly on: OnCourtMarkPlacement;
}

export function OnCourtMark({ on }: OnCourtMarkProps) {
  const placement = PLACEMENT[on];
  const box = onCourtTickBox(placement.words.fontSize);

  return (
    <View style={[s.mark, placement.row]}>
      {/* `Tick`'s own path in a smaller box: the stroke is scaled back up so it is 1,5pt on
          screen whatever the box, rather than 1,5 units of a 12-unit drawing. */}
      <Svg width={box} height={box} viewBox={`0 0 ${TICK_SPACE} ${TICK_SPACE}`}>
        <Path
          d={TICK_PATH}
          stroke={placement.colour}
          strokeWidth={theme.size.onCourtTick.stroke * (TICK_SPACE / box)}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </Svg>
      <Text
        style={[placement.words, s.words, { color: placement.colour }, placement.case]}
        numberOfLines={1}
        {...(placement.cap === undefined ? {} : { maxFontSizeMultiplier: placement.cap })}
      >
        {ON_COURT_MARK}
      </Text>
    </View>
  );
}

/** What one placement decides about the mark — the treatment, gathered, over the one drawing. */
interface Placement {
  /** `tag` on a panel — uppercased rather than `eyebrow`, which is the Sport's decision one line
   *  down and the same one: the tracking is what does not fit — and `inlineTitle` on the deck
   *  card, which is the size the mock draws the mark at beside a 40pt Level. */
  readonly words: {
    readonly fontFamily: string;
    readonly fontSize: number;
    readonly lineHeight: number;
  };
  /** The tick's colour and the words': `mintSoft` over a scrim, `surface` over a photograph. */
  readonly colour: string;
  /** The case is the placement's treatment of the two words, never the copy's. */
  readonly case: { readonly textTransform: 'uppercase' | 'lowercase' };
  readonly row: { readonly justifyContent?: 'center'; readonly flexShrink?: number };
  /** A panel is a fixed box and caps the words; the deck card is not, and does not. */
  readonly cap?: number;
}

const PLACEMENT: Readonly<Record<OnCourtMarkPlacement, Placement>> = {
  card: {
    words: theme.type.tag,
    colour: theme.color.mintSoft,
    case: { textTransform: 'uppercase' },
    row: { justifyContent: 'center' },
    cap: ON_COURT_MAX_SCALE.card,
  },
  record: {
    words: theme.type.tag,
    colour: theme.color.mintSoft,
    case: { textTransform: 'uppercase' },
    row: { justifyContent: 'center' },
    cap: ON_COURT_MAX_SCALE.record,
  },
  // Top-right of the deck card, opposite the Level, in the row the card gives it; the mock draws
  // *on court* in lower case after its tick.
  deck: {
    words: theme.type.inlineTitle,
    colour: theme.color.surface,
    case: { textTransform: 'lowercase' },
    row: { flexShrink: 1 },
  },
};

const s = StyleSheet.create({
  /**
   * A row of the tick and the words. **Centred on a panel**, and that is geometry rather than
   * composition: left-aligned at the panel's own padding the tick sits **inside the corner's
   * curve** — the radius is a third of the width, so even at `space.md` the box has narrowed on
   * each side — where centred, the line takes the middle of what is left and clears both curves.
   * The Level and the Sport underneath are left-aligned because they sit well below the corner's
   * influence. Where each placement puts the row is `PLACEMENT`'s.
   */
  mark: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
  },
  words: { flexShrink: 1, ...theme.shadow.textOnMedia },
});

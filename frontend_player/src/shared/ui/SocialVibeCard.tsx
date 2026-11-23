/**
 * **The Social vibe card** — [7.39](../../../docs/design-system.md#739-the-social-vibe-card)
 * ([#840](https://github.com/Raketa02/Raketa/issues/840); ADR-0207 §6, §9; for fun 7, which leads
 * over 5 and 6).
 *
 * A For-fun game's full card, where a competitive game draws its Balance forecast: how much the
 * whole table shares, and who shares **your** tags.
 *
 * ```
 * SOCIAL VIBE                                    eyebrow, a header
 * 67%  Good vibe                                 num.levelLarge in the band's paper ink · cardTitle
 * [██████████████████████░░░░░░░░░░░░]           size.socialVibeCard.bar (21) · track line2 · 0–100
 *                       (◉)  (◉)  (◉)  (◉)       faces 24, a column 36 each — hidden: the rows say who
 *                       You magda filip kuba     tag, muted, one line, an ellipsis
 * ▌🍻 Stays for a drink  ●              ●        shared: voltPale band · ink words · oliveInk dots
 * ─────────────────────────────────────────      line2 hairline between rows
 *  🔁 Here for a regular game ●                  only you: no band · vibeGrey words · a line dot
 * ```
 *
 * ## Two features, one card
 *
 * A game still filling opens on it (`proposals`, #840) and a booked game and the game at the court
 * draw it next (`games`, #841) — two features that may not import each other, so it is here, as the
 * Balance forecast block is. **It came down ahead of its second caller**, as the row did (#838):
 * ADR-0207 §6 decides the same card is drawn on all three screens, so it is built where both
 * features reach it rather than copied out of `proposals` by #841. Each hands it a `SocialVibeGrid` read off its own read; **the card
 * derives nothing**: which people are the columns and in what order, and which rows somebody else
 * shares, are the feature's rule. It only paints what it is handed, in its band's colours.
 *
 * ## The number is the deck card's
 *
 * The figure is the served Social vibe, the same one the For-fun card was swiped on (ADR-0207 §6:
 * *the % swiped on is the % looked at*), worded and coloured by `socialVibeBand`, and the bar runs 0
 * to 100 and fills to it — one value, as on the row (7.38). On paper the figure takes the olive
 * inks, and the fill the band's own colour on both grounds (ADR-0207 §8).
 *
 * ## Static, and spoken a row at a time
 *
 * The grid has no taps of its own. A listener hears the eyebrow, the reading (*Social vibe, 67
 * percent, Good vibe*, the row's own sentence), then **each row as one element**: *Stays for a
 * drink: you, kuba.w*. The faces and names over the columns are hidden — every row already names
 * whoever carries it — and the bar is part of the reading, whose figure it repeats.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatPercent } from '@/shared/formatting/ratingFormat';
import { socialTagLabel } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialVibeColumn, SocialVibeGrid } from '@/shared/vocabulary/socialVibeGrid';
import {
  SOCIAL_VIBE,
  socialVibeBand,
  socialVibeColumnName,
  socialVibeRowSpoken,
  socialVibeShown,
  socialVibeSpoken,
  type SocialVibeTone,
} from '@/shared/vocabulary/socialVibePresentation';

import { Card } from './Card';
import { PlayerPhoto } from './PlayerPhoto';
import { SOCIAL_VIBE_ON_DARK } from './SocialVibeRow';
import { theme } from './theme';

/**
 * Each band's figure **on paper** — olive ink for *Great* and *Good vibe*, a dimmed olive for *Some
 * common ground*, the grey for *Fresh mix* (ADR-0207 §8). Volt as a foreground on paper is ~1,3:1,
 * so the figure cannot be the fill's colour here, as it is on the dark card. **The Social vibe's
 * figure on paper wherever it is printed**: a For-fun fit's % on Post a game's sheet reads it too
 * (#842), on the same `surface`.
 */
export const SOCIAL_VIBE_CARD_FIGURE: Readonly<Record<SocialVibeTone, string>> = {
  volt: theme.color.oliveInk,
  dimVolt: theme.color.oliveInkDim,
  grey: theme.color.vibeGrey,
};

/**
 * Each band's fill — **the row's own table**, since a band has one fill whatever the ground
 * (ADR-0207 §8): one owner, so the deck card's bar and this one cannot drift apart.
 */
export const SOCIAL_VIBE_CARD_FILL: Readonly<Record<SocialVibeTone, string>> = SOCIAL_VIBE_ON_DARK;

/** The card, for a suite that asks what is inside it. */
export const SOCIAL_VIBE_CARD = 'social-vibe-card';

export interface SocialVibeCardProps {
  readonly grid: SocialVibeGrid;
}

export function SocialVibeCard({ grid }: SocialVibeCardProps) {
  // One number for every mark, as on the row.
  const pct = socialVibeShown(grid.pct);
  const band = socialVibeBand(pct);

  return (
    <Card>
      <View style={s.card} testID={SOCIAL_VIBE_CARD}>
        <Text accessibilityRole="header" style={s.eyebrow}>
          {SOCIAL_VIBE}
        </Text>

        <View accessible accessibilityLabel={socialVibeSpoken(pct)} style={s.reading}>
          <View style={s.figureRow}>
            <Text style={[s.figure, { color: SOCIAL_VIBE_CARD_FIGURE[band.tone] }]}>
              {formatPercent(pct)}
            </Text>
            <Text style={s.word}>{band.word}</Text>
          </View>
          <View style={s.bar}>
            {pct === 0 ? null : (
              <View
                style={[
                  s.fill,
                  { width: `${pct}%`, backgroundColor: SOCIAL_VIBE_CARD_FILL[band.tone] },
                ]}
                testID="social-vibe-card-fill"
              />
            )}
          </View>
        </View>

        <View>
          <View
            style={s.heads}
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            <View style={s.label} />
            {grid.columns.map((column) => (
              <Head key={column.playerId} column={column} />
            ))}
          </View>

          {grid.rows.map((row) => {
            const carriers = grid.columns.filter((_, at) => row.dots[at] === true);
            return (
              <View
                key={row.tag}
                accessible
                accessibilityLabel={socialVibeRowSpoken(row.tag, carriers)}
                style={[s.row, row.shared ? s.shared : null]}
                testID="social-vibe-row"
              >
                <Text style={[s.label, row.shared ? s.sharedWords : s.yoursWords]}>
                  {socialTagLabel(row.tag)}
                </Text>
                {grid.columns.map((column, at) => (
                  <View key={column.playerId} style={s.cell} testID="social-vibe-cell">
                    {row.dots[at] === true ? (
                      <View
                        style={[s.dot, row.shared ? s.sharedDot : s.yoursDot]}
                        testID="social-vibe-dot"
                      />
                    ) : null}
                  </View>
                ))}
              </View>
            );
          })}
        </View>
      </View>
    </Card>
  );
}

/** A column's head: the face, round, and the name under it on one line. */
function Head({ column }: { readonly column: SocialVibeColumn }) {
  return (
    <View style={s.head} testID="social-vibe-column">
      <PlayerPhoto
        playerId={column.playerId}
        {...(column.photoUrl === undefined ? {} : { photoUrl: column.photoUrl })}
        box={{ kind: 'face', size: theme.size.socialVibeCard.face }}
      />
      <Text style={s.name} numberOfLines={1} ellipsizeMode="tail">
        {socialVibeColumnName(column)}
      </Text>
    </View>
  );
}

const CARD = theme.size.socialVibeCard;

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  reading: { gap: theme.space.md },
  figureRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.levelLarge, ...theme.tabular },
  word: { ...theme.type.cardTitle, color: theme.color.ink, flexShrink: 1 },
  bar: {
    height: CARD.bar,
    borderRadius: theme.radius.socialVibe,
    overflow: 'hidden',
    backgroundColor: theme.color.line2,
  },
  fill: { position: 'absolute', left: 0, top: 0, bottom: 0 },
  // The heads and the rows share one inset and one column width, so a dot stands under its face.
  heads: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: theme.space.sm,
    paddingBottom: theme.space.xs,
  },
  head: { width: CARD.column, alignItems: 'center', gap: theme.space.xxs },
  name: { ...theme.type.tag, color: theme.color.muted, maxWidth: CARD.column },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: CARD.row,
    paddingHorizontal: theme.space.sm,
    paddingVertical: theme.space.xs,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: theme.color.line2,
  },
  shared: { backgroundColor: theme.color.voltPale },
  label: { flex: 1 },
  sharedWords: { ...theme.type.cardTitle, color: theme.color.ink },
  // The mock's row only you have is the same size at the regular weight, in grey.
  yoursWords: {
    ...theme.type.cardTitle,
    fontFamily: theme.font.sans[400],
    color: theme.color.vibeGrey,
  },
  cell: { width: CARD.column, alignItems: 'center' },
  dot: { width: CARD.dot, height: CARD.dot, borderRadius: CARD.dot / 2 },
  sharedDot: { backgroundColor: theme.color.oliveInk },
  // The mock's faint dot, 1,30 on `surface` — under a mark's 3:1 on purpose: it says a row is
  // yours, which every row is and the grey words and the missing band already say. Never the only
  // signal; recorded in 7.39 and held in socialVibeInks.test.ts.
  yoursDot: { backgroundColor: theme.color.line },
});

/**
 * **The Social vibe row** — [7.38](../../../docs/design-system.md#738-the-social-vibe-row) (#838;
 * ADR-0207 §9.4, for fun 1–2).
 *
 * For fun's headline number where the forecast is Competitive's (ADR-0207 §5): the % beside a
 * full-width bar filled to the same value, with *Social vibe* inside it.
 *
 * ```
 * 67%  [ Social vibe ████████████████████░░░░░░░░░░ ]
 * figure  num.xl, by band: volt · gameVoltDim · gameGrey
 * bar     size.socialVibe.bar (18) · radius.socialVibe (4) · clipped · track onDarkTag
 * fill    0–100, the figure's colour · its end square
 * name    tag, slanted (size.socialVibe.lean) · inset sm · surface on the track, ink on the fill
 * ```
 *
 * ## One value, two marks
 *
 * The figure and the fill are **one number**: the bar always runs 0 to 100, and the fill stops at
 * the %. It is not the balance bar, which maps an advantage to a fold on an amplified scale; a
 * vibe is a share of a whole, and drawn as one.
 *
 * ## The name stays readable over the fill and the track
 *
 * A fill that ends inside *Social vibe* would leave half the word `ink` on the dark track, which
 * nobody can read. So the name is drawn **twice, in the same place**: `surface` on the track, and
 * `ink` on a copy laid over the bar's whole width inside the fill, which clips it. Each letter is
 * whichever colour its ground carries — `ink` 13,96 on volt and 6,06 / 5,77 on the two lower bands,
 * white 9,9 on the track — however short or long the fill is. The copy is the bar's width as a
 * share of the fill (`100 / pct` of it), so it needs no measuring and no second frame.
 *
 * **The italic is drawn**: no italic Archivo is loaded, so the name leans by a skew, as Top 10's
 * mark and count do, at the same angle.
 *
 * ## One element
 *
 * The bar is a colour and the name inside it is a label, so the row is one `image` named *Social
 * vibe, 82 percent, Great vibe* (ADR-0207 §8): the band's word is said, since the colour is never
 * the only cue (Part 13), and the figure is drawn.
 *
 * **On dark only, today.** The deck card draws it; the Friends card draws it next (#842), on the
 * same ground. The Social vibe card on paper (#840) brings the paper paint — olive ink — with it.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatPercent } from '@/shared/formatting/ratingFormat';
import {
  SOCIAL_VIBE,
  socialVibeBand,
  socialVibeSpoken,
  type SocialVibeTone,
} from '@/shared/vocabulary/socialVibePresentation';

import { theme } from './theme';

/**
 * Each band's colour **on a dark card** — the figure's and the fill's at once, as `volt` is both.
 * Never `gameGreen` / `gameAmber` / `gameRed`: a vibe is not a verdict (ADR-0207 §8).
 */
export const SOCIAL_VIBE_ON_DARK: Readonly<Record<SocialVibeTone, string>> = {
  volt: theme.color.volt,
  dimVolt: theme.color.gameVoltDim,
  grey: theme.color.gameGrey,
};

export interface SocialVibeRowProps {
  /** The served Social vibe, a whole percent. The row words it in its band; it derives nothing. */
  readonly pct: number;
}

export function SocialVibeRow({ pct }: SocialVibeRowProps) {
  // One number for every mark: the figure printed is the fill, the word and the name. The server
  // sends a whole 0–100, so this only holds a slip to the scale rather than drawing *130%*.
  const filled = Math.round(Math.min(100, Math.max(0, pct)));
  const colour = SOCIAL_VIBE_ON_DARK[socialVibeBand(filled).tone];

  return (
    <View
      style={s.row}
      accessible
      accessibilityRole="image"
      accessibilityLabel={socialVibeSpoken(filled)}
    >
      <Text style={[s.figure, { color: colour }]}>{formatPercent(filled)}</Text>
      <View style={s.bar}>
        <View style={[s.box, s.wholeBar]}>
          <Text style={[s.name, s.onTrack]} numberOfLines={1}>
            {SOCIAL_VIBE}
          </Text>
        </View>
        {filled === 0 ? null : (
          <View
            style={[s.fill, { width: `${filled}%`, backgroundColor: colour }]}
            testID="social-vibe-fill"
          >
            {/* The bar's whole width, as a share of the fill: the same box as the copy above. */}
            <View style={[s.box, { width: `${10000 / filled}%` }]} testID="social-vibe-on-fill">
              <Text style={[s.name, s.onFill]} numberOfLines={1}>
                {SOCIAL_VIBE}
              </Text>
            </View>
          </View>
        )}
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  bar: {
    flex: 1,
    height: theme.size.socialVibe.bar,
    borderRadius: theme.radius.socialVibe,
    overflow: 'hidden',
    backgroundColor: theme.color.onDarkTag,
  },
  fill: { position: 'absolute', left: 0, top: 0, bottom: 0, overflow: 'hidden' },
  // Where the name sits: the bar's left edge, its full height. The track's copy runs to the bar's
  // right edge; the fill's is given the bar's width, so the two boxes are one.
  box: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    paddingLeft: theme.size.socialVibe.inset,
  },
  wholeBar: { right: 0 },
  name: { ...theme.type.tag, transform: [{ skewX: `${theme.size.socialVibe.lean}deg` }] },
  onTrack: { color: theme.color.surface },
  onFill: { color: theme.color.ink },
});

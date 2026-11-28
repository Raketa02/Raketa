/**
 * **The Top 10 numeral** ([#805](https://github.com/Rakieta02/Rakieta/issues/805); the Home rows screens
 * §7.2, §11; home rows 25–26.1; design-system 7.36) — the card's place, 1 to 10, huge, standing behind
 * the card's left edge so the card overlaps it.
 *
 * ```
 *   ░░░░┌──────────┐      ← the card covers the numeral's last `topTen.overlap`
 *  ██ ░░│          │
 *   █ ░░│  portrait│
 *   █ ░░│          │
 *  ███░░└──────────┘      ← the figures' baseline near the card's foot
 * ```
 *
 * **Drawn, as SVG text**: a gradient fill takes SVG, and so does an outline round the figures. Each
 * figure is drawn three times, in order — a hairline of `line`, the paper outline over it, and the
 * fill — so the outline reads on paper (paper on paper alone would not), and in *10* the *0* stands
 * over the *1*'s foot with its own outline, as home rows 25.3 draws it. The fill runs from `numeralTop`
 * at the figures' top to `numeralFoot` at the baseline — the screens' *night-to-teal* — and is
 * **`volt`** on the reader's own card (home rows 26.1).
 *
 * **Its box is worked out, not measured**: Archivo's figures are tabular, `size.topTen.figure`'s
 * advance of the em each, standing its `top` over the baseline and at most its `foot` under it — the
 * face's own metrics, beside the role in the theme — and `type.numeral` tracks them. So the card knows
 * where to overlap before anything is laid out, and *10* is wider by one figure, less the tracking.
 *
 * **A picture, hidden**: the card names its place (`topTenCardLabel`), so the numeral says nothing.
 */

import { useId } from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, G, LinearGradient, Stop, Text as SvgText } from 'react-native-svg';

import { theme } from '@/shared/ui';

const { fontFamily, fontSize, letterSpacing } = theme.type.numeral;
const { outline, edge, figure: FIGURE } = theme.size.topTen;
/** Room round the figures for the outline and its hairline, which stand outside the glyph's edge. */
const PAD = outline + edge;
const STEP = FIGURE.advance * fontSize + letterSpacing;
const HEIGHT = (FIGURE.top + FIGURE.foot) * fontSize + 2 * PAD;
const BASELINE = PAD + FIGURE.top * fontSize;

/** **The numeral's width** — its figures' advances, tracked, and the outline's room each side. */
export function numeralWidth(place: number): number {
  const figures = String(place).length;
  return figures * FIGURE.advance * fontSize + (figures - 1) * letterSpacing + 2 * PAD;
}

export function TopTenNumeral({
  place,
  mine,
}: {
  readonly place: number;
  /** The reader's own place: `volt`, where everybody else's is the gradient. */
  readonly mine: boolean;
}) {
  const gradient = useId();
  const width = numeralWidth(place);
  const fill = mine ? theme.color.volt : `url(#${gradient})`;
  const at = { y: BASELINE, fontFamily, fontSize };

  return (
    <View
      testID="top-ten-numeral"
      style={[s.box, { width }]}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={width} height={HEIGHT}>
        <Defs>
          <LinearGradient
            id={gradient}
            x1="0"
            y1={PAD}
            x2="0"
            y2={BASELINE}
            gradientUnits="userSpaceOnUse"
          >
            <Stop offset={0} stopColor={theme.color.numeralTop} />
            <Stop offset={1} stopColor={theme.color.numeralFoot} />
          </LinearGradient>
        </Defs>
        {String(place)
          .split('')
          .map((digit, index) => {
            const x = PAD + index * STEP;
            return (
              <G key={index}>
                <SvgText
                  {...at}
                  x={x}
                  fill="none"
                  stroke={theme.color.line}
                  strokeWidth={2 * (outline + edge)}
                  strokeLinejoin="round"
                >
                  {digit}
                </SvgText>
                <SvgText
                  {...at}
                  x={x}
                  fill="none"
                  stroke={theme.color.paper}
                  strokeWidth={2 * outline}
                  strokeLinejoin="round"
                >
                  {digit}
                </SvgText>
                <SvgText {...at} x={x} fill={fill}>
                  {digit}
                </SvgText>
              </G>
            );
          })}
      </Svg>
    </View>
  );
}

const s = StyleSheet.create({
  box: { height: HEIGHT },
});

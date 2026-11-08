/**
 * **The stage's hero** — the dark top of sign-in (and, from #785, sign-up): the *Raketa* wordmark
 * in its top-left corner, room for the deck in the middle (#786), and the headline at its foot
 * ([#784](https://github.com/Raketa02/Raketa/issues/784), PRD #783; design system 12.2).
 *
 * **A picture, and nothing else.** It is hidden from screen readers whole (ADR-0198: the form is the
 * screen), it takes no touch, and it does not move with the sheet: it is drawn behind the scroll at
 * a fixed height, so a short phone or a keyboard slides the sheet over it rather than pushing it.
 *
 * **Its words grow with the OS text size only so far** — `size.stage.textMaxScale`, the tab bar's
 * mechanism, derived in `stageTextCap.test.ts` — because the hero's room is fixed and the picture
 * takes what the words leave. The form under it is not capped.
 *
 * The room between the wordmark and the headline is where the deck (#786) and the podium (#788)
 * will be drawn, given whatever height those two leave; until then it is empty night.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import { STAGE_WORDMARK } from './authPresentation';
import { StageGround } from './StageGround';

export interface StageHeroProps {
  /** The line at the hero's foot — sign-in's names the swipe. */
  readonly headline: string;
  /** How tall the hero is — where the sheet's top edge sits at rest. */
  readonly height: number;
  /** The status bar's inset, which the wordmark sits under. */
  readonly topInset: number;
}

const CAP = theme.size.stage.textMaxScale;

export function StageHero({ headline, height, topInset }: StageHeroProps) {
  return (
    <View
      style={[s.hero, { height }]}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <StageGround />
      <View style={[s.content, { paddingTop: topInset + theme.space.xs }]}>
        <View style={s.wordmark}>
          <View style={s.mark} />
          <Text style={s.word} maxFontSizeMultiplier={CAP}>
            {STAGE_WORDMARK}
          </Text>
        </View>
        <View style={s.room} />
        <Text style={s.headline} maxFontSizeMultiplier={CAP}>
          {headline}
        </Text>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  hero: { position: 'absolute', top: 0, left: 0, right: 0 },
  // The sheet's own gutter, so the wordmark, the headline and the form share one left edge, as the
  // mock draws them.
  content: {
    flex: 1,
    paddingHorizontal: theme.space.xxl,
    paddingBottom: theme.space.lg,
  },
  wordmark: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs },
  // Volt as a fill on the dark — 2.2's rule, 12,57 on the ground.
  mark: {
    width: theme.size.stage.mark,
    height: theme.size.stage.mark,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.volt,
  },
  word: { ...theme.type.h1, color: theme.color.surface },
  // The deck's room (#786), between the wordmark and the headline.
  room: { flex: 1 },
  headline: { ...theme.type.stageTitle, color: theme.color.surface },
});

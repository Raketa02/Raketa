/**
 * **The stage's hero** — the dark top of sign-in and sign-up (#785): the *Raketa* wordmark in its
 * top-left corner, room for the deck (#786) or the podium (#788) in the middle, and the headline at
 * its foot ([#784](https://github.com/Raketa02/Raketa/issues/784), PRD #783; design system 12.2).
 *
 * **A picture, and nothing else.** It is hidden from screen readers whole (ADR-0198: the form is the
 * screen), it takes no touch, and it does not move with the sheet: it is drawn behind the scroll at
 * a fixed height, so a short phone or a keyboard slides the sheet over it rather than pushing it.
 *
 * **Its words grow with the OS text size only so far** — `size.stage.textMaxScale`, the tab bar's
 * mechanism, derived in `stageTextCap.test.ts` — because the hero's room is fixed and the picture
 * takes what the words leave. The form under it is not capped.
 *
 * **The room between the wordmark and the headline is the picture's** — sign-in's dealt deck
 * (#786), sign-up's podium (#788) — and it is whatever height those two leave, so the picture
 * measures it and fits itself in. Without a picture it is empty night.
 *
 * **A cover is drawn over the whole hero but the wordmark** — sign-in's *It's a game!* (#787), which
 * becomes the dark hero and nothing more: the cards and the headline go under it, the wordmark stays
 * in its corner over it, and the sheet is never under it because the hero ends where the sheet
 * begins.
 */

import type { ReactNode } from 'react';
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
  /** What the room between the wordmark and the headline draws — fitted to it by itself. */
  readonly picture?: ReactNode;
  /**
   * What is drawn over the whole hero — the picture and the headline both — and under the wordmark:
   * sign-in's *It's a game!* (#787). It fills the hero and lays itself out in it.
   */
  readonly cover?: ReactNode;
}

const CAP = theme.size.stage.textMaxScale;

export function StageHero({ headline, height, topInset, picture, cover }: StageHeroProps) {
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
        <View style={s.room}>{picture}</View>
        <Text style={s.headline} maxFontSizeMultiplier={CAP}>
          {headline}
        </Text>
        {/* Absolute in the column, so it fills the whole hero — Yoga sets an absolute child against
            its parent's border, not its padding — and drawn after the room and the headline, so it
            is over both. The wordmark is raised above it. */}
        {cover === undefined ? null : <View style={StyleSheet.absoluteFill}>{cover}</View>}
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
  // Raised over the cover: the wordmark stays in its corner while *It's a game!* fills the hero.
  wordmark: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xs, zIndex: 1 },
  // Volt as a fill on the dark — 2.2's rule, 12,57 on the ground.
  mark: {
    width: theme.size.stage.mark,
    height: theme.size.stage.mark,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.volt,
  },
  word: { ...theme.type.h1, color: theme.color.surface },
  // The picture's room, between the wordmark and the headline, a step clear of each.
  room: { flex: 1, marginVertical: theme.space.sm },
  headline: { ...theme.type.stageTitle, color: theme.color.surface },
});

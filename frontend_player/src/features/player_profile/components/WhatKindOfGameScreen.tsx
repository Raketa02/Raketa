/**
 * **What kind of game** — the per-sport declaration, behind a row and under one line
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * `PlayIntentsSection` as built ([#296](https://github.com/Raketa02/Raketa/issues/296)): one
 * row per rated sport, the row expands in place to the three answers, the footnote where a
 * sport is undeclared, every press a `PUT /play-intents/{sport}` on the `PROFILE_SCREEN`
 * surface. What the section lost on the way from the tab to a screen is its heading and its
 * body; what this screen says instead is one line under the title — *This changes how people
 * find you* — because the heading and the body were saying that in two paragraphs and the
 * title now says what the list is.
 */

import { useRouter } from 'expo-router';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';

import { PlayIntentsSection } from './PlayIntentsSection';
import { KIND_OF_GAME_LINE, WHAT_KIND_OF_GAME_TITLE } from './youProfilePresentation';

export function WhatKindOfGameScreen() {
  const router = useRouter();

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.playing}
      title={WHAT_KIND_OF_GAME_TITLE}
      subline={KIND_OF_GAME_LINE}
      onBack={router.back}
    >
      <PlayIntentsSection />
    </ShellScreen>
  );
}

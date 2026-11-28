/**
 * `theme.size.stage.textMaxScale`, held against the words it caps
 * ([#784](https://github.com/Rakieta02/Rakieta/issues/784), PRD #783 story 37).
 *
 * The hero is a picture with a fixed room — four tenths of the window, under the status bar, with
 * the deck (#786) taking whatever its words leave — so its words may neither be frozen (Part 13
 * requires text to scale) nor grow without bound. `maxFontSizeMultiplier` is what is left: the tab
 * bar's mechanism (`tabBarLabelCap.test.ts`), second instance. The form under the hero is not
 * capped; it scrolls.
 *
 * **The rule: at the cap, on the narrowest phone, every stage headline wraps to at most three
 * lines.** Two at the system size, as the mock draws it; a third is the room a large text setting
 * may take from the deck; a fourth would leave the deck nothing on a short phone. The cap is the
 * largest 0,1 step at which that holds, derived here and pinned in the theme, so a longer headline,
 * a heavier role or a wider gutter goes red here rather than overflowing on somebody's phone.
 *
 * **The wrap is greedy and word by word**, as a line breaker sets prose, against the real Archivo
 * advances (`test-support/fontMetrics.ts`). The tracking is NOT scaled with the text: a negative
 * tracking held at its system-size value is the wider of the two readings, so the cap errs short.
 */

import {
  NARROWEST_SCREEN,
  largestStepThatFits,
  readFace,
  widthOf,
} from '@/test-support/fontMetrics';
import { theme } from '@/shared/ui';

import { SIGN_IN_COPY, SIGN_UP_COPY, STAGE_WORDMARK } from './authPresentation';

/** Every headline the stage draws — sign-in's, and sign-up's since #785. */
const STAGE_HEADLINES = [SIGN_IN_COPY.headline, SIGN_UP_COPY.headline];

/** The most lines a headline may take at the cap — see the module note. */
const MOST_LINES = 3;

/** The hero's text column on the narrowest phone: the screen less the stage's gutter each side. */
const COLUMN = NARROWEST_SCREEN - 2 * theme.space.xxl;

const ROLE = theme.type.stageTitle;
const headlineFace = readFace(`@expo-google-fonts/archivo/${ROLE.fontFamily}.ttf`);
const wordmarkFace = readFace(`@expo-google-fonts/archivo/${theme.type.h1.fontFamily}.ttf`);

/** How many lines `text` takes in `column` at `scale` — greedy, word by word. */
function linesAt(text: string, scale: number): number {
  let lines = 1;
  let line = '';
  for (const word of text.split(' ')) {
    const longer = line === '' ? word : `${line} ${word}`;
    if (widthOf(headlineFace, longer, ROLE.fontSize * scale, ROLE.letterSpacing) <= COLUMN) {
      line = longer;
    } else {
      lines += 1;
      line = word;
    }
  }
  return lines;
}

/** The largest 0,1 step at which every headline keeps to `MOST_LINES`. */
function largestScaleThatKeeps(): number {
  let scale = 1;
  while (STAGE_HEADLINES.every((text) => linesAt(text, scale + 0.1) <= MOST_LINES)) {
    scale = Math.round((scale + 0.1) * 10) / 10;
  }
  return scale;
}

describe('the stage’s text cap', () => {
  it('is the largest step at which every headline keeps to three lines on the narrowest phone', () => {
    expect(theme.size.stage.textMaxScale).toBe(largestScaleThatKeeps());
    // Sign-in's line alone allowed 1,7; sign-up's (#785) is the one that wraps a fourth time there.
    expect(theme.size.stage.textMaxScale).toBe(1.6);
  });

  it('lets each headline sit on two lines at the system size, as the mock draws it', () => {
    for (const text of STAGE_HEADLINES) expect(linesAt(text, 1)).toBe(2);
  });

  it('keeps the wordmark on its one line at the cap', () => {
    const width = widthOf(
      wordmarkFace,
      STAGE_WORDMARK,
      theme.type.h1.fontSize,
      theme.type.h1.letterSpacing,
    );
    // The dot and its gap come out of the column before the word does.
    const room = COLUMN - theme.size.stage.mark - theme.space.xs;
    expect(largestStepThatFits(width, room)).toBeGreaterThanOrEqual(theme.size.stage.textMaxScale);
  });
});

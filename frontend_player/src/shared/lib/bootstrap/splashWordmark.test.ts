/**
 * **The wordmark's constants, pinned against the font file** — the numbers the splash places its
 * seven letters by, read back off `Archivo_800ExtraBold.ttf` in the bundle
 * ([#855](https://github.com/Rakieta02/Rakieta/issues/855); ADR-0209, *Consequences*).
 *
 * The splash sets *Rakieta* letter by letter from the font's own advances and kerning rather than
 * from a text layout, so its geometry is known before the first frame. That trades a measurement
 * for a copy, and this is what keeps the copy honest: **a font release that redraws a letter, or
 * kerns a pair differently, turns this red**, and `WORDMARK_FACE` is read again. The prior art is
 * `deckStampFit.test.ts`, which reads the same face the same way.
 *
 * **What makes it go red:** a new `@expo-google-fonts/archivo`, a `splashWord` pointed at another
 * face or size, or a number in `WORDMARK_FACE` typed wrong. **What it cannot see**: what a phone's
 * text engine does with a lone letter — that is the look on the A32 and an iPhone.
 */

import { theme } from '@/shared/ui/theme';
import { readFace, widthOf } from '@/test-support/fontMetrics';

import {
  LOCKUP,
  splashGeometry,
  WORDMARK,
  WORDMARK_FACE,
  type WordmarkPair,
} from './domain/splashGeometry';

const ROLE = theme.type.splashWord;
const archivo = readFace(`@expo-google-fonts/archivo/${ROLE.fontFamily}.ttf`);

const code = (letter: string) => letter.codePointAt(0)!;

const LETTERS = [...new Set(WORDMARK)];
const PAIRS = WORDMARK.slice(1).map((right, i) => `${WORDMARK[i]}${right}` as WordmarkPair);

describe('the splash’s word role', () => {
  it('is the brief’s: Archivo ExtraBold at 42 pt, tracked −4 %', () => {
    expect(ROLE).toEqual({
      fontFamily: theme.font.sans[800],
      fontSize: 42,
      letterSpacing: -1.68,
    });
    expect(ROLE.letterSpacing / ROLE.fontSize).toBeCloseTo(-0.04, 9);
  });
});

describe('the wordmark’s constants, against Archivo 800', () => {
  it('are in the face’s own em', () => {
    expect(WORDMARK_FACE.unitsPerEm).toBe(archivo.unitsPerEm);
  });

  it.each(LETTERS)('give %s the face’s own advance', (letter) => {
    expect(WORDMARK_FACE.advance[letter]).toBe(archivo.advance(code(letter)));
  });

  it.each(PAIRS)('kern %s as the face does', (pair) => {
    const [left, right] = [...pair];
    expect(WORDMARK_FACE.kerning[pair]).toBe(archivo.kerning(code(left!), code(right!)));
  });

  it('kern R·a and no other pair in the word, as the face did when they were read', () => {
    const kerned = PAIRS.filter((pair) => WORDMARK_FACE.kerning[pair] !== 0);
    expect(kerned).toEqual(['Ra']);
  });

  it('set each letter in the face’s own line box', () => {
    expect(WORDMARK_FACE.ascender).toBe(archivo.ascender);
    expect(WORDMARK_FACE.descender).toBe(archivo.descender);
  });

  /**
   * The geometry centres a letter's box of ascender over descender on the midline. iOS makes a line
   * that tall plus the face's line gap, and a platform may read the `OS/2` numbers instead of
   * `hhea`'s — so both must describe the same box, with no gap, or the baseline leaves the floor.
   */
  it('describe the one line box every platform sets: no line gap, and OS/2 saying the same', () => {
    expect(archivo.lineGap).toBe(0);
    expect(archivo.typo).toEqual({
      ascender: archivo.ascender,
      descender: archivo.descender,
      lineGap: 0,
      useTypo: true,
    });
  });
});

describe('the word the splash sets', () => {
  const setting = {
    face: WORDMARK_FACE,
    fontSize: ROLE.fontSize,
    letterSpacing: ROLE.letterSpacing,
  };
  const at = splashGeometry(
    { screen: { width: 390, height: 844 }, view: { x: 0, y: 0, width: 390, height: 844 } },
    setting,
  );

  it('is as wide as the face sets it: its advances, its kerning, and tracking between letters', () => {
    const last = at.letters[at.letters.length - 1]!;
    const kerning = PAIRS.reduce((sum, pair) => {
      const [left, right] = [...pair];
      return sum + archivo.kerning(code(left!), code(right!));
    }, 0);
    // `widthOf` tracks after every letter; the word is tracked only between them.
    const expected =
      widthOf(archivo, WORDMARK.join(''), ROLE.fontSize, ROLE.letterSpacing) -
      ROLE.letterSpacing +
      (kerning / archivo.unitsPerEm) * ROLE.fontSize;

    expect(last.x + last.width - at.letters[0]!.x).toBeCloseTo(expected, 9);
  });

  it('stands on the floor: the baseline of a line box centred on the midline is 14 pt down', () => {
    // The line box is the face's ascender over its descender; centred on the midline, the
    // baseline sits half their difference below it.
    const baseline =
      ((archivo.ascender + archivo.descender) / 2 / archivo.unitsPerEm) * ROLE.fontSize;

    expect(Math.abs(baseline - LOCKUP.floorBelowMidline)).toBeLessThan(0.05);
  });
});

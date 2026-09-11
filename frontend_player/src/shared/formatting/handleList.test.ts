/**
 * `WIDEST_HANDLE_EM`, derived rather than chosen — and the rule it feeds.
 *
 * The handle line gives way by **dropping whole names**, which needs an answer to *how many
 * characters fit* on a screen no module can measure. Pick that by eye and it is a guess that fails
 * on one handle, on one phone, as an ellipsis inside somebody's nickname that nobody who built the
 * row will ever see. So it is **measured**: this file reads the advance widths out of the Archivo
 * Bold that ships in the bundle and checks that no character a handle can be written in is wider
 * than the share the budget spends per character.
 *
 * **What makes it go red:** an Archivo release that redraws the letters, a different type role on
 * the handle line, or a repertoire that grows a wider character. Every one of those is a real
 * change to the answer, and none of them announces itself at 13pt.
 *
 * Font metrics come from `test-support/fontMetrics.ts`, which is where the tab bar's `cmap` walk
 * moved when a second surface needed the same measurement.
 */

import { theme } from '@/shared/ui';
import { readFace, widthOf } from '@/test-support/fontMetrics';

import {
  HANDLE_SEPARATOR,
  WIDEST_HANDLE_EM,
  charactersThatFit,
  handleLine,
  spokenHandles,
} from './handleList';

const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.cardTitle.fontFamily}.ttf`);

/**
 * Everything a nickname can be written in: printable ASCII, and the nine Polish letters this
 * platform's own players write their handles with.
 */
const REPERTOIRE = [
  ...Array.from({ length: 0x7f - 0x20 }, (_, at) => String.fromCodePoint(0x20 + at)),
  ...'ĄĆĘŁŃÓŚŹŻąćęłńóśźż',
];

describe('the widest character a handle may contain', () => {
  it('is drawn by the face the line is actually set in', () => {
    for (const character of REPERTOIRE) {
      expect(archivoBold.draws(character.codePointAt(0) ?? 0)).toBe(true);
    }
  });

  it('is inside the share the budget spends per character', () => {
    const size = theme.type.cardTitle.fontSize;
    const widest = Math.max(...REPERTOIRE.map((c) => widthOf(archivoBold, c, size)));

    expect(widest / size).toBeLessThanOrEqual(WIDEST_HANDLE_EM);
    // And not wildly under it, or the budget is throwing away room it could have spent.
    expect(widest / size).toBeGreaterThan(WIDEST_HANDLE_EM - 0.05);
  });

  it('never answers nought, because a row always names somebody', () => {
    expect(charactersThatFit(0)).toBe(1);
    expect(charactersThatFit(-100)).toBe(1);
  });

  /**
   * The budget is measured in the role the line is **set in**, and it defaults to the rows' —
   * the header sets its handles in `h1`, and a budget counted at `cardTitle` for a line drawn six
   * points larger is the mid-handle tail truncation §15 forbids, arriving through arithmetic
   * ([#401](https://github.com/Raketa02/Raketa/issues/401)).
   */
  it('holds fewer characters in a larger role, and counts the rows’ role by default', () => {
    expect(charactersThatFit(200, theme.type.h1)).toBeLessThan(charactersThatFit(200));
    expect(charactersThatFit(200)).toBe(charactersThatFit(200, theme.type.cardTitle));
  });

  it('spends the role’s own tracking as well as its size', () => {
    // `h1` is tracked tighter than nothing; a budget that ignored that would be pessimistic by
    // one character every thirty or so, which is a name dropped that would have fitted.
    const untracked = Math.floor(200 / (theme.type.h1.fontSize * WIDEST_HANDLE_EM));
    const tracked = Math.floor(
      200 / (theme.type.h1.fontSize * WIDEST_HANDLE_EM + theme.type.h1.letterSpacing),
    );

    expect(charactersThatFit(200, theme.type.h1)).toBe(tracked);
    expect(tracked).toBeGreaterThanOrEqual(untracked);
  });
});

describe('the line a row draws', () => {
  it('joins every name that fits', () => {
    expect(handleLine(['ewa.m', 'tomek.p', 'ola.k'], 40)).toBe('ewa.m, tomek.p, ola.k');
  });

  /** §15 is categorical: a nickname is not shortenable, so the list drops whole names. */
  it('drops a whole name rather than letting one be cut, and says how many it dropped', () => {
    expect(handleLine(['ewa.magdalena.wisniewska', 'tomek.przybylski'], 26)).toBe(
      'ewa.magdalena.wisniewska +1',
    );
  });

  it('charges for the counter that replaces what it dropped', () => {
    // Both names and the separator are exactly 24 characters — but saying `+1` costs two more,
    // so a line that just fitted stops fitting the moment it says what it left out.
    const names = ['aaaaaaaaaa', 'bbbbbbbbbbbb'];

    expect([...names.join(HANDLE_SEPARATOR)]).toHaveLength(24);
    expect(handleLine(names, 24)).toBe('aaaaaaaaaa, bbbbbbbbbbbb');
    expect(handleLine(names, 23)).toBe('aaaaaaaaaa +1');
  });

  it('keeps one name whatever the budget, because there is nothing shorter to draw', () => {
    expect(handleLine(['sixty-four-characters-of-handle'], 1)).toBe(
      'sixty-four-characters-of-handle',
    );
  });

  it('counts a handle by its characters and not by its bytes', () => {
    expect(handleLine(['żółć', 'ola.k'], 4)).toBe('żółć +1');
  });
});

describe('the handles a row speaks', () => {
  /**
   * §24.2 spells a Chats row as `Tomek W. and Ola K., padel, …`, and §22.6 gives the platform's
   * join for a list in a sentence: commas, and a final *and*.
   */
  it('joins with commas and a final and', () => {
    expect(spokenHandles(['ewa.m'])).toBe('ewa.m');
    expect(spokenHandles(['tomek.p', 'ola.k'])).toBe('tomek.p and ola.k');
    expect(spokenHandles(['tomek.p', 'ola.k', 'kuba.z'])).toBe('tomek.p, ola.k and kuba.z');
  });

  /** §20.4: the visible label truncates, the spoken one never does. */
  it('never drops a name, whatever the row drew', () => {
    const everybody = ['ewa.magdalena.wisniewska', 'tomek.przybylski', 'ola.kowalczyk'];

    expect(handleLine(everybody, 26)).toBe('ewa.magdalena.wisniewska +2');
    for (const name of everybody) expect(spokenHandles(everybody)).toContain(name);
  });
});

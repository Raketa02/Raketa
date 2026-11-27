/**
 * The shell's own sentences, held to the test a tab's line has to pass.
 *
 * Copy is not usually worth a suite. These are: some of them are **citations** of decisions
 * taken elsewhere, and one of them is a refusal.
 * A later edit that made a tab say *coming soon* or Now say *nothing is happening* would be a
 * product change wearing the clothes of a wording tweak.
 *
 * **The refusal outlived every placeholder it was written for.** Now's line left the
 * placeholder table when the rail replaced it ([#367](https://github.com/Raketa02/Raketa/issues/367)),
 * and You's, the last, went with the tab ADR-0179 built. *Never says nothing is happening* was
 * Now's refusal in the first place — it is where a game lands — so a build that deleted the row
 * along with the last placeholder would have dropped the one assertion the whole rule came from.
 * Every sentence the shell still writes is in `LINES` below, under the identical two refusals.
 */

import { TAB_BAR_TABS, type TabBarKey } from '@/shared/ui';

import {
  HOME_COPY,
  NEEDS_YOUR_ANSWER_COPY,
  PLAY_COPY,
  envelopeFigure,
  envelopeSpoken,
} from './shellCopy';
import { YOU_COPY } from './youCopy';

/** Every sentence the shell writes — Home's own lines, and You's group titles. */
const LINES = [HOME_COPY.empty.line, HOME_COPY.empty.act, ...Object.values(YOU_COPY.groups)];

describe('what the tabs are called', () => {
  const label = (key: TabBarKey) => TAB_BAR_TABS.find((tab) => tab.key === key)?.label;

  it('titles each composed tab with the name the bar gives it', () => {
    expect(HOME_COPY.title).toBe(label('home'));
    expect(YOU_COPY.title).toBe(label('you'));
  });

  /**
   * There is no placeholder table to hold equal to the bar any more: every column the bar
   * draws has a screen behind it, and the last line to leave the table is asserted **absent**
   * so it cannot come back as a gap-filler.
   */
  it('has no placeholder left, and You no longer says it is unbuilt', () => {
    for (const line of LINES) {
      expect(line).not.toMatch(/not built/i);
    }
  });
});

describe("what You's groups say", () => {
  /**
   * `the-words.md` §27: three groups, for the three questions the rows answer — and a fourth, the
   * account, since money arrived (ADR-0189 amending ADR-0179 §9; the screens A7, #552).
   */
  it('names the four questions the rows answer, in the order they are asked', () => {
    expect(Object.values(YOU_COPY.groups)).toEqual([
      'Playing',
      'Your games',
      'On your card',
      'Account',
    ]);
  });
});

describe('what Home says when it is holding nothing', () => {
  /**
   * The rail replaced a placeholder, and an empty Home would otherwise be a blank screen — worse
   * than the citation it replaced. So there are two sentences and each has a job: the first says
   * what the tab **is**, in the present tense, and the second names the act that fills it.
   */
  it('says what the tab is, and points at the act', () => {
    expect(HOME_COPY.empty.line).toMatch(/every game you arrange/i);
    expect(HOME_COPY.empty.act).toMatch(/play/i);
  });

  /**
   * 10.2: *the ⚡ is `zap` and never the character*. `U+26A1` is emoji-presentation by default, so
   * a bare one renders as a colour glyph this app's `color` cannot touch — the same deletion
   * `FILL_THE_SEATS` already made. The tab's drawn name is the word this sentence points at.
   */
  it('names Play without drawing the bolt', () => {
    expect(HOME_COPY.empty.act).not.toContain('⚡');
  });
});

describe("what Play's segment says", () => {
  it('names its two pages, Groups first', () => {
    expect(Object.values(PLAY_COPY.segment)).toEqual(['Groups', 'Explore']);
  });

  // #826: with `explore` off Play is the groups list under a title, and the title is the page's
  // own name — the word the segment gives it, and the Administrator's Groups tab's.
  it('titles Play, while Explore is off, with the name of the page it shows', () => {
    expect(PLAY_COPY.title).toBe('Groups');
    expect(PLAY_COPY.title).toBe(PLAY_COPY.segment.groups);
  });
});

describe('what they refuse to say', () => {
  it('never says nothing is happening', () => {
    // Home is where a game lands. Asserting emptiness would be a lie one tap after one was
    // booked — and the same sentence is wrong elsewhere for the simpler reason that a player
    // cannot tell it from a broken screen. **This is the row the rail had to keep**: it was
    // Now's refusal first, and Home's own line is in `LINES` above.
    for (const line of LINES) {
      expect(line).not.toMatch(/nothing/i);
      expect(line).not.toMatch(/empty/i);
    }
  });

  it('never promises a date, and never apologises', () => {
    for (const line of LINES) {
      expect(line).not.toMatch(/coming soon|soon|sorry|under construction/i);
    }
  });
});

/**
 * **The envelope's count** (#819, ADR-0205 §2) — the bell's count mark, so the bell's rule: the
 * served figure up to 99 and *99+* above it, nothing at nought, and spoken exactly on the
 * envelope's own name, since a listener is not short of room.
 */
describe("what the envelope's count says", () => {
  it('draws the served figure, 99+ above 99, and nothing at nought', () => {
    expect(envelopeFigure(0)).toBeUndefined();
    expect(envelopeFigure(2)).toBe('2');
    expect(envelopeFigure(99)).toBe('99');
    expect(envelopeFigure(100)).toBe('99+');
  });

  it('is spoken on the envelope’s name — Needs your answer, 2 new — and alone at nought', () => {
    expect(envelopeSpoken(0)).toBe(NEEDS_YOUR_ANSWER_COPY.title);
    expect(envelopeSpoken(2)).toBe('Needs your answer, 2 new');
    expect(envelopeSpoken(140)).toBe('Needs your answer, 140 new');
  });
});

/**
 * The shell's own sentences, held to the test a tab's line has to pass.
 *
 * Copy is not usually worth a suite. These are, for the same reason `optInPresentation.ts`
 * is: some of them are **citations** of decisions taken elsewhere, and one of them is a refusal.
 * A later edit that made a tab say *coming soon* or Now say *nothing is happening* would be a
 * product change wearing the clothes of a wording tweak.
 *
 * **The refusal outlived every placeholder it was written for.** Chats' line left the
 * placeholder table when the tab was built ([#360](https://github.com/Raketa02/Raketa/issues/360))
 * and `CONVERSATIONS`' own line joined it with the section that draws it
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)); **Now's went the same way when the rail
 * replaced it** ([#367](https://github.com/Raketa02/Raketa/issues/367)); and You's, the last,
 * went with the tab ADR-0179 built. *Never says nothing is happening* was Now's refusal in the
 * first place — it is where a send lands — so a build that deleted the row along with the last
 * placeholder would have dropped the one assertion the whole rule came from. Every sentence the
 * shell still writes is in `LINES` below, under the identical two refusals.
 */

import { TAB_BAR_TABS, type TabBarKey } from '@/shared/ui';

import { CHATS_COPY, NOW_COPY } from './shellCopy';
import { YOU_COPY } from './youCopy';

/** Every sentence the shell writes — the two built tabs' own lines, and You's three group titles. */
const LINES = [
  CHATS_COPY.panel.title,
  CHATS_COPY.panel.body,
  CHATS_COPY.emptyChallenges,
  CHATS_COPY.emptyConversations,
  NOW_COPY.empty.line,
  NOW_COPY.empty.act,
  ...Object.values(YOU_COPY.groups),
];

describe('what the tabs are called', () => {
  const label = (key: TabBarKey) => TAB_BAR_TABS.find((tab) => tab.key === key)?.label;

  it('titles each composed tab with the name the bar gives it', () => {
    expect(CHATS_COPY.title).toBe(label('chats'));
    expect(NOW_COPY.title).toBe(label('now'));
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
  /** `the-words.md` §27: three groups, for the three questions the rows answer. */
  it('names the three questions the rows answer, in the order they are asked', () => {
    expect(Object.values(YOU_COPY.groups)).toEqual(['Playing', 'Finding players', 'On your card']);
  });
});

describe('what Now says when it is holding nothing', () => {
  /**
   * The rail replaced a placeholder, and an empty Now would otherwise be a blank screen — worse
   * than the citation it replaced. So there are two sentences and each has a job: the first says
   * what the tab **is**, in the present tense, and the second names the act that fills it.
   */
  it('says what the tab is, and points at the act', () => {
    expect(NOW_COPY.empty.line).toMatch(/every game you arrange/i);
    expect(NOW_COPY.empty.act).toMatch(/play/i);
  });

  /**
   * 10.2: *the ⚡ is `zap` and never the character*. `U+26A1` is emoji-presentation by default, so
   * a bare one renders as a colour glyph this app's `color` cannot touch — the same deletion
   * `FILL_THE_SEATS` already made. The tab's drawn name is the word this sentence points at.
   */
  it('names Play without drawing the bolt', () => {
    expect(NOW_COPY.empty.act).not.toContain('⚡');
  });
});

describe("what each of the Chats tab's two empty lines points at", () => {
  /**
   * They are one screen apart and are filled by two different acts, so neither may be the other's
   * sentence: a challenge lands in the first when it is sent or received, and a room opens in the
   * second only when somebody **accepts**.
   */
  it('names the act that fills its own section, in the present tense', () => {
    expect(CHATS_COPY.emptyChallenges).toMatch(/challenges/i);
    expect(CHATS_COPY.emptyConversations).toMatch(/accepts/i);
    expect(CHATS_COPY.emptyConversations).not.toBe(CHATS_COPY.emptyChallenges);
  });
});

describe('what they refuse to say', () => {
  it('never says nothing is happening', () => {
    // Now is where a send lands, and so is Chats. Asserting emptiness would be a lie one tap
    // after a challenge went out — and the same sentence is wrong on the others for the
    // simpler reason that a player cannot tell it from a broken screen. **This is the row the
    // rail had to keep**: it was Now's refusal first, and Now's own line is in `LINES` above.
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

/**
 * The shell's own sentences, held to the test a placeholder has to pass.
 *
 * Copy is not usually worth a suite. These are, for the same reason `optInPresentation.ts`
 * is: some of them are **citations** of decisions taken elsewhere, and one of them is a refusal.
 * A later edit that made a tab say *coming soon* or Now say *nothing is happening* would be a
 * product change wearing the clothes of a wording tweak.
 *
 * **The refusal moved with the copy rather than being deleted, twice.** Chats' placeholder line
 * left this table when the tab was built ([#360](https://github.com/Raketa02/Raketa/issues/360))
 * and `CONVERSATIONS`' own line joined it with the section that draws it
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)); **Now's went the same way when the rail
 * replaced it** ([#367](https://github.com/Raketa02/Raketa/issues/367)). *Never says nothing is
 * happening* was Now's refusal in the first place — it is where a send lands — so a build that
 * deleted the row along with the placeholder would have dropped the one assertion the whole rule
 * came from. `NOW_COPY`'s two sentences are in `LINES` below, under the identical two refusals.
 */

import { TAB_BAR_TABS, type TabBarKey } from '@/shared/ui';

import { CHATS_COPY, NOW_COPY, PLACEHOLDER_COPY, type PlaceholderTab } from './shellCopy';

/** Every sentence this file owns — the placeholders, and the two built tabs' own lines. */
const LINES = [
  ...Object.values(PLACEHOLDER_COPY).map((copy) => copy.line),
  CHATS_COPY.panel.title,
  CHATS_COPY.panel.body,
  CHATS_COPY.emptyChallenges,
  CHATS_COPY.emptyConversations,
  NOW_COPY.empty.line,
  NOW_COPY.empty.act,
];

describe('what the placeholders say', () => {
  /** The three tabs with a screen behind them. None of them is a placeholder any more. */
  const BUILT: readonly TabBarKey[] = ['now', 'play', 'chats'];

  /** The narrowing the loop below needs, and the one place the two lists are held equal. */
  const stillAPlaceholder = (key: TabBarKey): key is PlaceholderTab => !BUILT.includes(key);

  it('covers every tab the bar draws except the three that are built', () => {
    const drawn = TAB_BAR_TABS.map((tab) => tab.key).filter(stillAPlaceholder);

    expect(Object.keys(PLACEHOLDER_COPY).sort()).toEqual([...drawn].sort());
  });

  it('titles each tab with the name the bar gives it', () => {
    for (const tab of TAB_BAR_TABS) {
      if (!stillAPlaceholder(tab.key)) continue;
      expect(PLACEHOLDER_COPY[tab.key].title).toBe(tab.label);
    }
  });

  it('titles the two built tabs with the names the bar gives them too', () => {
    const label = (key: TabBarKey) => TAB_BAR_TABS.find((tab) => tab.key === key)?.label;

    expect(CHATS_COPY.title).toBe(label('chats'));
    expect(NOW_COPY.title).toBe(label('now'));
  });

  it('quotes the two lines the map fixed, word for word', () => {
    // Pinned because they are **citations**: one of the two quotes a decision taken on another
    // ticket, so a reworded line is that decision being restated by somebody who was not in the
    // argument. Three stubs were never pinned and are gone entirely — #268 replaced Play's with
    // the screen, which is what a placeholder is for, and #360 and #367 did the same for Chats
    // and Now.
    expect(PLACEHOLDER_COPY.around.line).toBe('Players and courts near you — not built yet');
    expect(PLACEHOLDER_COPY.you.line).toBe('Your profile, your radius, your week — not built yet');
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

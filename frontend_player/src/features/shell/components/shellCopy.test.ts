/**
 * The shell's own sentences, held to the test a placeholder has to pass.
 *
 * Copy is not usually worth a suite. These are, for the same reason `optInPresentation.ts`
 * is: some of them are **citations** of decisions taken elsewhere, and one of them is a refusal.
 * A later edit that made a tab say *coming soon* or Now say *nothing is happening* would be a
 * product change wearing the clothes of a wording tweak.
 *
 * **The refusal moved with the copy rather than being deleted.** Chats' placeholder line left
 * this table when the tab was built ([#360](https://github.com/Raketa02/Raketa/issues/360)), and
 * the tab's real sentences took its place here: an empty state that may not assert nothing is
 * happening is the same rule the placeholder was held to, on a screen where a send genuinely
 * lands one tap later.
 */

import { TAB_BAR_TABS, type TabBarKey } from '@/shared/ui';

import { CHATS_COPY, PLACEHOLDER_COPY } from './shellCopy';

/** Every sentence this file owns — the placeholders, and the built tab's own lines. */
const LINES = [
  ...Object.values(PLACEHOLDER_COPY).map((copy) => copy.line),
  CHATS_COPY.panel.title,
  CHATS_COPY.panel.body,
  CHATS_COPY.emptyChallenges,
];

describe('what the placeholders say', () => {
  /** The two tabs with a screen behind them. Neither is a placeholder any more. */
  const BUILT: readonly TabBarKey[] = ['play', 'chats'];

  it('covers every tab the bar draws except the two that are built', () => {
    const drawn = TAB_BAR_TABS.map((tab) => tab.key).filter((key) => !BUILT.includes(key));

    expect(Object.keys(PLACEHOLDER_COPY).sort()).toEqual([...drawn].sort());
  });

  it('titles each tab with the name the bar gives it', () => {
    for (const tab of TAB_BAR_TABS) {
      if (tab.key === 'play' || tab.key === 'chats') continue;
      expect(PLACEHOLDER_COPY[tab.key].title).toBe(tab.label);
    }
  });

  it('titles the built tab with the name the bar gives it too', () => {
    expect(CHATS_COPY.title).toBe(TAB_BAR_TABS.find((tab) => tab.key === 'chats')?.label);
  });

  it('quotes the three lines the map fixed, word for word', () => {
    // Pinned because they are **citations**: two of the three quote a decision taken on
    // another ticket, so a reworded line is that decision being restated by somebody who
    // was not in the argument. Play's stub was never pinned and is gone entirely — #268
    // replaced it with the screen, which is what a placeholder is for, and #360 did the same
    // for Chats.
    expect(PLACEHOLDER_COPY.now.line).toBe('What is happening today and next — not built yet');
    expect(PLACEHOLDER_COPY.around.line).toBe('Players and courts near you — not built yet');
    expect(PLACEHOLDER_COPY.you.line).toBe('Your profile, your radius, your week — not built yet');
  });
});

describe('what they refuse to say', () => {
  it('never says nothing is happening', () => {
    // Now is where a send lands, and so is Chats. Asserting emptiness would be a lie one tap
    // after a challenge went out — and the same sentence is wrong on the others for the
    // simpler reason that a player cannot tell it from a broken screen.
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

/**
 * The four lines, held to the test a placeholder has to pass.
 *
 * Copy is not usually worth a suite. These are, for the same reason `optInPresentation.ts`
 * is: two of them are **citations** of decisions taken elsewhere, and the third is a refusal.
 * A later edit that made Chats say *coming soon* or Now say *nothing is happening* would be a
 * product change wearing the clothes of a wording tweak.
 */

import { TAB_BAR_TABS } from '@/shared/ui';

import { PLACEHOLDER_COPY } from './shellCopy';

const LINES = Object.values(PLACEHOLDER_COPY).map((copy) => copy.line);

describe('what the placeholders say', () => {
  it('covers every tab the bar draws except the one that is built', () => {
    const drawn = TAB_BAR_TABS.map((tab) => tab.key).filter((key) => key !== 'play');

    expect(Object.keys(PLACEHOLDER_COPY).sort()).toEqual([...drawn].sort());
  });

  it('titles each tab with the name the bar gives it', () => {
    for (const tab of TAB_BAR_TABS) {
      if (tab.key === 'play') continue;
      expect(PLACEHOLDER_COPY[tab.key].title).toBe(tab.label);
    }
  });

  it('quotes the four lines the map fixed, word for word', () => {
    // Pinned because they are **citations**: three of the four quote a decision taken on
    // another ticket, so a reworded line is that decision being restated by somebody who
    // was not in the argument. Play's stub was never pinned and is now gone entirely — #268
    // replaced it with the screen, which is what a placeholder is for.
    expect(PLACEHOLDER_COPY.now.line).toBe('What is happening today and next — not built yet');
    expect(PLACEHOLDER_COPY.around.line).toBe('Players and courts near you — not built yet');
    expect(PLACEHOLDER_COPY.chats.line).toBe('A chat opens when somebody accepts — not built yet');
    expect(PLACEHOLDER_COPY.you.line).toBe('Your profile, your radius, your week — not built yet');
  });
});

describe('what they refuse to say', () => {
  it('never says nothing is happening', () => {
    // Now is where a send lands. Asserting emptiness would be a lie one tap after a
    // challenge went out — and the same sentence is wrong on the other three for the
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

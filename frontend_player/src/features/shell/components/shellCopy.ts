/**
 * What the one unbuilt tab says, and what the two built ones the shell writes for say.
 *
 * **These are citations, not filler.** A placeholder line is one sentence naming what its tab
 * will be, plus that it is not built — decided elsewhere, so the sentence is quoting a rule
 * rather than making a promise ([#227](https://github.com/Raketa02/Raketa/issues/227)):
 *
 * | Tab | Where the line comes from |
 * | --- | --- |
 * | You | [#226](https://github.com/Raketa02/Raketa/issues/226) — the grid, the radius and the declaration are exactly the three facts on the wire |
 *
 * **Four tabs have left this table and none of them was deleted.** Play's stub was replaced by
 * the screen itself ([#268](https://github.com/Raketa02/Raketa/issues/268)); Chats' line — *"a
 * chat opens when somebody accepts"* — was a citation of
 * [#221](https://github.com/Raketa02/Raketa/issues/221), and `CHATS_COPY` below is that same
 * citation said properly on a tab that is built
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)); **Now's died with the rail**
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)), replaced by `NOW_COPY` below; and
 * **Around's retired with the tab** — its line promised *players and courts near you*, nothing
 * had been decided about either, and the deck moved in as **Players**
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1). Courts get their own home when they arrive. One tab remains unbuilt, and `PlaceholderTab`
 * excludes the four that are not.
 *
 * **No sentence here may say "nothing is happening."** It began as Now's refusal — Now is where a
 * send lands, so a placeholder asserting emptiness would be lying one tap after a challenge went
 * out — and it now governs every empty state the shell writes, on both of the built tabs. Naming
 * what a tab **is** is true in both states, which is the test each line has to pass and the test
 * `shellCopy.test.ts` holds them to.
 *
 * The em dash is a dash and not a colon on purpose: *not built yet* is an aside about the
 * app, not a second clause of the sentence about the tab.
 */

import type { TabBarKey } from '@/shared/ui';

/** A tab with no screen behind it yet: what it is called, and the one line it shows. */
export interface PlaceholderCopy {
  readonly title: string;
  readonly line: string;
}

/** The one tab that ships unbuilt. Now, Players, Play and Chats are built and are not it. */
export type PlaceholderTab = Exclude<TabBarKey, 'now' | 'players' | 'play' | 'chats'>;

export const PLACEHOLDER_COPY = {
  you: {
    title: 'You',
    line: 'Your profile, your radius, your week — not built yet',
  },
} as const satisfies Record<PlaceholderTab, PlaceholderCopy>;

/**
 * **The Chats tab's own sentences** — the panel, and each section's empty state.
 *
 * They sit with the shell rather than with `challenges` or `conversations` because §1's rule is
 * the **vocabulary owner**, not the feature
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22): these are about
 * the *tab* — what a chat is on this platform, and what lands on this screen — where the
 * sections under them own the words for a challenge and a conversation. Each section is handed
 * its own empty line and owns its own heading.
 *
 * **The panel states the limit that makes this a sports app, and both of the design's promises
 * are dropped** (§22.1). *"When you count yourself into something tonight"* was Around's, and
 * Around **has no tab now** — the deck took the column as Players (ADR-0169 §1) and nothing on
 * it is a thing to count yourself into; *"inside a game or a plan"* is wrong in the other
 * direction, because a conversation opens on the **first acceptance**, before there is a game at
 * all. What is kept is the sentence that does the work: there is no way to message a stranger.
 *
 * **No empty state here may assert that nothing is happening.** Now's standing refusal,
 * inherited for the same reason — a send lands here now, so *nothing here yet* can be false one
 * tap after it is drawn. It is one present-tense line naming the act, which is 10.1's
 * empty-state rule, and `shellCopy.test.ts` holds it to that exactly as it holds the three
 * placeholders. **Both sections have their line now**
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)), and each points at the act that fills
 * its own list: one at sending or being sent a challenge, the other at the acceptance that opens
 * a room.
 */
export const CHATS_COPY = {
  title: 'Chats',
  panel: {
    title: 'Chat exists only where you have agreed to play',
    body:
      'A conversation opens the moment somebody accepts — theirs or yours. There is no way to ' +
      'message a stranger, and that line is what keeps this a sports app.',
  },
  /** `CHALLENGES` holds nothing. The line names the act, in the present tense, on both sides. */
  emptyChallenges: 'Challenges you send and challenges sent to you land here.',
  /**
   * `CONVERSATIONS` holds nothing — and the act it names is somebody **accepting**, which is the
   * one thing that opens a room. Not *no chats yet*: a player with an outstanding challenge is one
   * answer away from a room, and the sentence has to be true of them too.
   */
  emptyConversations: 'The moment somebody accepts, the two of you can talk here.',
} as const;

/**
 * **The Now tab's own sentences** — its title, and what it says when it holds no games
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7).
 *
 * `PLACEHOLDER_COPY.now` **died with the rail** ([#367](https://github.com/Raketa02/Raketa/issues/367)),
 * and an empty Now would then have been a blank screen, which is worse than the citation it
 * replaced. So there are two lines and they are here rather than in `features/plans` for §1's
 * reason: the heading over the rail is that feature's because it names its own content, and these
 * are about the **tab**.
 *
 * **The first says what Now is**, in the present tense and true whether or not anything is on it;
 * **the second names the act**, which is 10.1's empty-state rule. Neither may assert that nothing
 * is happening — Now's oldest refusal, and the one `shellCopy.test.ts` still holds every line in
 * this file to.
 *
 * **The bolt is not drawn.** §22.7 writes the second line as `⚡ Play finds you one.`, and 10.2 is
 * explicit that *"the ⚡ is `zap` and never the character"*: `U+26A1` carries
 * `Emoji_Presentation=Yes`, so a bare one in a muted sentence renders as a colour emoji that this
 * app's `color` has nothing to apply to. The tab's own drawn name is `Play`, and that is the word
 * this sentence points at — the same deletion `FILL_THE_SEATS` already made one screen over.
 */
export const NOW_COPY = {
  title: 'Now',
  empty: {
    line:
      'Every game you arrange shows up here — what is agreed, what is today, and what still ' +
      'needs a score.',
    act: 'Play finds you one.',
  },
} as const;

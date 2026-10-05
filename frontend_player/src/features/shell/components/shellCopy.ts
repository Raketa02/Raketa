/**
 * The sentences the shell writes for the tabs it composes — Chats and Home.
 *
 * **These are citations, not filler**, and there is no placeholder among them any more. For
 * as long as a tab was unbuilt its line was one sentence naming what the tab would be plus
 * that it was not built — decided elsewhere, so the sentence was quoting a rule rather than
 * making a promise ([#227](https://github.com/Raketa02/Raketa/issues/227)). **Every tab has
 * left that table and none of them was deleted.** Play's stub was replaced by the screen
 * itself ([#268](https://github.com/Raketa02/Raketa/issues/268)); Chats' line — *"a chat
 * opens when somebody accepts"* — was a citation of
 * [#221](https://github.com/Raketa02/Raketa/issues/221), and `CHATS_COPY` below is that same
 * citation said properly on a tab that is built
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)); **Now's died with the rail**
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)), replaced by `HOME_COPY` below;
 * **Around's retired with the tab** — its line promised *players and courts near you*, nothing
 * had been decided about either, and the deck moved in as **Players**
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1); and **You's went last, with the tab it cited** — *your profile, your radius, your week —
 * not built yet* was [#226](https://github.com/Raketa02/Raketa/issues/226)'s three facts on the
 * wire, and the tab draws all three now and a good deal more
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)),
 * with its own words in `youCopy`. `PlaceholderCopy`, `PlaceholderTab` and `PLACEHOLDER_COPY`
 * went with it: an empty union and an empty table would have been a shape kept for a case that
 * cannot recur, since every column the bar draws has a screen behind it.
 *
 * **No sentence here may say "nothing is happening."** It began as Now's refusal — Now is where a
 * send lands, so a placeholder asserting emptiness would be lying one tap after a challenge went
 * out — and it now governs every empty state the shell writes, on both of the built tabs. Naming
 * what a tab **is** is true in both states, which is the test each line has to pass and the test
 * `shellCopy.test.ts` holds them to.
 */

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
 * **The Home tab's own sentences** — its title, and what it says when it holds no games
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7).
 *
 * **Home is today's Now, renamed** ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)):
 * the title is the bar's new word and nothing else moved. The two lines below are still true of
 * the tab — every game you are in shows up here — and the booked game's statuses are
 * [#556](https://github.com/Raketa02/Raketa/issues/556)'s to write.
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
export const HOME_COPY = {
  title: 'Home',
  empty: {
    line:
      'Every game you arrange shows up here — what is agreed, what is today, and what still ' +
      'needs a score.',
    act: 'Play finds you one.',
  },
} as const;

/**
 * **The Play tab's own words** — the two segments it opens on
 * ([#512](https://github.com/Raketa02/Raketa/issues/512), play mocks 1 and 3).
 *
 * The shell's rather than `groups`' because the segment is the *tab*: it names the two ways the
 * tab finds a player games, and each segment's page owns its own sentences under it. Explore draws
 * nothing yet, so it has nothing here but its name.
 */
export const PLAY_COPY = {
  segment: {
    groups: 'Groups',
    explore: 'Explore',
  },
} as const;

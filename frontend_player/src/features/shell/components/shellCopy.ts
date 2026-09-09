/**
 * What the three unbuilt tabs say, and what the Chats tab says.
 *
 * **These are citations, not filler.** Each placeholder line is one sentence naming what its
 * tab will be, plus that it is not built — and two of the three are decided elsewhere, so the
 * sentence is quoting a rule rather than making a promise
 * ([#227](https://github.com/Raketa02/Raketa/issues/227)):
 *
 * | Tab | Where the line comes from |
 * | --- | --- |
 * | Now | The landing after onboarding, and the landing after a send |
 * | Around | Nothing decided: it states the tab's job and stops |
 * | You | [#226](https://github.com/Raketa02/Raketa/issues/226) — the grid, the radius and the declaration are exactly the three facts on the wire |
 *
 * **Play is not among them, and Chats has now left too.** Play's stub was replaced by the
 * screen itself ([#268](https://github.com/Raketa02/Raketa/issues/268)); Chats' line — *"a chat
 * opens when somebody accepts"* — was a citation of
 * [#221](https://github.com/Raketa02/Raketa/issues/221), and `CHATS_COPY` below is that same
 * citation said properly on a tab that is built
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)). Three tabs remain unbuilt, and
 * `PlaceholderTab` excludes the two that are not.
 *
 * **Now deliberately never says "nothing is happening."** It is where a send lands, so a
 * placeholder asserting emptiness would be lying one tap after a challenge went out. Naming
 * the tab's job is true in both states, which is the test the line has to pass and the test
 * `shellCopy.test.ts` holds it to.
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

/** The three tabs that ship unbuilt. Play and Chats are built and are not among them. */
export type PlaceholderTab = Exclude<TabBarKey, 'play' | 'chats'>;

export const PLACEHOLDER_COPY = {
  now: {
    title: 'Now',
    line: 'What is happening today and next — not built yet',
  },
  around: {
    title: 'Around',
    line: 'Players and courts near you — not built yet',
  },
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
 * are dropped** (§22.1). *"When you count yourself into something tonight"* is Around, which
 * this build does not have; *"inside a game or a plan"* is wrong in the other direction, because
 * a conversation opens on the **first acceptance**, before there is a game at all. What is kept
 * is the sentence that does the work: there is no way to message a stranger.
 *
 * **No empty state here may assert that nothing is happening.** Now's standing refusal,
 * inherited for the same reason — a send lands here now, so *nothing here yet* can be false one
 * tap after it is drawn. It is one present-tense line naming the act, which is 10.1's
 * empty-state rule, and `shellCopy.test.ts` holds it to that exactly as it holds the three
 * placeholders. `CONVERSATIONS` gains its own line beside this one with the section that draws
 * it ([#363](https://github.com/Raketa02/Raketa/issues/363)).
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
} as const;

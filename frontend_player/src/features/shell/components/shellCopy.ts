/**
 * What the four unbuilt tabs say, and what the Play stub says.
 *
 * **These are citations, not filler.** Each line is one sentence naming what its tab will
 * be, plus that it is not built — and three of the four are decided elsewhere, so the
 * sentence is quoting a rule rather than making a promise
 * ([#227](https://github.com/Raketa02/Raketa/issues/227)):
 *
 * | Tab | Where the line comes from |
 * | --- | --- |
 * | Now | The landing after onboarding, and the landing after a send |
 * | Around | Nothing decided: it states the tab's job and stops |
 * | Chats | [#221](https://github.com/Raketa02/Raketa/issues/221) — a chat opens on the **first** acceptance and grows with each one |
 * | You | [#226](https://github.com/Raketa02/Raketa/issues/226) — the grid, the radius and the declaration are exactly the three facts on the wire |
 *
 * **Play is not among them any more.** Its stub said *"the search, the deck and the court —
 * not built yet"* and was replaced by the screen itself
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)); the title it held is the screen's
 * own and moved there with it. Four tabs remain unbuilt, and `PlaceholderTab` already
 * excluded Play.
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

/** The four tabs that ship unbuilt. Play is the fifth and is not one of them. */
export type PlaceholderTab = Exclude<TabBarKey, 'play'>;

export const PLACEHOLDER_COPY = {
  now: {
    title: 'Now',
    line: 'What is happening today and next — not built yet',
  },
  around: {
    title: 'Around',
    line: 'Players and courts near you — not built yet',
  },
  chats: {
    title: 'Chats',
    line: 'A chat opens when somebody accepts — not built yet',
  },
  you: {
    title: 'You',
    line: 'Your profile, your radius, your week — not built yet',
  },
} as const satisfies Record<PlaceholderTab, PlaceholderCopy>;

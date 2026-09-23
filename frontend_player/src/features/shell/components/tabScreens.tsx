/**
 * The screens the shell composes under a tab's own words — **one of them here now**, and none
 * of them a placeholder.
 *
 * Named components rather than one taking a `tab` prop: a route file's whole job is to say
 * which screen a path is, and `<NowScreen />` says it where `<TabScreen tab="now" />` makes
 * the route file hold the answer as data.
 *
 * **Every tab has left the placeholder table.** Play's stub was an entry until
 * [#268](https://github.com/Raketa02/Raketa/issues/268) built the screen, Chats' until
 * [#360](https://github.com/Raketa02/Raketa/issues/360) built the inbox, Now's until
 * [#367](https://github.com/Raketa02/Raketa/issues/367) built the rail, and You's until
 * [ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * built the tab — the last of them, and the table went with it. Three are still the shell's,
 * because each is a composition of other features' surfaces under the tab's own words: Now
 * below, and Chats and You in files of their own because neither is thin. **Around's entry
 * retired with the tab**: the deck moved in as Players
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1), and that screen is `features/play`'s own, named by its route file exactly as Find a game
 * is — the tab has no words of its own for the shell to compose anything under.
 */

import { GamesRail } from '@/features/plans/types';

import { ShellScreen } from './ShellScreen';
import { NOW_COPY } from './shellCopy';

/**
 * **The landing, after onboarding and after a send — and it stopped being a placeholder here**
 * ([#367](https://github.com/Raketa02/Raketa/issues/367)).
 *
 * The games list arrived under a citation first ([#314](https://github.com/Raketa02/Raketa/issues/314));
 * what replaces both is `GamesRail`, which is *what is happening today and next* drawn rather than
 * described. The tab keeps the shape it has always had — it owns its own words and nothing that is
 * drawn under them — so the empty sentences are handed down and the heading over the rail is the
 * rail's.
 *
 * **It still never says nothing is happening.** The line says what the tab **is** and the one under
 * it names the act, which is true whether or not a game is on screen.
 */
export function NowScreen() {
  return (
    <ShellScreen title={NOW_COPY.title}>
      <GamesRail empty={NOW_COPY.empty} />
    </ShellScreen>
  );
}
